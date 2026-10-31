"""Read a 3GPP specification (.docx) and split it into sections."""

import json
from pathlib import Path

from docx import Document

RAW_DIR = Path("data/raw")
OUT_FILE = Path("data/processed/sections.json")

# Paragraph styles that contain real content (see scripts/explore_docx.py).
TEXT_STYLES = {"Normal", "B1", "B2", "B3", "NO", "EX", "EW", "TF"}


def parse_heading(text):
    """Split a heading like '4.1\tOverall Architecture' into ('4.1', 'Overall Architecture')."""
    text = text.replace("\n", "\t")
    if "\t" not in text:
        return "", text.strip()
    number, title = text.split("\t", 1)
    number = number.split(" (")[0].rstrip(":").strip()
    return number, title.strip()


def load_sections(path):
    """Return a list of sections: {section, title, level, text}."""
    sections = []
    current = None

    for p in Document(path).paragraphs:
        style = p.style.name
        text = p.text.strip()

        if style.startswith("Heading"):
            number, title = parse_heading(p.text)
            current = {
                "section": number,
                "title": title,
                "level": int(style.split()[-1]),
                "paragraphs": [],
            }
            sections.append(current)
        elif style in TEXT_STYLES and text and current is not None:
            current["paragraphs"].append(text)

    result = []
    for s in sections:
        if s["paragraphs"]:
            result.append({
                "section": s["section"],
                "title": s["title"],
                "level": s["level"],
                "text": "\n".join(s["paragraphs"]),
            })
    return result


def main():
    path = next(RAW_DIR.glob("*.docx"))
    sections = load_sections(path)

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(sections, indent=2, ensure_ascii=False), encoding="utf-8")

    words = [len(s["text"].split()) for s in sections]
    print(f"File: {path.name}")
    print(f"Sections with text: {len(sections)}")
    print(f"Total words: {sum(words)}")
    print(f"Average words per section: {sum(words) // len(sections)}")
    print(f"Longest section: {max(words)} words")
    print(f"Saved to: {OUT_FILE}")

    example = sections[min(5, len(sections) - 1)]
    print(f"\nExample: {example['section']} {example['title']}")
    print(example["text"][:300])


if __name__ == "__main__":
    main()