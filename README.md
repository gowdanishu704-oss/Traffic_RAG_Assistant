# 🚦 Challan Saathi: Ask India's Traffic Law

A Retrieval-Augmented Generation (RAG) app that answers questions about **Indian traffic law**: the Motor Vehicles Act (2019 amendment), fine amounts, what to do after an accident, driving licence renewal, and e-challans. Every answer is grounded in the document collection and shows its sources. Questions the documents don't cover get **"I don't know"**.

**Why this domain:** everyone who drives deals with it, the answers are specific (a section number, a rupee amount, a deadline), and you can check them against the Act.

## Pipeline

| Step | What we do | Where |
|---|---|---|
| **01 Ingest** | **Official text:** `ingest.py` downloads the consolidated **Motor Vehicles Act, 1988 (as amended up to 2019)** PDF from a government site, extracts it with `pdftotext`, removes the contents pages, footnotes, amendment markers (`6[`, `]`, `9***`) and page numbers, and splits it into **one chunk per section**. 253 sections become 376 chunks, with long sections cut into 300-word windows that overlap by 50 words. Each chunk is tagged with its chapter. **Guides:** 4 Markdown summaries (46 chunks) cover practical procedures the Act doesn't describe, such as portals, steps and schemes. They were fact-checked against the Act text. | `ingest.py`, `data/official/`, `data/*.md` |
| **02 Retrieve** | **BM25** written in pure Python (no FAISS or embedding download, so it deploys easily), with a synonym map that links everyday words to the Act's wording (helmet → headgear, phone → handheld communications device, minor → juvenile) and light stemming. Every result set includes **at least 2 passages of official Act text**. | `rag.BM25Index` |
| **03 Generate** | **Claude (`claude-opus-5-5`)** answers **only** from the numbered passages, streamed into the UI. The system prompt requires exact amounts and section numbers, and the exact "I don't know" sentence when the passages don't contain the answer. Where the official text and a guide disagree, **the official text wins**. | `rag.generate` |
| **04 Cite** | Inline `[n]` citations in the answer, plus a **Sources** panel where each passage is labelled 📜 *Official Act text* or 📘 *Summary guide*, with its chapter, BM25 score and a link to the source PDF. | `app.show_sources` |

**State rules.** The Act gives the statutory (court) penalty. Each State also notifies **compounding amounts** under Sec 200, the on-the-spot fine an authorised officer collects, and these differ by State. The app indexes the official gazette notifications for:

| State | Notification | In force | Example: helmet (194D) |
|---|---|---|---|
| Karnataka | Transport Secretariat No. TD 250 TDO 2019 (Karnataka Gazette No. 781) | 21-09-2019 | Rs 500 |
| Tamil Nadu | G.O. Ms. No. 758, Home (Transport-VII), Notification No. II(2)/HO/811(a)/2022 (TN Gazette Extraordinary No. 491) | 20-10-2022 | Rs 1,000 |

Choose a State in the sidebar, or just name a State or city in the question ("helmet fine in **Chennai**"). Only that State's notification is searched; other States' notifications are never mixed in. With no State, answers use the central Act. Both gazettes are scanned or have misaligned table text, so they were **transcribed by reading the page images**, not by `pdftotext`, which put amounts in the wrong rows. To add a State, create `data/states/<state>.md` with a `State: <Name>` line and `## <State> fine for …` sections, and add its cities to `STATE_ALIASES` in `rag.py`.

**Scan Document.** Upload a challan, court notice, police receipt or insurance letter (PDF, photo or .txt, up to 10 MB). `scan.py` makes two Claude calls. The first reads the file (PDFs and photos natively, no OCR) and returns structured JSON: summary, key details, sections cited, difficult words and next steps. Each cited section is then **looked up in the official Act text**, and the second call explains it **using only that text**, shown next to the official wording. Without an API key, text PDFs and .txt files still get section lookup (with the official text) and a built-in legal glossary. Rules (CMVR), BNS and State Acts are flagged as "not in the knowledge base". The uploaded file is sent to the Claude API and is not stored.

