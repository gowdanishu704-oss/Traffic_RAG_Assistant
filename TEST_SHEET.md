# Test Sheet: Challan Saathi (Indian Traffic Law RAG)

Knowledge base: **376 chunks of the official Motor Vehicles Act, 1988 text (as amended in 2019)** plus 46 summary-guide chunks.
Five questions: four that the documents can answer, from different areas, and one that the app must answer with "I don't know".
To re-run them: `python eval.py` checks retrieval and the "I don't know" gate; `python eval.py --llm` also generates answers with Claude.

| # | Question | Expected answer (from the documents) | Expected source | Retrieval result |
|---|----------|--------------------------------------|-----------------|------------------|
| 1 | What is the fine for riding a bike without a helmet? | Rs 1,000 fine and 3 months' disqualification from holding a licence; applies to everyone above 4 years old on a motorcycle; Sikhs wearing turbans are exempt | **Act Sec 194D + Sec 129**; guide "Helmet rule" | PASS, rank 1; Act sections 129 and 194D retrieved |
| 2 | Within how many hours must I report an accident to the police? | As soon as possible and within 24 hours if no police officer is present; also get medical help for the injured and inform the insurer; failing this: up to 6 months or Rs 5,000 (Sec 187) | **Act Sec 134**; guide "Legal duty of the driver" | PASS, rank 2; Act sections 134, 159, 158 retrieved |
| 3 | I got my driving licence at 25. When does it expire and when can I renew it? | Valid until age 40; renewal can be applied for up to 1 year before or within 1 year after expiry; more than 1 year late means the authority **shall refuse** renewal unless a retest is passed; medical certificate needed if aged 40+ | **Act Sec 14, Sec 15**; guide "Validity" | PASS, rank 1; Act section 15 retrieved |
| 4 | How do I contest a wrong e-challan? | Raise a grievance on the e-challan or traffic police portal with evidence; in the Virtual Court choose to contest, and the case moves to a regular court | guide "How to contest a wrong challan" (procedure, not in the Act) | PASS, rank 1 |
| 5 | What is the road tax for an electric car in Karnataka? | **"I don't know"**: road tax is set by State Motor Vehicles Taxation Acts, which are not indexed | none | PASS, blocked by the gate (coverage 0.67 < 0.75) |

## Extra probes (in `eval.py`)
| Question | Outcome |
|---|---|
| Penalty for drunk driving a second time? | Act Sec 185 at rank 1: up to 2 years, or a fine of **Rs 15,000**, or both |
| Is a DigiLocker copy of my RC valid? | Guide (Rule 139) at rank 1 |
| Compensation for a hit-and-run death? | Act Sec 161: Rs 2 lakh (death), Rs 50,000 (grievous hurt) |
| What happens if a minor drives a car? | Act Sec 199A at rank 1 (via the synonym minor → juvenile) |
| Penalty for not giving way to an ambulance? | Act Sec 194E at rank 1 |
| Fine for driving without insurance? | Act Sec 196 at rank 1 |
| Helmet fine in Bengaluru? | Karnataka notice: **Rs 500** (State detected from the city name; Tamil Nadu passages excluded) |
| Mobile phone while driving a car in Karnataka? | Karnataka notice: Rs 3,000 for an LMV, first offence; Rs 10,000 for a repeat |
| Can I pay a spot fine for drunk driving in Karnataka? | Karnataka notice: Sec 185 is not compoundable, so the case goes to court |
| Overspeeding fine for a car in Mysuru? | Karnataka notice: Rs 1,000 |
| Helmet fine in Chennai? | Tamil Nadu notice: **Rs 1,000** |
| Driving without PUC in Tamil Nadu? | Tamil Nadu notice: Sec 190(2), Rs 10,000 |
| Jumping a red light in Coimbatore? | Tamil Nadu notice: Sec 184, Rs 1,000 first offence, Rs 10,000 repeat |
| Who won the IPL in 2024? / Capital of France? | Blocked by the gate |
| How do I apply for a passport? | **Known failure of the gate.** "Passport" appears in the licence and IDP text, so the gate lets it through. The prompt's "I don't know" rule has to catch it at the generation step. |

## Failure cases noted
1. **Keyword overlap gets past the gate.** Out-of-scope questions whose words all appear in the Act (such as "passport") reach the LLM. The prompt's "I don't know" rule is the second guard.
2. **The summaries contained errors.** Comparing them with the official text found five mistakes: Sec 185's repeat-offence fine is a fixed Rs 15,000, and the "within 3 years" condition was removed in 2019; Sec 177A is Rs 500–1,000; Sec 187 and Sec 184 set fixed fines; Sec 179 is "up to" Rs 2,000. All five are fixed, and the prompt now treats official text as authoritative.
3. **Legal wording vs everyday wording.** The Act says "protective headgear", "handheld communications devices" and "juvenile". Without the synonym map, BM25 misses these. Phrasings not on the list may still retrieve weakly; adding embeddings for hybrid search is the next step.
4. **Only 2 States are covered.** Karnataka and Tamil Nadu compounding notifications are indexed. Other States fall back to the central Act amounts with a note. Delhi and Maharashtra were checked: for Delhi only news reports could be found online (no official text), and the only Maharashtra PDF found dated from 2016 (pre-2019 amounts, such as "up to Rs 2,000" for drunk driving), so both were left out. The Karnataka notification is from 2019; later amendments, if any, are not indexed.
5. **State names are skipped by the gate.** All 28 States and 8 UTs can be selected, but only Karnataka and Tamil Nadu have fine notifications. State names are ignored when checking coverage, so "helmet fine in Kerala" gets an answer (central amounts, with a note). As a side effect, "road tax in Kerala" passes the gate, because "road" and "tax" both appear in the Act. With an LLM, the prompt's "I don't know" rule must catch it; in retrieval-only mode it shows an unrelated passage.
5a. **City names must be known.** A State is detected from its name or a listed city (`STATE_ALIASES`). A smaller town that isn't listed won't be detected, so pick the State in the sidebar instead.
6. **Rules aren't indexed.** Speed limits, PUC validity and licence fees are in the CMV Rules and notifications, not in the Act. "Speed limit on expressways" is correctly gated as "I don't know" (coverage 0.51).
