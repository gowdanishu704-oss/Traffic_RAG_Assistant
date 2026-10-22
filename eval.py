"""Test sheet for the RAG pipeline. Importable: nothing runs at import time.

    python eval.py          # all tests + probes, retrieval and "I don't know" gate only
    python eval.py --llm    # also generate answers with Claude (needs ANTHROPIC_API_KEY)

    from eval import TESTS, run_tests      # used by the app's About page
"""

import sys

from rag import BM25Index, answer, load_chunks


def case(question, sections, expected):
    """sections: section-heading prefixes, any one in the top-k passes;
    None means the correct answer is "I don't know"."""
    return {"question": question, "sections": sections, "expected": expected}


# The 5-question test sheet (see TEST_SHEET.md).
TESTS = [
    case("What is the fine for riding a bike without a helmet?",
         ("Section 194D.", "Helmet rule for two-wheelers"),
         "Rs 1,000 + 3-month licence disqualification (Sec 194D)"),
    case("Within how many hours must I report an accident to the police?",
         ("Section 134.", "Legal duty of the driver after an accident"),
         "Within 24 hours (Sec 134)"),
    case("I got my driving licence at 25. When does it expire and when can I renew it?",
         ("Section 14.", "Validity of a driving licence", "When to renew a driving licence"),
         "Valid till age 40; renew up to 1 year before expiry (Sec 14, 15)"),
    case("How do I contest a wrong e-challan?",
         ("How to contest a wrong challan",),
         "Portal grievance, then contest in Virtual Court"),
    case("What is the road tax for an electric car in Karnataka?", None, "I don't know"),
]

# Extra probes run from the command line.
PROBES = [
    case("What is the penalty for drunk driving a second time?", ("Section 185.", "Drunk driving"),
         "Up to 2 years and/or Rs 15,000"),
    case("Is a DigiLocker copy of my RC valid?", ("Digital documents through DigiLocker",),
         "Yes (Rule 139)"),
    case("How much compensation is given for a hit and run death?",
         ("Section 161.", "Hit-and-run compensation"), "Rs 2 lakh"),
    case("What happens if a minor drives a car?", ("Section 199A.", "Offences by juveniles"),
         "Guardian/owner liable (Sec 199A)"),
    case("Penalty for not giving way to an ambulance?",
         ("Section 194E.", "Not giving way to emergency"), "Rs 10,000"),
    case("What is the fine for driving without insurance?",
         ("Section 196.", "Driving without insurance"), "Rs 2,000 / Rs 4,000"),
    # State notifications (State detected from the place name in the question)
    case("Helmet fine in Bengaluru?", ("Karnataka fine for not wearing a helmet",), "Rs 500"),
    case("Fine for using a mobile phone while driving a car in Karnataka?",
         ("Karnataka fine for using a mobile phone",), "Rs 3,000 (LMV)"),
    case("Can I pay a spot fine for drunk driving in Karnataka?",
         ("Karnataka: what a compounding fine is",), "No, not compoundable"),
    case("What is the overspeeding fine for a car in Mysuru?",
         ("Karnataka fine for overspeeding",), "Rs 1,000"),
    case("Helmet fine in Chennai?", ("Tamil Nadu fine for not wearing a helmet",), "Rs 1,000"),
    case("Fine for driving without a PUC in Tamil Nadu?", ("Tamil Nadu fine for pollution",),
         "Rs 10,000"),
    case("What is the fine for jumping a red light in Coimbatore?",
         ("Tamil Nadu fine for dangerous driving",), "Rs 1,000 / Rs 10,000"),
    case("Fine for violating a mandatory traffic sign in Madurai?",
         ("Tamil Nadu fine for general offences, traffic signs",), "Rs 500 / Rs 1,500"),
    case("Who won the IPL in 2024?", None, "I don't know"),
    case("What is the capital of France?", None, "I don't know"),
    case("How do I apply for a passport?", None, "I don't know"),
]


def run_tests(index: BM25Index, use_llm: bool = True, cases: list | None = None) -> list[dict]:
    """Run test cases; returns one dict per case:
    question, expected, passed, answer, detail.

    use_llm=False checks retrieval and the "I don't know" gate only. With
    use_llm=True the full pipeline runs (rag.answer falls back to the best
    passage when no API key is configured)."""
    results = []
    for c in TESTS if cases is None else cases:
        if use_llm:
            r = answer(c["question"], index)
        else:   # retrieval-only: same gate, no generation
            from rag import IDK, is_answerable
            hits = index.search(c["question"])
            ok = is_answerable(c["question"], hits, index)
            r = {"answer": "(retrieval only)" if ok else IDK, "answerable": ok, "hits": hits}
        sections = [ch.section for ch, _ in r["hits"]]
        if c["sections"] is None:
            passed = not r["answerable"]
            detail = "declined" if passed else f"answered from: {sections[:1]}"
        else:
            ranks = [i for i, s in enumerate(sections, 1) if s.startswith(c["sections"])]
            passed = r["answerable"] and bool(ranks)
            detail = f"expected section at rank {ranks[0] if ranks else '-'}"
        results.append({"question": c["question"], "expected": c["expected"],
                        "passed": passed, "answer": r["answer"], "detail": detail})
    return results


def main() -> int:
    use_llm = "--llm" in sys.argv
    index = BM25Index(load_chunks())
    print(f"Indexed {len(index.chunks)} chunks ({index.mode})\n")
    results = run_tests(index, use_llm=use_llm, cases=TESTS + PROBES)
    for i, r in enumerate(results, 1):
        tag = "TEST" if i <= len(TESTS) else "PROBE"
        print(f"[{'PASS' if r['passed'] else 'FAIL'}] {tag} {i}: {r['question']}\n"
              f"       expected: {r['expected']}; {r['detail']}")
        if use_llm:
            print("       answer: " + r["answer"].replace("\n", "\n               ") + "\n")
    passed = sum(r["passed"] for r in results)
    print(f"\n{passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
