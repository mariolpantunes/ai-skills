#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# ///
"""Manage your skills: list, show, new, check, edit, merge, remove, restore, package, install.

  skills.py list
  skills.py new NAME "what it does. Use when ..."
  skills.py show NAME
  skills.py check [NAME]
  skills.py edit NAME [RELPATH] [--from FILE]     (replace or add a file; no --from reads stdin)
  skills.py merge KEEP DROP [--apply]             (dry run unless --apply)
  skills.py remove NAME                           (moves to the archive; nothing is deleted)
  skills.py restore NAME
  skills.py package NAME [--out DIR]              (ZIP with the folder as root, for Claude Desktop upload)
  skills.py install FILE.zip

Skills folder: --root, else env AI_SKILLS, else ~/.claude/skills. Archive: <root>/../skills-archive.
Python standard library only; works the same on Windows and Linux.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
import zipfile
from datetime import datetime
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
# personal data that must not live in a reusable skill
PERSONAL = [
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "e-mail address"),
    (re.compile(r"[A-Za-z]:\\Users\\[^\\\s]+|/hom[e]/[^/\s]+|/User[s]/[^/\s]+"), "personal path (use ~ or %USERPROFILE%)"),
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "IP address"),
    (re.compile(r"(?i)\b(?:password|palavra-passe|api[_-]?key|token)\s*[:=]\s*\S+"), "secret"),
    (re.compile(r"\b\d{9}\b"), "9-digit number (tax number?)"),
]


def root_dir(arg: str | None) -> Path:
    return Path(arg or os.environ.get("AI_SKILLS") or Path.home() / ".claude" / "skills").expanduser()


def fm(text: str) -> dict[str, str]:
    """Read the header between the two --- lines (simple key: value)."""
    m = re.match(r"---\r?\n(.*?)\r?\n---", text, re.S)
    out: dict[str, str] = {}
    if m:
        for line in m.group(1).splitlines():
            k, _, v = line.partition(":")
            if v:
                out[k.strip()] = v.strip().strip("\"'")
    return out


def skill_dir(root: Path, name: str) -> Path:
    if not NAME_RE.match(name):
        sys.exit(f"error: name {name!r} must be lowercase words joined by hyphens")
    return root / name


def problems(d: Path) -> list[tuple[str, str]]:
    """(level, message) for one skill folder; level is error or warn."""
    out: list[tuple[str, str]] = []
    f = d / "SKILL.md"
    if not f.is_file():
        return [("error", "no SKILL.md")]
    text = f.read_text(encoding="utf-8-sig")
    h = fm(text)
    if h.get("name") != d.name:
        out.append(("error", f"header name {h.get('name')!r} differs from folder {d.name!r}"))
    desc = h.get("description", "")
    if not desc:
        out.append(("error", "no description in the header"))
    elif len(desc) > 300:
        out.append(("error", f"description has {len(desc)} characters (max 300)"))
    elif not re.search(r"(?i)\buse (when|for|to)\b", desc):
        out.append(("warn", "description should say when to use the skill ('Use when ...')"))
    body = re.sub(r"\A---.*?---", "", text, count=1, flags=re.S)
    if len(body.strip().splitlines()) > 60:
        out.append(("warn", "body over 60 lines: move detail to a second file"))
    if not re.search(r"^\s*1\.", body, re.M):
        out.append(("warn", "no numbered steps"))
    for p in d.rglob("*"):
        if p.is_file() and p.suffix.lower() in {".md", ".txt", ".py", ".json", ".yaml", ".yml", ".ps1", ".sh"}:
            t = p.read_text(encoding="utf-8", errors="ignore")
            for rx, what in PERSONAL:
                if rx.search(t):
                    out.append(("error", f"{p.relative_to(d)}: {what}"))
    return out


def stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def archive_dir(root: Path) -> Path:
    return root.parent / "skills-archive"


def cmd_list(a, root: Path) -> int:
    if not root.is_dir():
        print(f"no skills folder yet: {root}")
        return 0
    for d in sorted(x for x in root.iterdir() if x.is_dir()):
        h = fm((d / "SKILL.md").read_text(encoding="utf-8-sig")) if (d / "SKILL.md").is_file() else {}
        bad = sum(1 for lv, _ in problems(d) if lv == "error")
        print(f"{d.name:28} {'OK ' if not bad else 'ERR'} {h.get('description', '')[:90]}")
    return 0


def cmd_new(a, root: Path) -> int:
    d = skill_dir(root, a.name)
    if d.exists():
        sys.exit(f"error: {d} exists; use edit")
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(
        f"---\nname: {a.name}\ndescription: {a.description}\n---\n\n# {a.name}\n\n"
        "1. Read the input the user names.\n2. Do the task step by step (one action per step).\n"
        "3. If data is missing, write MISSING; never invent.\n4. Check the result against the input and list what the user must check.\n",
        encoding="utf-8",
    )
    print(f"created {d / 'SKILL.md'}; now run: skills.py edit {a.name}  then  skills.py check {a.name}")
    return 0


def cmd_show(a, root: Path) -> int:
    d = skill_dir(root, a.name)
    if not d.is_dir():
        sys.exit(f"error: no skill {a.name}")
    for p in sorted(x for x in d.rglob("*") if x.is_file()):
        print(f"{p.relative_to(d)}  ({p.stat().st_size} bytes)")
    print("\n" + (d / "SKILL.md").read_text(encoding="utf-8-sig"))
    return 0


def cmd_check(a, root: Path) -> int:
    names = [a.name] if a.name else sorted(x.name for x in root.iterdir() if x.is_dir())
    errors = 0
    for n in names:
        for lv, msg in problems(skill_dir(root, n)):
            print(f"{lv}: {n}: {msg}")
            errors += lv == "error"
    print("check:", "FAILED" if errors else "ok", f"({errors} error(s))")
    return 1 if errors else 0


def cmd_edit(a, root: Path) -> int:
    d = skill_dir(root, a.name)
    if not d.is_dir():
        sys.exit(f"error: no skill {a.name}; use new")
    rel = Path(a.relpath)
    if rel.is_absolute() or ".." in rel.parts:
        sys.exit("error: relpath must stay inside the skill")
    data = Path(a.src).read_text(encoding="utf-8-sig") if a.src else sys.stdin.read()
    target = d / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    old = target.read_text(encoding="utf-8") if target.is_file() else None
    target.write_text(data, encoding="utf-8")
    bad = [m for lv, m in problems(d) if lv == "error"]
    if bad:  # restore the previous state when the result breaks the format
        if old is None:
            target.unlink()
        else:
            target.write_text(old, encoding="utf-8")
        sys.exit("refused, previous file restored:\n  " + "\n  ".join(bad))
    print(f"wrote {target}")
    return 0


def cmd_merge(a, root: Path) -> int:
    if a.keep == a.drop:
        sys.exit("error: keep and drop are the same skill")
    keep, drop = skill_dir(root, a.keep), skill_dir(root, a.drop)
    if not keep.is_dir() or not drop.is_dir():
        sys.exit("error: both skills must exist")
    copy, clash = [], []
    for p in sorted(x for x in drop.rglob("*") if x.is_file() and x.name != "SKILL.md"):
        rel = p.relative_to(drop)
        (clash if (keep / rel).exists() else copy).append(rel)
    print(f"keep: {a.keep}\ndrop: {a.drop}\nfiles to copy: {[str(x) for x in copy]}\nconflicts (go to references/merged-from-{a.drop}/): {[str(x) for x in clash]}")
    print(f"\n--- body of {a.drop} (fold the steps you need into {a.keep}) ---\n" + (drop / "SKILL.md").read_text(encoding="utf-8-sig"))
    if not a.apply:
        print("\ndry run: add --apply to move the files and archive the dropped skill")
        return 0
    for rel in copy:
        (keep / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(drop / rel, keep / rel)
    for rel in clash:
        t = keep / "references" / f"merged-from-{a.drop}" / rel
        t.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(drop / rel, t)
    ref = keep / "references"
    ref.mkdir(exist_ok=True)
    shutil.copy2(drop / "SKILL.md", ref / f"merged-from-{a.drop}.md")
    return cmd_remove(argparse.Namespace(name=a.drop), root, note=f"merged into {a.keep}; now fold the steps into {a.keep}/SKILL.md and widen its description")


def cmd_remove(a, root: Path, note: str = "") -> int:
    d = skill_dir(root, a.name)
    if not d.is_dir():
        sys.exit(f"error: no skill {a.name}")
    dest = archive_dir(root) / f"{a.name}-{stamp()}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(d), str(dest))
    print(f"archived to {dest} (restore: skills.py restore {a.name}) {note}")
    return 0


def cmd_restore(a, root: Path) -> int:
    d = skill_dir(root, a.name)
    found = sorted(archive_dir(root).glob(f"{a.name}-*")) if archive_dir(root).is_dir() else []
    if not found:
        sys.exit(f"error: nothing archived for {a.name}")
    if d.exists():
        sys.exit(f"error: {d} exists already")
    shutil.move(str(found[-1]), str(d))
    print(f"restored {d}")
    return 0


def cmd_package(a, root: Path) -> int:
    d = skill_dir(root, a.name)
    if cmd_check(argparse.Namespace(name=a.name), root):
        sys.exit("fix the errors first")
    out = Path(a.out or ".") / f"{a.name}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(x for x in d.rglob("*") if x.is_file() and "__pycache__" not in x.parts):
            z.write(p, Path(a.name) / p.relative_to(d))
    print(f"wrote {out}: upload it in Claude Desktop under Customize, Skills, Create skill, Upload a skill")
    return 0


def cmd_install(a, root: Path) -> int:
    with zipfile.ZipFile(a.file) as z:
        tops = {Path(n).parts[0] for n in z.namelist() if n.strip("/")}
        if len(tops) != 1 or any(Path(n).is_absolute() or ".." in Path(n).parts for n in z.namelist()):
            sys.exit("error: the ZIP must hold one folder as its root, with no absolute or .. paths")
        name = tops.pop()
        if (root / name).exists():
            sys.exit(f"error: {name} exists; remove it first (it is archived, not deleted)")
        z.extractall(root)
    return cmd_check(argparse.Namespace(name=name), root)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    p = sub.add_parser("new"); p.add_argument("name"); p.add_argument("description")
    for c in ("show", "remove", "restore", "package"):
        p = sub.add_parser(c); p.add_argument("name")
        if c == "package":
            p.add_argument("--out")
    p = sub.add_parser("check"); p.add_argument("name", nargs="?")
    p = sub.add_parser("edit"); p.add_argument("name"); p.add_argument("relpath", nargs="?", default="SKILL.md"); p.add_argument("--from", dest="src")
    p = sub.add_parser("merge"); p.add_argument("keep"); p.add_argument("drop"); p.add_argument("--apply", action="store_true")
    p = sub.add_parser("install"); p.add_argument("file")
    a = ap.parse_args()
    root = root_dir(a.root)
    root.mkdir(parents=True, exist_ok=True)
    return globals()["cmd_" + a.cmd](a, root)


if __name__ == "__main__":
    sys.exit(main())
