"""Answer a question using only retrieved TS 38.300 sections, with citations."""

import os
import sys

from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import CrossEncoder, SentenceTransformer

from retrieve import MODEL_NAME, RERANK_MODEL, build_bm25, hybrid_rerank_search, load_index

load_dotenv()
LLM_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini-2025-04-14")
TOP_K = 3

SYSTEM_PROMPT = """You answer questions about 3GPP specifications.
Rules:
- Use ONLY the context sections below. Do not use outside knowledge.
- After each fact, cite its source in square brackets, e.g. [TS 38.300 §4.1].
- If the context does not contain the answer, reply exactly: Not found in the provided sections.
- Keep the answer short: 2-5 sentences."""


class Assistant:
    """Loads all models and the index once, then answers many questions."""

    def __init__(self):
        self.chunks, self.embeddings = load_index()
        self.model = SentenceTransformer(MODEL_NAME)
        self.reranker = CrossEncoder(RERANK_MODEL)
        self.bm25 = build_bm25(self.chunks)
        self.client = OpenAI()

    def retrieve(self, question, k=TOP_K):
        return hybrid_rerank_search(
            question, self.model, self.reranker, self.bm25, self.chunks, self.embeddings, k=k
        )

    def answer(self, question, k=TOP_K):
        results = self.retrieve(question, k=k)
        response = self.client.chat.completions.create(
            model=LLM_MODEL,
            temperature=0,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Context:\n{build_context(results)}\n\nQuestion: {question}"},
            ],
        )
        return {
            "answer": response.choices[0].message.content.strip(),
            "sources": [(chunk["section"], chunk["title"], score) for score, chunk in results],
            "chunks": results,
        }


def build_context(results):
    """Turn retrieved chunks into a text block the LLM can read."""
    blocks = []
    for score, chunk in results:
        header = f"[{chunk['spec']} §{chunk['section']}] {chunk['title']}"
        blocks.append(f"{header}\n{chunk['text']}")
    return "\n\n---\n\n".join(blocks)


def main():
    question = " ".join(sys.argv[1:]) or "What is paging used for?"
    result = Assistant().answer(question)
    print(f"Question: {question}\n")
    print(result["answer"])
    print("\nRetrieved sections:")
    for section, title, score in result["sources"]:
        print(f"  [{score:.3f}] §{section} {title}")


if __name__ == "__main__":
    main()
