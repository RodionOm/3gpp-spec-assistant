"""Compare retrieval strategies on the same questions: dense, BM25, hybrid, and both with a reranker."""

import json
from pathlib import Path

from sentence_transformers import CrossEncoder, SentenceTransformer

from evaluate_retrieval import QUESTIONS_FILE, first_hit_rank
from retrieve import (
    MODEL_NAME,
    RERANK_MODEL,
    bm25_ranking,
    build_bm25,
    dense_ranking,
    hybrid_ranking,
    load_index,
    reranked,
)

RESULTS_FILE = Path("eval/results_compare.json")
K_VALUES = [1, 3, 5]


def main():
    questions = json.loads(QUESTIONS_FILE.read_text(encoding="utf-8"))
    chunks, embeddings = load_index()
    model = SentenceTransformer(MODEL_NAME)
    reranker = CrossEncoder(RERANK_MODEL)
    bm25 = build_bm25(chunks)

    methods = ["dense", "bm25", "hybrid", "dense+rerank", "hybrid+rerank"]
    ranks = {m: [] for m in methods}
    details = []

    for q in questions:
        dense = dense_ranking(q["question"], model, embeddings)
        keyword = bm25_ranking(q["question"], bm25)
        hybrid = hybrid_ranking(dense, keyword)
        rankings = {
            "dense": dense,
            "bm25": keyword,
            "hybrid": hybrid,
            "dense+rerank": reranked(q["question"], dense, chunks, reranker),
            "hybrid+rerank": reranked(q["question"], hybrid, chunks, reranker),
        }
        row = {"question": q["question"], "expected": q["expected"]}
        for m, ranking in rankings.items():
            found = [chunks[i]["section"] for i in ranking[:max(K_VALUES)]]
            rank = first_hit_rank(found, q["expected"])
            ranks[m].append(rank)
            row[m] = {"found": found[:3], "rank": rank}
        details.append(row)

    n = len(questions)
    print(f"Questions: {n}\n")
    print(f"{'method':<16}" + "".join(f"hit@{k:<6}" for k in K_VALUES))
    for m in methods:
        cells = []
        for k in K_VALUES:
            hits = sum(1 for r in ranks[m] if r is not None and r <= k)
            cells.append(f"{hits / n:<10.0%}")
        print(f"{m:<16}" + "".join(cells))

    RESULTS_FILE.write_text(json.dumps(details, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved to: {RESULTS_FILE}")


if __name__ == "__main__":
    main()
