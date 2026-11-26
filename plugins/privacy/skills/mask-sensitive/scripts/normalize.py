"""Normalise extracted document text before it is masked and read: one clean Markdown form.

Fixes what PDF extraction leaves behind: ligatures and odd spaces, words broken at line ends,
paragraphs cut at every line, page numbers; headers and footers go with PyMuPDF's layout analysis.
`pdf_to_markdown` keeps headings and tables (PyMuPDF layout analysis); `clean` works on any text.
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

LIGATURES = {"ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl", " ": " ", "​": "", "­": "", "’": "'", "“": '"', "”": '"'}


PAGENO = re.compile(r"\s*(?:page|pág\.?|p\.)?\s*\d+(?:\s*(?:/|of|de)\s*\d+)?\s*", re.I)


def drop_page_numbers(pages: list[str]) -> list[str]:
    """Remove lines that hold only a page number. Headers and footers are removed by the PDF layout analysis."""
    return ["\n".join(l for l in p.splitlines() if not (l.strip() and PAGENO.fullmatch(l))) for p in pages]


def clean(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    for a, b in LIGATURES.items():
        text = text.replace(a, b)
    text = re.sub(r"[ \t]+\n", "\n", text.replace("\r\n", "\n"))
    text = re.sub(r"(\w)-\n(?=[a-zà-ÿ])", r"\1", text)  # word broken at the line end
    lines, out = text.split("\n"), []
    for i, l in enumerate(lines):  # join the lines of one paragraph (not lists, tables, headings)
        if (out and l.strip() and out[-1].strip() and not re.match(r"\s*(?:[#>|*+-]|\d+[.)])\s", l) and not re.match(r"\s*(?:[#|]|[-*+] |\d+[.)] )", out[-1])
                and not re.search(r"[.:;!?]$", out[-1].strip()) and re.match(r"\s*[a-zà-ÿ(]", l)):
            out[-1] = out[-1].rstrip() + " " + l.strip()
        else:
            out.append(l.rstrip())
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip() + "\n"


def pdf_to_markdown(path: Path) -> str:
    """PDF -> clean Markdown; empty text when the PDF is a scan (no text layer)."""
    try:
        import pymupdf4llm
    except ImportError:
        from markitdown import MarkItDown

        return clean(MarkItDown().convert(str(path)).text_content)
    chunks = pymupdf4llm.to_markdown(str(path), page_chunks=True, show_progress=False, header=False, footer=False)
    pages = drop_page_numbers([c["text"] for c in chunks])
    return clean("\n\n".join(pages))
