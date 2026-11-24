#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["markitdown[docx,xlsx,pdf,pptx]==0.1.9"]
# ///
"""Mask, restore and scan sensitive data on this PC, before an AI agent sees a document.

  sensitive.py mask    [SRC] [--out DIR] [--terms FILE] [--map FILE]
  sensitive.py restore FILE  [--out FILE] [--map FILE]
  sensitive.py scan    [DIR] [--terms FILE]

Layout (env AI_HOME, default ~/ai):
  private/in   originals (never connect this folder to the agent)
  private/map.json   token <-> value map (never share)   private/terms.txt  your own names
  work/masked  masked copies: the only folder the agent gets
Output of mask and scan lists types and counts, never the values.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

HOME = Path(os.environ.get("AI_HOME", Path.home() / "ai"))
TEXT = {".md", ".txt", ".csv", ".tsv", ".json", ".eml", ".html", ".htm", ".xml"}
OFFICE = {".docx", ".xlsx", ".pptx", ".pdf"}
TOKEN = re.compile(r"<([A-Z]+)_(\d+)>")


# ---- validators ------------------------------------------------------------
def nif_ok(s: str) -> bool:
    if not re.fullmatch(r"\d{9}", s) or s[0] not in "123568" and s[:2] not in {"45", "70", "71", "72", "74", "75", "77", "78", "79", "90", "91", "98", "99"}:
        return False
    total = sum(int(c) * w for c, w in zip(s[:8], range(9, 1, -1)))
    check = 11 - total % 11
    return int(s[8]) == (0 if check >= 10 else check)


def iban_ok(s: str) -> bool:
    s = re.sub(r"\s", "", s).upper()
    if not 15 <= len(s) <= 34 or not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]+", s):
        return False
    r = s[4:] + s[:4]
    return int("".join(str(int(c, 36)) for c in r)) % 97 == 1


def luhn_ok(s: str) -> bool:
    d = [int(c) for c in re.sub(r"\D", "", s)]
    if not 13 <= len(d) <= 19:
        return False
    d.reverse()
    t = sum(x if i % 2 == 0 else (x * 2 - 9 if x * 2 > 9 else x * 2) for i, x in enumerate(d))
    return t % 10 == 0


# ---- detectors: (type, regex, validator); earlier wins on overlap ----------
DETECTORS = [
    ("SECRET", re.compile(r"\b(?:sk-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{30,})\b"), None),
    ("SECRET", re.compile(r"(?i)\b(?:password|palavra-passe|senha|pwd)[ \t]*[:=][ \t]*(?!<[A-Z]+_\d+>)(\S+)"), None),
    ("EMAIL", re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"), None),
    ("IBAN", re.compile(r"\b[A-Z]{2}\d{2}(?: ?[A-Z0-9]){11,30}\b"), iban_ok),
    ("CARD", re.compile(r"\b(?:\d[ -]?){13,19}\b"), luhn_ok),
    ("PHONE", re.compile(r"(?:\+|00)351[ .-]?\d{3}[ .-]?\d{3}[ .-]?\d{3}\b|\b[29]\d{2}[ .-]\d{3}[ .-]\d{3}\b"), None),
    ("NIF", re.compile(r"\b\d{9}\b"), nif_ok),
    ("PHONE", re.compile(r"\b9[1236]\d{7}\b"), None),
    ("ADDRESS", re.compile(r"\b(?:Rua|Av\.?|Avenida|Travessa|Pra[cç]a|Largo|Estrada|Street|St\.|Road)\s+[^,;\n\d]{2,40}?\s\d{1,4}\b"), None),
    ("POSTAL", re.compile(r"\b\d{4}-\d{3}\b"), None),
    ("PLATE", re.compile(r"\b(?=[A-Z0-9-]*[A-Z])(?=[A-Z0-9-]*\d)[A-Z0-9]{2}-[A-Z0-9]{2}-[A-Z0-9]{2}\b"), None),
]


def load_terms(path: Path | None) -> list[tuple[str, str]]:
    """Lines 'term' or 'TYPE: term'; '#' starts a comment. Longest first."""
    out: list[tuple[str, str]] = []
    if path and path.is_file():
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            m = re.match(r"([A-Z]{2,10}):\s*(.+)", line)
            out.append((m.group(1), m.group(2).strip()) if m else ("NAME", line))
    return sorted(out, key=lambda t: -len(t[1]))


def find_spans(text: str, terms: list[tuple[str, str]]) -> list[tuple[int, int, str]]:
    spans: list[tuple[int, int, str]] = []

    def free(a: int, b: int) -> bool:
        return all(b <= s or a >= e for s, e, _ in spans)

    for kind, rx, ok in DETECTORS:
        for m in rx.finditer(text):
            g = 1 if rx.groups else 0
            if (ok is None or ok(m.group(g))) and free(m.start(g), m.end(g)):
                spans.append((m.start(g), m.end(g), kind))
    for kind, term in terms:
        for m in re.finditer(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text, re.I):
            if free(m.start(), m.end()):
                spans.append((m.start(), m.end(), kind))
    return sorted(spans)


class Vault:
    """Stable value <-> token map, persisted as JSON (token -> value)."""

    def __init__(self, path: Path):
        self.path = path
        self.tok: dict[str, str] = json.loads(path.read_text("utf-8")) if path.is_file() else {}
        self.rev = {v.casefold(): t for t, v in self.tok.items()}

    def token(self, kind: str, value: str) -> str:
        t = self.rev.get(value.casefold())
        if t is None:
            n = 1 + sum(1 for k in self.tok if k.startswith(f"<{kind}_"))
            t = f"<{kind}_{n}>"
            self.tok[t], self.rev[value.casefold()] = value, t
        return t

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.tok, ensure_ascii=False, indent=1), encoding="utf-8")


def mask_text(text: str, vault: Vault, terms: list[tuple[str, str]]) -> tuple[str, Counter]:
    count: Counter = Counter()
    out, pos = [], 0
    for a, b, kind in find_spans(text, terms):
        out += [text[pos:a], vault.token(kind, text[a:b])]
        count[kind] += 1
        pos = b
    out.append(text[pos:])
    return "".join(out), count


def read_text(p: Path) -> str:
    if p.suffix.lower() in TEXT:
        return p.read_text(encoding="utf-8-sig", errors="replace")
    from markitdown import MarkItDown  # office and pdf

    return MarkItDown().convert(str(p)).text_content


# ---- commands --------------------------------------------------------------
def cmd_mask(a: argparse.Namespace) -> int:
    src = a.src or HOME / "private" / "in"
    out = a.out or HOME / "work" / "masked"
    terms = load_terms(a.terms or HOME / "private" / "terms.txt")
    vault = Vault(a.map or HOME / "private" / "map.json")
    files = [src] if src.is_file() else sorted(p for p in src.rglob("*") if p.is_file())
    out.mkdir(parents=True, exist_ok=True)
    bad = 0
    for f in files:
        ext = f.suffix.lower()
        if ext not in TEXT | OFFICE:
            print(f"SKIP  {f.name}: type not supported (images are never copied)")
            bad += 1
            continue
        try:
            text = read_text(f)
        except Exception as e:
            print(f"FAIL  {f.name}: {e}")
            bad += 1
            continue
        if len(text.strip()) < 20:
            print(f"EMPTY {f.name}: no text (scanned or image); not copied")
            bad += 1
            continue
        masked, n = mask_text(text, vault, terms)
        stem, _ = mask_text(f.stem, vault, terms)
        stem = TOKEN.sub(r"\1-\2", stem)  # < and > are not allowed in Windows file names
        dest = out / (stem + (ext if ext in {".csv", ".tsv", ".txt", ".json"} else ".md"))
        dest.write_text(masked, encoding="utf-8")
        print(f"OK    {f.name} -> {dest.name}: " + (", ".join(f"{k}x{v}" for k, v in sorted(n.items())) or "nothing found"))
    vault.save()
    print(f"map: {vault.path} ({len(vault.tok)} values, keep it private)")
    return 1 if bad else 0


def cmd_restore(a: argparse.Namespace) -> int:
    vault = Vault(a.map or HOME / "private" / "map.json")
    text = a.file.read_text(encoding="utf-8")
    unknown = {m.group() for m in TOKEN.finditer(text) if m.group() not in vault.tok}
    text = TOKEN.sub(lambda m: vault.tok.get(m.group(), m.group()), text)
    dest = a.out or HOME / "private" / "restored" / a.file.name  # never next to the shared copy
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")
    print(f"OK restored -> {dest}" + (f" ({len(unknown)} unknown tokens left)" if unknown else ""))
    return 0


def cmd_scan(a: argparse.Namespace) -> int:
    root = a.dir or HOME / "work"
    terms = load_terms(a.terms or HOME / "private" / "terms.txt")
    found = 0
    for f in sorted(p for p in root.rglob("*") if p.is_file()):
        ext = f.suffix.lower()
        if ext in OFFICE or ext in {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff", ".zip", ".msg", ".pst"}:
            print(f"UNMASKED-FORMAT {f.relative_to(root)}: binary file in the shared folder (mask it, then remove it)")
            found += 1
        elif ext in TEXT:
            text = f.read_text(encoding="utf-8-sig", errors="replace")
            n = Counter(k for _, _, k in find_spans(text, terms))
            if n:
                print(f"LEAK  {f.relative_to(root)}: " + ", ".join(f"{k}x{v}" for k, v in sorted(n.items())))
                found += 1
    print("scan: CLEAN" if not found else f"scan: {found} file(s) need attention")
    return 1 if found else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("mask"); m.add_argument("src", nargs="?", type=Path); m.add_argument("--out", type=Path)
    m.add_argument("--terms", type=Path); m.add_argument("--map", type=Path); m.set_defaults(fn=cmd_mask)
    r = sub.add_parser("restore"); r.add_argument("file", type=Path); r.add_argument("--out", type=Path)
    r.add_argument("--map", type=Path); r.set_defaults(fn=cmd_restore)
    s = sub.add_parser("scan"); s.add_argument("dir", nargs="?", type=Path); s.add_argument("--terms", type=Path)
    s.set_defaults(fn=cmd_scan)
    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
