#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["markitdown[docx,xlsx,pdf,pptx]==0.1.9"]
# ///
"""Convert documents (docx, xlsx, pptx, pdf, html, csv) to Markdown, one .md per file."""
import argparse
import sys
from pathlib import Path

from markitdown import MarkItDown

EXT = {".docx", ".xlsx", ".pptx", ".pdf", ".html", ".htm", ".csv", ".json", ".xml"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("src", type=Path, help="a file or a folder")
    ap.add_argument("--out", type=Path, required=True, help="folder for the .md files")
    a = ap.parse_args()
    files = [a.src] if a.src.is_file() else sorted(p for p in a.src.rglob("*") if p.suffix.lower() in EXT)
    a.out.mkdir(parents=True, exist_ok=True)
    md, bad = MarkItDown(), 0
    for f in files:
        try:
            text = md.convert(str(f)).text_content
        except Exception as e:  # report and go on
            print(f"FAIL {f.name}: {e}", file=sys.stderr)
            bad += 1
            continue
        if len(text.strip()) < 20:
            print(f"EMPTY {f.name}: no text (scanned or image?)", file=sys.stderr)
            bad += 1
        (a.out / (f.stem + ".md")).write_text(text, encoding="utf-8")
        print(f"OK {f.name} -> {f.stem}.md ({len(text)} chars)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
