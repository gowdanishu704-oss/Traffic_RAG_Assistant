"""Scan Document: explain an uploaded traffic document (challan, notice, receipt...).

Flow: read the file -> Claude extracts summary / key details / sections /
difficult terms (structured JSON) -> each section is looked up in the official
Act text in the knowledge base -> Claude explains each section using ONLY that
text. Without an LLM, text files still get section lookup and a built-in glossary.
"""

from __future__ import annotations

import base64
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import rag

MAX_BYTES = 10 * 1024 * 1024
IMAGE_TYPES = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
               "webp": "image/webp"}
FILE_TYPES = ["pdf", "txt", *IMAGE_TYPES]

# Fallback glossary (used when no LLM is configured).
GLOSSARY = {
    "challan": "An official ticket or notice for a traffic offence, stating the offence and the fine.",
    "e-challan": "An electronic challan issued by traffic police or a traffic camera, linked to the vehicle number.",
    "compounding": "Settling an offence by paying a fixed amount to an authorised officer instead of going to court (Section 200).",
    "compoundable": "An offence that can be settled by paying a fixed amount instead of going to court.",
    "impound": "When the police or an authority takes and holds a document (such as a licence) or vehicle.",
    "detain": "To keep a vehicle in official custody for a period, for example under Section 207.",
    "summons": "An official order to appear before a court on a given date.",
    "cognizable": "An offence for which the police can register a case and arrest without a court warrant.",
    "non-cognizable": "An offence for which the police need a magistrate's permission to investigate.",
    "virtual court": "An online court that disposes of traffic challans; you can pay or choose to contest.",
    "lok adalat": "A 'people's court' that settles pending cases, including traffic challans, often at a reduced amount.",
    "mact": "Motor Accident Claims Tribunal: the court that decides compensation claims for road accidents.",
    "claims tribunal": "The Motor Accident Claims Tribunal, which decides compensation for road-accident death, injury or damage.",
    "fir": "First Information Report: the first written police record of a cognizable offence.",
    "disqualification": "A period during which a person is not allowed to hold or get a driving licence.",
    "endorsement": "A record of an offence written on a driving licence.",
    "registration certificate": "The RC: the official document proving a vehicle is registered and who owns it.",
    "puc": "Pollution Under Control certificate, showing the vehicle meets emission standards.",
    "third party insurance": "Compulsory insurance covering the owner's liability for death, injury or damage caused to others (Section 146).",
    "good samaritan": "A person who helps a road-accident victim in good faith; protected from legal liability (Section 134A).",
    "ex parte": "A court decision made without hearing one party because they did not appear.",
    "adjournment": "Postponing a court hearing to a later date.",
    "penalty": "The punishment for an offence: a fine, imprisonment, licence disqualification or a mix.",
    "imprisonment": "Being sent to jail for a period ordered by a court.",
    "juvenile": "A person under 18 years of age.",
    "solatium": "Fixed compensation paid to victims of hit-and-run accidents (Section 161).",
}

# "Section 194D", "u/s 185", "S. 177", "190(2) MVA", "184 of the M.V. Act".
# Section letters must be capitals ("194D"), so "184 of" is not read as "184OF".
_SUB = r"(?:\s*\(\w{1,4}\))*"
SECTION_RE = re.compile(
    rf"(?:\bsec(?:tion)?s?\.?|\bu/s\.?|\bs\.|§)\s*(\d{{1,3}})(?:\s*-?\s*(?-i:([A-Z]{{1,2}}))\b)?"
    rf"|\b(\d{{1,3}})(?:\s*-?\s*(?-i:([A-Z]{{1,2}}))\b)?{_SUB}\s*(?:of\s+(?:the\s+)?)?"
    rf"(?:MVA|M\.\s*V\.\s*Act|MV\s*Act|Motor\s+Vehicles\s+Act)",
    re.I)


# ---------------------------------------------------------------- reading

