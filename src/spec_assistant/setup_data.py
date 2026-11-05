"""Build the index on a fresh server: download TS 38.300, then run ingest, chunk and embed."""

import io
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
DOCX = RAW_DIR / "38300-ib0.docx"
EMBEDDINGS = ROOT / "data" / "processed" / "embeddings.npy"
SPEC_URL = "https://www.3gpp.org/ftp/Specs/archive/38_series/38.300/38300-ib0.zip"
STEPS = ["ingest.py", "chunk.py", "embed.py"]


def download_spec():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(SPEC_URL, headers={"User-Agent": "ClauseFinder/1.0 (student project)"})
    with urllib.request.urlopen(request, timeout=60) as response:
        archive = zipfile.ZipFile(io.BytesIO(response.read()))
    name = next(n for n in archive.namelist() if n.endswith(".docx"))
    DOCX.write_bytes(archive.read(name))


def ensure_index():
    if EMBEDDINGS.exists():
        return
    if not DOCX.exists():
        download_spec()
    for step in STEPS:
        subprocess.run([sys.executable, str(Path(__file__).parent / step)], cwd=ROOT, check=True)


if __name__ == "__main__":
    ensure_index()
    print("Index ready:", EMBEDDINGS)
