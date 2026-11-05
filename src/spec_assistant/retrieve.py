"""Retrieval: dense (embeddings), BM25 (keywords), hybrid (both) and reranking."""

import json
import re
import sys
from pathlib import Path

import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder, SentenceTransformer

CHUNKS_FILE = Path("data/processed/chunks.json")
EMBEDDINGS_FILE = Path("data/processed/embeddings.npy")
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
CANDIDATES = 20   # how many chunks the reranker re-scores
RRF_K = 60        # standard constant for reciprocal rank fusion


def load_index():
    chunks = json.loads(CHUNKS_FILE.read_text(encoding="utf-8"))
    embeddings = np.load(EMBEDDINGS_FILE)
    return chunks, embeddings


def tokenize(text):
    """Lowercase words, keeping 3GPP terms like rrc_inactive and 5gc together."""
    return re.findall(r"[a-z0-9_]+", text.lower())


def build_bm25(chunks):
    return BM25Okapi([tokenize(c["text"]) for c in chunks])


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


def rerank_with_scores(question, ranking, chunks, reranker):
    """Re-score the top candidates of any ranking; return (score, index) pairs, best first."""
    candidates = ranking[:CANDIDATES]
    scores = reranker.predict([(question, chunks[i]["text"]) for i in candidates])
    return sorted(zip((float(s) for s in scores), candidates), reverse=True)


def reranked(question, ranking, chunks, reranker):
    return [idx for score, idx in rerank_with_scores(question, ranking, chunks, reranker)]


def search(question, model, chunks, embeddings, k=3):
    """Baseline: k chunks with the highest cosine similarity (dense only)."""
    q = model.encode([question], normalize_embeddings=True)[0]
    scores = embeddings @ q
    top = np.argsort(-scores)[:k]
    return [(float(scores[i]), chunks[i]) for i in top]


def hybrid_rerank_search(question, model, reranker, bm25, chunks, embeddings, k=3):
    """Best method from eval/results_compare.json: hybrid candidates, reranked by a cross-encoder."""
    dense = dense_ranking(question, model, embeddings)
    keyword = bm25_ranking(question, bm25)
    hybrid = hybrid_ranking(dense, keyword)
    best = rerank_with_scores(question, hybrid, chunks, reranker)[:k]
    return [(score, chunks[idx]) for score, idx in best]


def main():
    question = " ".join(sys.argv[1:]) or "What does a gNB do?"
    chunks, embeddings = load_index()
    model = SentenceTransformer(MODEL_NAME)
    reranker = CrossEncoder(RERANK_MODEL)
    bm25 = build_bm25(chunks)

    print(f"Question: {question}\n")
    for score, chunk in hybrid_rerank_search(question, model, reranker, bm25, chunks, embeddings):
        print(f"[{score:.3f}] {chunk['spec']} §{chunk['section']} {chunk['title']}")
        print(f"        {chunk['text'][:150]}...\n")


if __name__ == "__main__":
    main()