**No model training is involved.** RAG keeps the LLM unchanged and grounds it in documents found at question time. Using "real data" means indexing the actual statute. To add more official texts (for example the Central Motor Vehicles Rules or State fine notifications), add them to `SOURCES` in `ingest.py` and run `python ingest.py`.

**Two layers of "I don't know":**
1. **Retrieval gate.** The app doesn't call the LLM if the best BM25 score is below 4.0, or if the IDF-weighted coverage of the question's terms in the retrieved passages is below 0.75. Rare words such as "Karnataka" or "IPL" weigh more than common ones such as "vehicle".
2. **Prompt rule.** The LLM must reply "I don't know" if the passages don't answer the question.

## Run locally

```bash
pip install -r requirements.txt
set ANTHROPIC_API_KEY=sk-ant-...     # PowerShell: $env:ANTHROPIC_API_KEY="sk-ant-..."
streamlit run app.py
```

Without an API key (or without the `anthropic` package), the app still works in **retrieval-only mode** and shows the best-matching passage. You can also paste a key into the sidebar.

## Test

```bash
python eval.py          # 5-question test sheet + probes: retrieval rank and the "I don't know" gate
python eval.py --llm    # also generates answers and checks that the LLM declines out-of-scope questions
python rag.py "fine for no seat belt"   # inspect raw retrieval
```

See **[TEST_SHEET.md](TEST_SHEET.md)** for the questions, expected answers, results and noted failure cases.

## Deploy (live link)

1. Push this folder to a GitHub repository.
2. On [share.streamlit.io](https://share.streamlit.io), create a new app from the repository with `app.py` as the main file.
3. Under **App settings → Secrets**, add `ANTHROPIC_API_KEY = "sk-ant-..."` (see `.streamlit/secrets.toml.example`).

## Project layout

```
app.py                        Streamlit UI (chat, sample questions, sources panel)
rag.py                        load chunks -> BM25 retrieve -> Claude generate -> cite
scan.py                       Scan Document: read upload -> summary, sections, glossary
ingest.py                     download official PDF -> clean -> section chunks (needs pdftotext)
packages.txt                  poppler-utils (pdftotext) for Streamlit Cloud
eval.py                       automated test sheet
data/official/*.jsonl         official Act text, one record per section (committed; built by ingest.py)
data/*.md                     summary guides (one ## section = one chunk)
data/states/*.md              State compounding-fine notifications (Karnataka, Tamil Nadu)
TEST_SHEET.md                 5-question test sheet + failure cases
```

## Data sources and limits
- **Official text:** [The Motor Vehicles Act, 1988, consolidated with the 2019 amendments](https://www.tourism.rajasthan.gov.in/content/dam/transport/transport-dept/pdf/Act&Rules/motor%20vehicle%20act,%201988.pdf), as hosted by the Rajasthan Transport Department. The India Code copy was unreachable (HTTP 504) at build time. The 2019 Amendment Act text is also available from [PRS India](https://prsindia.org/files/bills_acts/bills_parliament/2019/Motor%20Vehicles%20(Amendment)%20Act,%202019.pdf).
- **Guides:** plain-language summaries of the MV Act, the CMV Rules 1989 (Rule 139 digital documents, Rule 115 PUC), the MoRTH Parivahan, Sarathi and e-challan portals, the Hit and Run (2022) and Cashless Treatment (2025) schemes, and the BNS 2023. The penalty amounts in them were checked against the official text, and five errors were corrected (Sec 177A, 179, 184, 185, 187).
- Fine amounts are the **central** amounts; States can change them (Sec 210A). The Kolkata Traffic Police offences table was considered but left out: its PDF columns extract misaligned, and its amounts are specific to West Bengal.

To add a topic, drop a new `.md` file into `data/` with `## ` sections, or add a PDF to `ingest.py`. New files are indexed automatically on the next start.

*General legal information only, not legal advice.*
