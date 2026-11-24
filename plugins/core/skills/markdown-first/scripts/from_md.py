#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pypandoc_binary==1.17"]
# ///
"""Convert a Markdown file to Word (.docx) with pandoc (bundled)."""
import argparse
from pathlib import Path

import pypandoc

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("src", type=Path)
ap.add_argument("--out", type=Path, required=True)
a = ap.parse_args()
pypandoc.convert_file(str(a.src), "docx", outputfile=str(a.out))
print(f"OK {a.src.name} -> {a.out}")