def extract_text(data: bytes, ext: str) -> str | None:
    """Plain text from .txt, or from a text PDF via pypdf or pdftotext."""
    if ext == "txt":
        return data.decode("utf-8", errors="replace")
    if ext == "pdf":
        try:
            import io, pypdf
            reader = pypdf.PdfReader(io.BytesIO(data))
            text = "\n".join(page.extract_text() or "" for page in reader.pages).strip()
            if text:
                return text
        except Exception:
            pass
        if shutil.which("pdftotext"):
            with tempfile.TemporaryDirectory() as d:
                pdf = Path(d) / "doc.pdf"
                pdf.write_bytes(data)
                out = subprocess.run(["pdftotext", "-layout", str(pdf), "-"],
                                     capture_output=True, timeout=60)
                text = out.stdout.decode("utf-8", errors="replace").strip()
                return text or None   # empty = scanned PDF, needs the LLM
    return None


def find_sections(text: str) -> list[str]:
    """Section numbers mentioned in text, e.g. 'u/s 194D', 'Section 185', '177 MVA'."""
    found = []
    for m in SECTION_RE.finditer(text):
        num, letters = (m.group(1), m.group(2)) if m.group(1) else (m.group(3), m.group(4))
        sec = num + (letters or "").upper()
        if sec not in found:
            found.append(sec)
    return found


def normalise_section(raw: str) -> str | None:
    """'Section 194-D' / 'u/s 185 MVA' / '194D' -> '194D'; None if not an MV Act section."""
    if re.search(r"\b(rule|cmvr|bns|ipc|crpc)\b", raw, re.I):
        return None
    m = re.search(r"(\d{1,3})\s*-?\s*\(?([A-Za-z]{1,2})?\b", raw)
    if not m:
        return None
    letters = (m.group(2) or "").upper()
    return m.group(1) + (letters if letters.isalpha() else "")


def lookup_section(index: rag.BM25Index, sec: str) -> list[rag.Chunk]:
    """Official Act chunks for a section number (all parts of a long section)."""
    prefix = f"Section {sec}."
    return [c for c in index.chunks if c.kind == "official" and c.section.startswith(prefix)]


def glossary_terms(text: str) -> list[dict]:
    low = text.lower()
    return [{"term": t.title() if len(t) > 4 else t.upper(), "meaning": m}
            for t, m in GLOSSARY.items()
            if re.search(rf"\b{re.escape(t)}(?:s|d|ed|ing)?\b", low)]


# ---------------------------------------------------------------- LLM calls

