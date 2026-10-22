"""RAG engine for Indian traffic law Q&A.

Pipeline: ingest (markdown -> section chunks) -> retrieve (BM25) ->
generate (Claude, context-only) -> cite (numbered passages).
Pure standard library except the optional `anthropic` package.
"""

from __future__ import annotations

import json
import math
import os
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

DATA_DIR = Path(__file__).parent / "data"
MODEL = "claude-opus-5-5"
IDK = "I don't know. My documents don't cover this question."

# A query whose best BM25 score is below this is treated as out of scope
# and answered with IDK without calling the LLM. Tuned with eval.py.
MIN_SCORE = 4.0
# ...or when too little of its (IDF-weighted) vocabulary appears in the
# retrieved passages. In-scope questions score 1.0; "road tax for an electric
# car" scores 0.67, "speed limit on expressways" 0.51.
MIN_COVERAGE = 0.75

# ---------------------------------------------------------------- ingest


@dataclass
class Chunk:
    id: int
    doc_title: str
    source_file: str
    source_ref: str
    section: str
    text: str
    kind: str = "guide"   # "official" = statute text, "guide" = summary, "state" = State notification
    url: str = ""
    state: str = ""       # set only for kind == "state"

    @property
    def label(self) -> str:
        return f"{self.doc_title} > {self.section}"


def _clean(text: str) -> str:
    text = text.replace("₹", "Rs ")
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def load_chunks(data_dir: Path = DATA_DIR) -> list[Chunk]:
    """Official statute chunks (data/official/*.jsonl, built by ingest.py),
    plain-language guides (data/*.md) and State notifications (data/states/*.md,
    with a 'State: <name>' line); markdown is chunked one per '## ' section."""
    chunks: list[Chunk] = []
    for path in sorted((data_dir / "official").glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            chunks.append(Chunk(len(chunks), r["doc_title"], f"official/{path.name}",
                                r["source_ref"], r["section"], r["text"],
                                "official", r.get("url", "")))
    for path in sorted(data_dir.glob("*.md")) + sorted(data_dir.glob("states/*.md")):
        raw = _clean(path.read_text(encoding="utf-8"))
        title_match = re.search(r"^# (.+)$", raw, re.M)
        doc_title = title_match.group(1).strip() if title_match else path.stem
        source_match = re.search(r"^Source: (.+)$", raw, re.M)
        source_ref = source_match.group(1).strip() if source_match else ""
        state_match = re.search(r"^State: (.+)$", raw, re.M)
        state = state_match.group(1).strip() if state_match else ""

        for part in re.split(r"^## ", raw, flags=re.M)[1:]:
            heading, _, body = part.partition("\n")
            body = body.strip()
            if body:
                chunks.append(Chunk(len(chunks), doc_title,
                                    path.relative_to(data_dir).as_posix(), source_ref,
                                    heading.strip(), body,
                                    "state" if state else "guide", state=state))
    return chunks


# All 28 States and 8 Union Territories (2019 onward). Only some have a
# compounding notification in data/states/; see BM25Index.states.
ALL_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa",
    "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala",
    "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland",
    "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
    "Uttar Pradesh", "Uttarakhand", "West Bengal",
]
ALL_UNION_TERRITORIES = [
    "Andaman and Nicobar Islands", "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu", "Delhi", "Jammu and Kashmir", "Ladakh",
    "Lakshadweep", "Puducherry",
]

# City / alternate names that identify a State in a question.
STATE_ALIASES = {
    "karnataka": "Karnataka", "bengaluru": "Karnataka", "bangalore": "Karnataka",
    "mysuru": "Karnataka", "mysore": "Karnataka", "mangaluru": "Karnataka",
    "mangalore": "Karnataka", "hubli": "Karnataka", "hubballi": "Karnataka",
    "tamilnadu": "Tamil Nadu", "chennai": "Tamil Nadu", "madras": "Tamil Nadu",
    "coimbatore": "Tamil Nadu", "madurai": "Tamil Nadu", "trichy": "Tamil Nadu",
    "tiruchirappalli": "Tamil Nadu", "salem": "Tamil Nadu", "tirunelveli": "Tamil Nadu",
}


