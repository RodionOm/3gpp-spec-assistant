"""Find the chunks most similar to a question."""

import json
import sys
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

CHUNKS_FILE = Path("data/processed/chunks.json")
EMBEDDINGS_FILE = Path("data/processed/embeddings.npy")
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def load_index():
    chunks = json.loads(CHUNKS_FILE.read_text(encoding="utf-8"))
    embeddings = np.load(EMBEDDINGS_FILE)
    return chunks, embeddings


def search(question, model, chunks, embeddings, k=3):
    """Return the k chunks with the highest cosine similarity to the question."""
    q = model.encode([question], normalize_embeddings=True)[0]
    scores = embeddings @ q
    top = np.argsort(-scores)[:k]
    return [(float(scores[i]), chunks[i]) for i in top]


def main():
    question = " ".join(sys.argv[1:]) or "What does a gNB do?"
    model = SentenceTransformer(MODEL_NAME)
    chunks, embeddings = load_index()

    print(f"Question: {question}\n")
    for score, chunk in search(question, model, chunks, embeddings):
        print(f"[{score:.3f}] {chunk['spec']} §{chunk['section']} {chunk['title']}")
        print(f"        {chunk['text'][:150]}...\n")


if __name__ == "__main__":
    main()