READ_SCHEMA = {
    "type": "object",
    "properties": {
        "is_traffic_document": {"type": "boolean"},
        "document_type": {"type": "string"},
        "summary": {"type": "string"},
        "key_details": {"type": "array", "items": {
            "type": "object", "properties": {"label": {"type": "string"},
                                             "value": {"type": "string"}},
            "required": ["label", "value"], "additionalProperties": False}},
        "sections_mentioned": {"type": "array", "items": {"type": "string"}},
        "difficult_terms": {"type": "array", "items": {
            "type": "object", "properties": {"term": {"type": "string"},
                                             "meaning": {"type": "string"}},
            "required": ["term", "meaning"], "additionalProperties": False}},
        "next_steps": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["is_traffic_document", "document_type", "summary", "key_details",
                 "sections_mentioned", "difficult_terms", "next_steps"],
    "additionalProperties": False,
}

READ_PROMPT = """Read the attached document. The reader is an ordinary person in India who \
received it and wants to understand it.

Fill the JSON fields:
- is_traffic_document: true only if it relates to traffic, vehicles, driving licences, \
challans, road accidents or motor insurance.
- document_type: e.g. "e-challan", "court summons", "police seizure receipt", \
"insurance claim letter".
- summary: a plain-English summary of the entire document in 3-6 sentences: who issued it, \
to whom, what it is about, what is demanded and by when.
- key_details: the important facts exactly as written (challan or case number, date, vehicle \
number, offence, amount, deadline, court or office, officer).
- sections_mentioned: every legal section or rule cited, exactly as written \
(e.g. "Section 194D MVA", "u/s 185", "Rule 138 CMVR").
- difficult_terms: legal, technical or Hindi/regional terms in the document that an ordinary \
person may not understand, each with a one-sentence plain-English meaning in this context.
- next_steps: what the document asks the reader to do (pay, appear, reply, produce documents), \
with any deadline. Only what the document itself says or directly implies.

Use only what is in the document. If something is unreadable or missing, leave it out \
rather than guessing. If it is not a traffic document, set is_traffic_document to false and \
keep the other fields brief."""

EXPLAIN_SCHEMA = {
    "type": "object",
    "properties": {"explanations": {"type": "array", "items": {
        "type": "object", "properties": {"section": {"type": "string"},
                                         "explanation": {"type": "string"}},
        "required": ["section", "explanation"], "additionalProperties": False}}},
    "required": ["explanations"], "additionalProperties": False,
}


def _call_json(content: list, schema: dict, api_key: str | None) -> dict:
    import anthropic

    client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
    response = client.beta.messages.create(
        model=rag.MODEL,
        max_tokens=16000,
        thinking={"type": "adaptive"},
        output_config={"effort": "low",
                       "format": {"type": "json_schema", "schema": schema}},
        betas=["server-side-fallback-2026-07-01"],
        extra_body={"fallbacks": "default"},
        messages=[{"role": "user", "content": content}],
    )
    if response.stop_reason == "refusal":
        raise RuntimeError("The model declined to read this document.")
    if response.stop_reason == "max_tokens":
        raise RuntimeError("The document is too long to explain in one go.")
    text = next(b.text for b in response.content if b.type == "text")
    return json.loads(text)


def _file_block(data: bytes, ext: str, text: str | None) -> dict:
    if ext in IMAGE_TYPES:
        return {"type": "image", "source": {"type": "base64", "media_type": IMAGE_TYPES[ext],
                                            "data": base64.standard_b64encode(data).decode()}}
    if ext == "pdf":
        return {"type": "document", "source": {"type": "base64", "media_type": "application/pdf",
                                               "data": base64.standard_b64encode(data).decode()}}
    return {"type": "text", "text": f"<document>\n{text}\n</document>"}


def explain_sections(found: list[dict], api_key: str | None) -> dict[str, str]:
    """Plain-English explanation per section, grounded only in the Act text."""
    passages = "\n\n".join(
        f'<section id="{f["section"]}">\n' + "\n".join(c.text for c in f["chunks"]) + "\n</section>"
        for f in found)
    prompt = (f"{passages}\n\nFor each <section> above, explain in 2-3 plain-English sentences "
              "what it requires and the penalty it sets, for an ordinary driver in India. Use "
              "ONLY the text given; quote amounts exactly. Use the section id as `section`.")
    result = _call_json([{"type": "text", "text": prompt}], EXPLAIN_SCHEMA, api_key)
    return {e["section"]: e["explanation"] for e in result["explanations"]}


# ---------------------------------------------------------------- pipeline

def scan(data: bytes, filename: str, index: rag.BM25Index, api_key: str | None = None) -> dict:
    """Explain an uploaded document. Raises ValueError for unusable files."""
    ext = Path(filename).suffix.lower().lstrip(".")
    if ext not in FILE_TYPES:
        raise ValueError(f"Unsupported file type .{ext}. Use PDF, TXT, PNG, JPG or WEBP.")
    if len(data) > MAX_BYTES:
        raise ValueError("File is larger than 10 MB.")
    text = extract_text(data, ext)
    llm = rag.llm_configured(api_key)
    if not llm and not text:
        raise ValueError("Reading photos and scanned PDFs needs the language model. "
                         "Set ANTHROPIC_API_KEY, or upload a text PDF or .txt file.")

    if llm:
        read = _call_json([_file_block(data, ext, text), {"type": "text", "text": READ_PROMPT}],
                          READ_SCHEMA, api_key)
        raw_sections = read["sections_mentioned"]
    else:
        read = {"is_traffic_document": True, "document_type": "", "summary": "",
                "key_details": [], "difficult_terms": glossary_terms(text), "next_steps": []}
        raw_sections = find_sections(text)

    sections, seen = [], set()
    for raw in raw_sections:
        sec = normalise_section(raw)
        if sec in seen:
            continue
        seen.add(sec)
        chunks = lookup_section(index, sec) if sec else []
        sections.append({"raw": raw, "section": sec, "chunks": chunks, "explanation": ""})
    found = [s for s in sections if s["chunks"]]
    if llm and found:
        explained = explain_sections(found, api_key)
        for s in found:
            s["explanation"] = explained.get(s["section"], "")
    return {**read, "sections": sections, "llm": llm, "filename": filename}
