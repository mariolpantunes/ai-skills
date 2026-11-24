#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["mcp==2.3.0", "markitdown[docx,xlsx,pdf,pptx]==0.1.9"]
# ///
"""masked-reader: an MCP server that reads documents on this PC and returns ONLY masked text.

The agent can list, open, read by page, read a section and search. Every answer is masked with the same
rules as sensitive.py (tokens such as <NIF_1>, names from terms.txt). There is no tool that returns
a real value: the token-to-value map stays in private/map.json and only the user restores it.

Env: AI_HOME (default ~/ai); MASK_READER_DIR (originals, default $AI_HOME/private/in).
Run:  uv run masked_reader.py        (stdio; register it in Claude Desktop, Claude Code or goose)
"""
from __future__ import annotations

import os
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
for cand in (HERE, HERE.parent / "skills" / "mask-sensitive" / "scripts"):  # installed beside it, or in the repo
    if (cand / "sensitive.py").is_file():
        sys.path.insert(0, str(cand))
        break
import sensitive as S  # noqa: E402  (the masking rules live in one place)

from mcp.server.mcpserver import MCPServer  # noqa: E402

AI_HOME = Path(os.environ.get("AI_HOME", Path.home() / "ai"))
SRC = Path(os.environ.get("MASK_READER_DIR", AI_HOME / "private" / "in"))
PAGE = 3500  # characters per logical page of masked text
SUPPORTED = S.TEXT | S.OFFICE

app = MCPServer("masked-reader")
_cache: dict[str, tuple[float, str, Counter]] = {}


def _terms() -> list[tuple[str, str]]:
    return S.load_terms(AI_HOME / "private" / "terms.txt")


def _vault() -> "S.Vault":
    return S.Vault(AI_HOME / "private" / "map.json")


def _files() -> dict[str, Path]:
    """masked display name -> original path (the original name is never returned)."""
    out: dict[str, Path] = {}
    if not SRC.is_dir():
        return out
    v, terms = _vault(), _terms()
    for p in sorted(x for x in SRC.rglob("*") if x.is_file() and x.suffix.lower() in SUPPORTED):
        stem, _ = S.mask_text(p.stem, v, terms)
        name = S.TOKEN.sub(r"\1-\2", stem) + p.suffix.lower()
        out[name] = p
    v.save()
    return out


def _masked(name: str) -> tuple[str, Counter]:
    files = _files()
    if name not in files:
        raise ValueError(f"unknown document {name!r}; call list_documents first")
    p = files[name]
    m = p.stat().st_mtime
    if name in _cache and _cache[name][0] == m:
        return _cache[name][1], _cache[name][2]
    text = S.read_text(p)
    if len(text.strip()) < 20:
        raise ValueError("no text in this document (scanned or image); it is not shown")
    v = _vault()
    masked, n = S.mask_text(text, v, _terms())
    v.save()
    _cache[name] = (m, masked, n)
    return masked, n


def _pages(text: str) -> list[str]:
    pages, cur = [], ""
    for para in re.split(r"(?<=\n)\n", text):
        if cur and len(cur) + len(para) > PAGE:
            pages.append(cur)
            cur = ""
        cur += para + "\n"
    if cur.strip():
        pages.append(cur)
    return pages or [text]


@app.tool()
def list_documents() -> str:
    """List the documents available, by masked name, with their type and size in pages."""
    files = _files()
    if not files:
        return "no documents: the user must put files in the private input folder"
    lines = []
    for name in files:
        try:
            t, _ = _masked(name)
            lines.append(f"{name}: {len(_pages(t))} page(s)")
        except ValueError as e:
            lines.append(f"{name}: not readable ({e})")
    return "\n".join(lines)


@app.tool()
def open_document(name: str) -> str:
    """Show the outline (headings with their page) and the kinds of values that were masked (counts only)."""
    text, n = _masked(name)
    pages = _pages(text)
    out = [f"{name}: {len(pages)} page(s), {len(text)} characters (masked)"]
    for i, pg in enumerate(pages, 1):
        for h in re.findall(r"^#{1,4} .+$", pg, re.M):
            out.append(f"  p{i}: {h}")
    out.append("masked: " + (", ".join(f"{k} x{v}" for k, v in sorted(n.items())) or "nothing found"))
    return "\n".join(out)


@app.tool()
def read_pages(name: str, start: int = 1, count: int = 1) -> str:
    """Read `count` masked pages from page `start` (1-based). Tokens like <NIF_1> stand for real values you must never guess."""
    pages = _pages(_masked(name)[0])
    s = max(1, start)
    if s > len(pages):
        return f"{name} has {len(pages)} page(s)"
    e = min(len(pages), s + max(1, count) - 1)
    return "\n".join(f"--- page {i} of {len(pages)} ---\n{pages[i - 1]}" for i in range(s, e + 1))


@app.tool()
def read_section(name: str, heading: str) -> str:
    """Read the masked text of one section, found by (part of) its heading."""
    text = _masked(name)[0]
    heads = list(re.finditer(r"^(#{1,4}) (.+)$", text, re.M))
    for i, m in enumerate(heads):
        if heading.lower() in m.group(2).lower():
            end = next((h.start() for h in heads[i + 1:] if len(h.group(1)) <= len(m.group(1))), len(text))
            return text[m.start():end]
    return "no heading contains that text; call open_document for the outline"


@app.tool()
def search_document(name: str, query: str, context: int = 80) -> str:
    """Search the masked text (case-insensitive); returns page numbers and short masked snippets. A query with a token finds that token."""
    pages = _pages(_masked(name)[0])
    hits = []
    for i, pg in enumerate(pages, 1):
        for m in re.finditer(re.escape(query), pg, re.I):
            a, b = max(0, m.start() - context), min(len(pg), m.end() + context)
            hits.append(f"p{i}: ...{pg[a:b].strip()}...".replace("\n", " "))
            if len(hits) >= 30:
                return "\n".join(hits) + "\n(first 30 matches)"
    return "\n".join(hits) or "no match"


if __name__ == "__main__":
    app.run()
