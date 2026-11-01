"""Split sections into chunks of similar size for retrieval."""

import json
import statistics
from pathlib import Path

SECTIONS_FILE = Path("data/processed/sections.json")
CHUNKS_FILE = Path("data/processed/chunks.json")
ABBREVIATIONS_FILE = Path("data/processed/abbreviations.json")

SPEC = "TS 38.300"
MAX_WORDS = 200
OVERLAP = 30
SKIP_SECTIONS = {"", "2"}       # Foreword (no number) and References
ABBREVIATIONS_SECTION = "3.1"


def split_words(text, max_words=MAX_WORDS, overlap=OVERLAP):
    """Split text into windows of max_words words; neighbours share `overlap` words."""
    words = text.split()
    if len(words) <= max_words:
        return [" ".join(words)]

    pieces = []
    step = max_words - overlap
    for start in range(0, len(words), step):
        pieces.append(" ".join(words[start:start + max_words]))
        if start + max_words >= len(words):
            break
    return pieces

def parse_abbreviations(text):
    """Turn lines like '5GC\t5G Core Network' into {'5GC': '5G Core Network'}."""
    result = {}
    for line in text.split("\n"):
        if "\t" in line:
            short, full = line.split("\t", 1)
            result[short.strip()] = full.strip()
    return result


def make_chunks(sections):
    chunks = []
    for s in sections:
        if s["section"] in SKIP_SECTIONS or s["section"] == ABBREVIATIONS_SECTION:
            continue
        for i, piece in enumerate(split_words(s["text"])):
            chunks.append({
                "id": f"{s['section']}#{i}",
                "spec": SPEC,
                "section": s["section"],
                "title": s["title"],
                "text": f"{s['title']}\n{piece}",
            })
    return chunks


def main():
    sections = json.loads(SECTIONS_FILE.read_text(encoding="utf-8"))
    chunks = make_chunks(sections)
    CHUNKS_FILE.write_text(json.dumps(chunks, indent=2, ensure_ascii=False), encoding="utf-8")

    abbreviations = {}
    for s in sections:
        if s["section"] == ABBREVIATIONS_SECTION:
            abbreviations = parse_abbreviations(s["text"])
    ABBREVIATIONS_FILE.write_text(json.dumps(abbreviations, indent=2, ensure_ascii=False), encoding="utf-8")

    sizes = [len(c["text"].split()) for c in chunks]
    print(f"Sections in: {len(sections)}")
    print(f"Chunks out: {len(chunks)}")
    print(f"Words per chunk: min {min(sizes)}, median {statistics.median(sizes)}, max {max(sizes)}")
    print(f"Abbreviations saved: {len(abbreviations)}")

    split = [c for c in chunks if c["id"].endswith("#1")]
    print(f"Sections split into several chunks: {len(split)}")
    print(f"\nExample chunk ids: {[c['id'] for c in chunks[:5]]}")


if __name__ == "__main__":
    main()