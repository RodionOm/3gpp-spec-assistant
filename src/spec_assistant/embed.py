"""Turn every chunk into a vector (embedding) and save them."""

import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

CHUNKS_FILE = Path("data/processed/chunks.json")
EMBEDDINGS_FILE = Path("data/processed/embeddings.npy")
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def main():
    chunks = json.loads(CHUNKS_FILE.read_text(encoding="utf-8"))
    texts = [c["text"] for c in chunks]

    model = SentenceTransformer(MODEL_NAME)
    print(f"Model max tokens: {model.max_seq_length}")

    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=True,
        normalize_embeddings=True,
    )
    np.save(EMBEDDINGS_FILE, embeddings)

    print(f"Chunks: {len(chunks)}")
    print(f"Embeddings shape: {embeddings.shape}")
    print(f"Length of first vector: {np.linalg.norm(embeddings[0]):.3f}")
    print(f"Saved to: {EMBEDDINGS_FILE}")


if __name__ == "__main__":
    main()