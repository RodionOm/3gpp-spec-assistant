"""Answer a question using only retrieved TS 38.300 sections, with citations."""

import os
import sys

from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer

from retrieve import MODEL_NAME, load_index, search

load_dotenv()
LLM_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
TOP_K = 3

SYSTEM_PROMPT = """You answer questions about 3GPP specifications.
Rules:
- Use ONLY the context sections below. Do not use outside knowledge.
- After each fact, cite its source in square brackets, e.g. [TS 38.300 §4.1].
- If the context does not contain the answer, reply exactly: Not found in the provided sections.
- Keep the answer short: 2-5 sentences."""


def build_context(results):
    """Turn retrieved chunks into a text block the LLM can read."""
    blocks = []
    for score, chunk in results:
        header = f"[{chunk['spec']} §{chunk['section']}] {chunk['title']}"
        blocks.append(f"{header}\n{chunk['text']}")
    return "\n\n---\n\n".join(blocks)


def answer(question, model, chunks, embeddings, client, k=TOP_K):
    """Retrieve k chunks, ask the LLM, return the answer and its sources."""
    results = search(question, model, chunks, embeddings, k=k)
    context = build_context(results)

    response = client.chat.completions.create(
        model=LLM_MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ],
    )
    return {
        "answer": response.choices[0].message.content.strip(),
        "sources": [(chunk["section"], chunk["title"], score) for score, chunk in results],
    }


def main():
    question = " ".join(sys.argv[1:]) or "What is paging used for?"
    model = SentenceTransformer(MODEL_NAME)
    chunks, embeddings = load_index()
    client = OpenAI()

    result = answer(question, model, chunks, embeddings, client)
    print(f"Question: {question}\n")
    print(result["answer"])
    print("\nRetrieved sections:")
    for section, title, score in result["sources"]:
        print(f"  [{score:.3f}] §{section} {title}")


if __name__ == "__main__":
    main()