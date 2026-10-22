"""Ingest official legal texts into section-level chunks.

    python ingest.py            # download (if missing), extract, clean, chunk

Downloads each source PDF to sources/raw/, extracts text with `pdftotext`
(poppler; ships with Git for Windows), strips footnotes / amendment markers /
page numbers, splits the Act into one chunk per section, and writes
data/official/<id>.jsonl, which rag.load_chunks() indexes alongside data/*.md.
"""

from __future__ import annotations

import json
import re
import subprocess
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
RAW_DIR = ROOT / "sources" / "raw"
OUT_DIR = ROOT / "data" / "official"

SOURCES = [
    {
        "id": "mv_act_1988",
        "title": "The Motor Vehicles Act, 1988 (as amended up to the 2019 Amendment)",
        "publisher": "Transport Department, Government of Rajasthan (official consolidated text)",
        "url": "https://www.tourism.rajasthan.gov.in/content/dam/transport/transport-dept/"
               "pdf/Act&Rules/motor%20vehicle%20act,%201988.pdf",
    },
]

MAX_WORDS = 300   # long sections are split into windows of this size...
OVERLAP = 50      # ...overlapping by this many words


def download(src: dict) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    pdf = RAW_DIR / f"{src['id']}.pdf"
    if not pdf.exists():
        req = urllib.request.Request(src["url"], headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=180) as r:
            data = r.read()
        if not data.startswith(b"%PDF"):
            raise RuntimeError(f"{src['url']} did not return a PDF")
        pdf.write_bytes(data)
    return pdf


def pdf_to_text(pdf: Path) -> str:
    out = subprocess.run(["pdftotext", "-layout", str(pdf), "-"],
                         capture_output=True, check=True)
    return out.stdout.decode("utf-8", errors="replace")


def clean(text: str) -> list[str]:
    """Drop the table of contents, footnote blocks and page numbers."""
    lines = text.replace("\f", "\n").splitlines()
    # The body starts at the second "CHAPTER I" (the first is in the contents).
    starts = [i for i, ln in enumerate(lines) if ln.strip() == "CHAPTER I"]
    lines = lines[starts[1]:] if len(starts) > 1 else lines

    kept, in_footnotes = [], False
    for ln in lines:
        if re.fullmatch(r"\s*\d{1,3}\s*", ln):          # page number ends a page
            in_footnotes = False
            continue
        if re.match(r"\d{1,3}\. (Subs|Ins|Omitted|The |Rep|Added|Clause|Sub-|Section|Certain|Renumbered|Proviso|Vide|Words|S\.|Cl\.|Explanation)", ln):
            in_footnotes = True                          # footnotes run to page end
        if not in_footnotes:
            kept.append(ln)
    return kept


def strip_markers(s: str) -> str:
    s = re.sub(r"(?<![\w.,])\d{1,3}\[", "", s)   # "6[(a) has..." -> "(a) has..."
    s = re.sub(r"\d{1,3}\*{3,}", "", s)          # "9***" omitted-text markers
    s = s.replace("[", "").replace("]", "")
    s = re.sub(r"-\n(?=[a-z])", "", s)            # de-hyphenate line breaks
    s = re.sub(r"[ \t]+", " ", s)
    return re.sub(r"\n\s*\n+", "\n", s).strip()


SECTION_RE = re.compile(r"^ {3,6}(?:\d{1,3}\[)?(\d{1,3}[A-Z]{0,2})\. (\S.*)$")
CHAPTER_RE = re.compile(r"^\s+(?:\d{1,3}\[)?CHAPTER ([IVXL]+[A-Z]?)\s*$")
SMALL_WORDS = {"of", "and", "or", "the", "to", "in", "for", "by", "on", "against"}


def title_case(s: str) -> str:
    words = s.lower().split()
    return " ".join(w if i and w in SMALL_WORDS else w.capitalize()
                    for i, w in enumerate(words))


def split_sections(lines: list[str]) -> list[dict]:
    sections, cur, chapter, pending_chapter = [], None, "", None
    for ln in lines:
        m = CHAPTER_RE.match(ln)
        if m:
            pending_chapter = f"Chapter {m.group(1)}"
            continue
        if pending_chapter and ln.strip():
            if ln.strip().isupper() or not SECTION_RE.match(ln):
                chapter = f"{pending_chapter}: {title_case(strip_markers(ln))}"
                pending_chapter = None
                continue
            chapter, pending_chapter = pending_chapter, None
        m = SECTION_RE.match(ln)
        if m:
            cur = {"no": m.group(1), "chapter": chapter, "lines": [m.group(2)]}
            sections.append(cur)
        elif cur is not None:
            cur["lines"].append(ln)

    out = []
    for s in sections:
        body = strip_markers("\n".join(s["lines"]))
        title, sep, rest = body.partition("--")
        if not sep or len(title) > 250:
            continue                                     # not a real section header
        title = " ".join(title.split()).rstrip(".")
        rest = rest.strip()
        if len(rest) < 40 and re.search(r"Rep\.|Omitted", rest + title):
            continue                                     # repealed / omitted section
        out.append({"no": s["no"], "title": title, "chapter": s["chapter"], "text": rest})
    return out


def to_chunks(src: dict, sections: list[dict]) -> list[dict]:
    chunks = []
    for s in sections:
        words = s["text"].split()
        windows = [words] if len(words) <= MAX_WORDS else [
            words[i:i + MAX_WORDS] for i in range(0, len(words) - OVERLAP, MAX_WORDS - OVERLAP)]
        for j, w in enumerate(windows, 1):
            part = f" (part {j}/{len(windows)})" if len(windows) > 1 else ""
            chunks.append({
                "doc_title": "Motor Vehicles Act, 1988 (official text)",
                "section": f"Section {s['no']}. {s['title']}{part}",
                "text": " ".join(w),
                "source_ref": f"{src['title']}; {s['chapter']}; {src['publisher']}",
                "url": src["url"],
            })
    return chunks


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for src in SOURCES:
        pdf = download(src)
        sections = split_sections(clean(pdf_to_text(pdf)))
        chunks = to_chunks(src, sections)
        out = OUT_DIR / f"{src['id']}.jsonl"
        with out.open("w", encoding="utf-8") as f:
            for c in chunks:
                f.write(json.dumps(c, ensure_ascii=False) + "\n")
        print(f"{src['id']}: {len(sections)} sections -> {len(chunks)} chunks -> {out}")


if __name__ == "__main__":
    main()