def detect_state(query: str, states: list[str]) -> str | None:
    q = query.lower()
    for s in states:
        if re.search(rf"\b{re.escape(s.lower())}\b", q):
            return s
    for alias, s in STATE_ALIASES.items():
        if s in states and re.search(rf"\b{alias}\b", q):
            return s
    return None


# ---------------------------------------------------------------- retrieve

STOPWORDS = set("""
a an the and or of to in on for with by at from is are was were be been am do does
did i me my we our you your he she it its they them this that these those what which
who whom how when where why can could should would will shall may might must if
than then so as not no yes there here about into up out over under again any all
some such only own same too very just also get got have has had having
many much need needed want please tell know time times given long happen happens
""".split())

# Map everyday words to the vocabulary used in the documents.
SYNONYMS = {
    "license": "licence", "licenses": "licence", "dl": "licence driving",
    "ll": "learner", "renew": "renewal", "renewing": "renewal",
    "expired": "expiry valid validity", "expire": "expiry valid validity",
    "expires": "expiry valid validity", "fine": "penalty fine", "fines": "penalty fine",
    "challan": "challan fine", "challans": "challan fine", "ticket": "challan",
    "drunk": "alcohol drunken", "drink": "alcohol", "drinking": "alcohol",
    "phone": "mobile phone handheld communications", "mobile": "mobile handheld",
    "speeding": "overspeeding speed", "overspeed": "overspeeding",
    "helmet": "helmet headgear", "helmets": "helmet headgear",
    "seatbelt": "seat belt safety", "belt": "belt safety",
    "bike": "two-wheeler motorcycle", "scooter": "two-wheeler motorcycle",
    "triple": "pillion triple",
    "spot": "spot compounding", "compound": "compounding", "compoundable": "compounding",
    "settle": "compounding",
    "crash": "accident", "collision": "accident", "hospital": "medical hospital",
    "puc": "puc pollution", "pollution": "pollution puc", "rc": "registration rc",
    "car": "vehicle", "underage": "juvenile", "minor": "juvenile", "kid": "child",
    "signal": "red light signal", "insured": "insurance", "uninsured": "insurance",
    "compensation": "compensation claim", "pay": "pay payment",
}


def _stem(tok: str) -> str:
    for suf in ("ing", "ed", "es", "s"):
        if tok.endswith(suf) and len(tok) - len(suf) >= 4:
            return tok[: -len(suf)]
    return tok


def tokenize(text: str, expand: bool = False) -> list[str]:
    toks = re.findall(r"[a-z0-9]+", text.lower())
    out: list[str] = []
    for t in toks:
        if t in STOPWORDS:
            continue
        words = SYNONYMS.get(t, t).split() if expand else [t]
        out.extend(_stem(w) for w in words if w not in STOPWORDS)
    return out


