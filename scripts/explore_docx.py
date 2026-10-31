from collections import Counter
from pathlib import Path

from docx import Document

RAW_DIR = Path("data/raw")

docx_files = list(RAW_DIR.glob("*.docx"))
if not docx_files:
    raise SystemExit(f"No .docx file found in {RAW_DIR}")

path = docx_files[0]
doc = Document(path)
paragraphs = doc.paragraphs

print(f"File: {path.name}")
print(f"Paragraphs: {len(paragraphs)}")

style_counts = Counter(p.style.name for p in paragraphs)
print("\nParagraphs per style:")
for style, count in style_counts.most_common():
    print(f"  {style:<20} {count}")

print("\nFirst 15 headings:")
headings = [p for p in paragraphs if p.style.name.startswith("Heading")]
for p in headings[:15]:
    print(f"  {p.style.name:<10} | {p.text}")

STYLES_TO_CHECK = ["NO", "EX", "EW", "TH", "TF", "Heading 8"]
EXAMPLES_PER_STYLE = 2

print("\nExamples of unclear styles:")
for style in STYLES_TO_CHECK:
    print(f"\n=== {style} ===")
    found = 0
    for p in paragraphs:
        if p.style.name == style:
            print(f"  {p.text[:120]!r}")
            found += 1
            if found == EXAMPLES_PER_STYLE:
                break
    if found == 0:
        print("  (no paragraphs with this style)")