"""Measure how often retrieval finds the expected section (hit@k)."""

import json
from pathlib import Path

from sentence_transformers import SentenceTransformer

from retrieve import MODEL_NAME, load_index, search

QUESTIONS_FILE = Path("eval/my_questions.json")
RESULTS_FILE = Path("eval/results_retrieval.json")
K_VALUES = [1, 3, 5]


def is_match(found_section, expected_sections):
    """A hit is the expected section itself or one of its subsections (9.2.5 matches 9.2.5.1)."""
    return any(found_section == e or found_section.startswith(e + ".") for e in expected_sections)


def first_hit_rank(found_sections, expected_sections):
    """Return the position (1, 2, 3, ...) of the first correct section, or None."""
    for rank, section in enumerate(found_sections, start=1):
        if is_match(section, expected_sections):
            return rank
    return None


def main():
    questions = json.loads(QUESTIONS_FILE.read_text(encoding="utf-8"))
    model = SentenceTransformer(MODEL_NAME)
    chunks, embeddings = load_index()

    rows = []
    for q in questions:
        results = search(q["question"], model, chunks, embeddings, k=max(K_VALUES))
        found = [chunk["section"] for score, chunk in results]
        rows.append({
            "question": q["question"],
            "expected": q["expected"],
            "found": found,
            "rank": first_hit_rank(found, q["expected"]),
        })

    print(f"Questions: {len(rows)}\n")
    for k in K_VALUES:
        hits = sum(1 for r in rows if r["rank"] is not None and r["rank"] <= k)
        print(f"hit@{k}: {hits}/{len(rows)} = {hits / len(rows):.0%}")

    print("\nMissed at top 3:")
    for r in rows:
        if r["rank"] is None or r["rank"] > 3:
            print(f"  {r['question']}")
            print(f"    expected {r['expected']}, found {r['found'][:3]}")

    RESULTS_FILE.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved to: {RESULTS_FILE}")


if __name__ == "__main__":
    main()