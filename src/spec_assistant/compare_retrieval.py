"""Compare retrieval strategies on the same questions: dense, BM25, hybrid, and both with a reranker."""

import json
import re
from pathlib import Path

import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder, SentenceTransformer

from evaluate_retrieval import QUESTIONS_FILE, first_hit_rank
from retrieve import MODEL_NAME, load_index

RESULTS_FILE = Path("eval/results_compare.json")
RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
K_VALUES = [1, 3, 5]
CANDIDATES = 20   # how many chunks the reranker re-scores
RRF_K = 60        # standard constant for reciprocal rank fusion


def tokenize(text):
    """Lowercase words, keeping 3GPP terms like rrc_inactive and 5gc together."""
    return re.findall(r"[a-z0-9_]+", text.lower())


def dense_ranking(question, model, embeddings):
    q = model.encode([question], normalize_embeddings=True)[0]
    return list(np.argsort(-(embeddings @ q)))


def bm25_ranking(question, bm25):
    return list(np.argsort(-bm25.get_scores(tokenize(question))))


def hybrid_ranking(dense, keyword):
    """Reciprocal rank fusion: a chunk ranked high by either method moves up."""
    scores = {}
    for ranking in (dense, keyword):
        for rank, idx in enumerate(ranking, start=1):
            scores[idx] = scores.get(idx, 0) + 1 / (RRF_K + rank)
    return sorted(scores, key=scores.get, reverse=True)


def reranked(question, ranking, chunks, reranker):
    """Re-score the top candidates of any ranking with a cross-encoder that reads question and chunk together."""
    candidates = ranking[:CANDIDATES]
    pairs = [(question, chunks[i]["text"]) for i in candidates]
    scores = reranker.predict(pairs)
    order = np.argsort(-np.array(scores))
    return [candidates[i] for i in order]


def main():
    questions = json.loads(QUESTIONS_FILE.read_text(encoding="utf-8"))
    chunks, embeddings = load_index()
    model = SentenceTransformer(MODEL_NAME)
    reranker = CrossEncoder(RERANK_MODEL)
    bm25 = BM25Okapi([tokenize(c["text"]) for c in chunks])

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