class BM25Index:
    mode = "BM25 keyword search (pure Python) + IDF-weighted answerability gate"

    def __init__(self, chunks: list[Chunk], k1: float = 1.5, b: float = 0.75):
        self.chunks = chunks
        self.k1, self.b = k1, b
        # Section heading is weighted by repeating it in the indexed text.
        self.docs = [tokenize(f"{c.section} {c.section} {c.text}", expand=True)
                     for c in chunks]
        self.tf = [Counter(d) for d in self.docs]
        self.avgdl = sum(len(d) for d in self.docs) / max(len(self.docs), 1)
        df = Counter(t for d in self.docs for t in set(d))
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    @property
    def states(self) -> list[str]:
        return sorted({c.state for c in self.chunks if c.state})

    def search(self, query: str, k: int = 5, min_official: int = 2,
               state: str | list[str] | None = None, min_state: int = 1
               ) -> list[tuple[Chunk, float]]:
        """Top-k hits, guaranteeing at least `min_official` statute passages so
        every answer can be traced to the Act itself, not only to a summary.
        Only the selected States' notifications (plus a State named in the
        question) are eligible; each contributes at least `min_state` passages
        when it matches at all."""
        states = [state] if isinstance(state, str) else list(state or [])
        detected = detect_state(query, self.states)
        if detected and detected not in states:
            states.append(detected)
        ranked = [h for h in self._rank(query) if h[0].state in ("", *states)]
        picked = [h for s in states for h in [h for h in ranked if h[0].state == s][:min_state]]
        picked += [h for h in ranked if h[0].kind == "official"][:min_official]
        for h in ranked:
            if len(picked) >= k:
                break
            if h not in picked:
                picked.append(h)
        return sorted(picked, key=lambda h: -h[1])

    def _rank(self, query: str) -> list[tuple[Chunk, float]]:
        q = tokenize(query, expand=True)
        scores = []
        for i, tf in enumerate(self.tf):
            dl = len(self.docs[i])
            s = 0.0
            for t in set(q):
                if t in tf:
                    f = tf[t]
                    s += self.idf[t] * f * (self.k1 + 1) / (
                        f + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
            scores.append(s)
        ranked = sorted(range(len(scores)), key=scores.__getitem__, reverse=True)
        return [(self.chunks[i], scores[i]) for i in ranked if scores[i] > 0]


def term_coverage(query: str, hits: list[tuple[Chunk, float]],
                  idf: dict[str, float]) -> float:
    """IDF-weighted share of query terms (or a synonym) found in the hits.
    Terms unseen in the corpus get the maximum weight, so one unmatched
    specific word ("Karnataka", "IPL") outweighs generic matches ("vehicle")."""
    # Skip numbers (ages, years, amounts) and place names: a place only routes
    # the question to a State, it is not something the passages must contain.
    places = {t for name in [*STATE_ALIASES, *ALL_STATES, *ALL_UNION_TERRITORIES]
              for t in tokenize(name)}
    terms = [t for t in tokenize(query) if not t.isdigit() and t not in places]
    if not terms:
        return 0.0
    vocab = {t for c, _ in hits for t in tokenize(f"{c.section} {c.text}", expand=True)}
    max_idf = max(idf.values())
    total = known = 0.0
    for t in terms:
        forms = [t] + tokenize(t, expand=True)
        w = max((idf.get(f, 0.0) for f in forms), default=0.0) or max_idf
        total += w
        if any(f in vocab for f in forms):
            known += w
    return known / total


def is_answerable(query: str, hits: list[tuple[Chunk, float]],
                  index: "BM25Index") -> bool:
    """Cheap pre-filter; the system prompt's "I don't know" rule is the second guard."""
    return (bool(hits) and hits[0][1] >= MIN_SCORE
            and term_coverage(query, hits, index.idf) >= MIN_COVERAGE)


# ---------------------------------------------------------------- generate

SYSTEM_PROMPT = """You answer questions about Indian traffic law: the Motor Vehicles Act, \
traffic fines and challans, what to do after an accident, and driving licences.

Passages are of three kinds: kind="official" is verbatim text of the Motor Vehicles Act, \
1988 (as amended) and gives the statutory (court) penalty; kind="state" is a State \
Government compounding notification under Section 200, giving the amount an authorised \
officer collects in that State to settle the offence without court; kind="guide" is a \
plain-language summary (procedures, portals, schemes).

Rules:
- If an official passage and a guide disagree, the official passage is authoritative.
- When a state passage covers the offence, lead with that State's compounding amount and \
name the State and notification, then give the statutory penalty under the Act for \
comparison. If no state passage covers it, give the Act's penalty and note that States \
may notify different compounding amounts.
- Use ONLY the numbered passages in <context>. Do not use outside knowledge, even if you \
believe it is correct or more recent.
- If the passages do not contain the answer, reply exactly: "I don't know. My documents \
don't cover this question." and nothing else.
- If they answer only part of the question, answer that part and say plainly which part \
is not covered.
- Cite every factual sentence with the passage number(s) in square brackets, e.g. [1] or \
[2][3]. Only cite passages you actually used.
- Quote fine amounts, section numbers and time limits exactly as written in the passages.
- Be concise: lead with the direct answer (amount, rule or steps), then short supporting \
detail. Use a numbered list for procedures.
- Where amounts can differ by State, say so if the passages mention it.
- This is general legal information, not legal advice."""


def build_context(hits: list[tuple[Chunk, float]]) -> str:
    parts = []
    for i, (c, _) in enumerate(hits, 1):
        state = f' state="{c.state}"' if c.state else ""
        parts.append(f'<passage id="{i}" kind="{c.kind}"{state} source="{c.label}">\n'
                     f'{c.text}\n</passage>')
    return "<context>\n" + "\n\n".join(parts) + "\n</context>"


def generate(question: str, hits: list[tuple[Chunk, float]],
             api_key: str | None = None) -> Iterator[str]:
    """Stream a grounded answer from Claude. Raises if `anthropic` is missing."""
    import anthropic

    client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
    user = f"{build_context(hits)}\n\nQuestion: {question}"
    with client.beta.messages.stream(
        model=MODEL,
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        thinking={"type": "adaptive"},
        output_config={"effort": "low"},
        # Re-run on a fallback model server-side if a safety classifier declines.
        betas=["server-side-fallback-2026-07-01"],
        extra_body={"fallbacks": "default"},
        messages=[{"role": "user", "content": user}],
    ) as stream:
        for text in stream.text_stream:
            yield text
        final = stream.get_final_message()
    if final.stop_reason == "refusal":
        yield "\n\n_The model declined to answer this request._"
    elif final.stop_reason == "max_tokens":
        yield "\n\n_(Answer truncated.)_"


def extractive_answer(hits: list[tuple[Chunk, float]]) -> str:
    """Fallback when no LLM is configured: return the best passage verbatim."""
    c = hits[0][0]
    return f"**{c.section}** [1]\n\n{c.text}"


def llm_configured(api_key: str | None = None) -> bool:
    try:
        import anthropic  # noqa: F401
    except ImportError:
        return False
    return bool(api_key or os.environ.get("ANTHROPIC_API_KEY"))


def answer(question: str, index: BM25Index, state: str | list[str] | None = None, k: int = 5,
           api_key: str | None = None) -> dict:
    """One-call pipeline for UIs and tests: retrieve -> gate -> generate -> cite.

    Returns {"answer", "answerable", "sources" (cited (Chunk, score) pairs),
    "hits" (all retrieved, best first), "llm" (False = retrieval-only fallback)}.
    API errors from the LLM propagate to the caller.
    """
    hits = index.search(question, k=k, state=state)
    result = {"answer": IDK, "answerable": False, "sources": [], "hits": hits,
              "llm": llm_configured(api_key)}
    if not is_answerable(question, hits, index):
        return result
    if not result["llm"]:
        # No LLM: show each selected State's notice (more specific), else the best passage.
        best = [h for h in hits if h[0].kind == "state"] or hits[:1]
        text = "\n\n---\n\n".join(f"**{c.section}** [{i}]\n\n{c.text}"
                                  for i, (c, _) in enumerate(best, 1))
        result.update(answer=text, answerable=True, sources=best)
        return result
    text = "".join(generate(question, hits, api_key))
    if text.startswith("I don't know"):
        result["answer"] = text
        return result
    cited = sorted({int(n) for n in re.findall(r"\[(\d+)\]", text) if 0 < int(n) <= len(hits)})
    result.update(answer=text, answerable=True,
                  sources=[hits[n - 1] for n in cited] or hits[:1])
    return result


if __name__ == "__main__":
    import sys

    idx = BM25Index(load_chunks())
    q = " ".join(sys.argv[1:]) or "What is the fine for not wearing a helmet?"
    for c, s in idx.search(q):
        print(f"{s:6.2f}  {c.label}")
