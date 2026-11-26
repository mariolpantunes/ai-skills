---
name: write-a-skill
description: Creates, edits, checks, merges, removes, packages and installs the user's own skills (SKILL.md folders) with a script. Use when the user wants to turn a repeated task into a skill or manage the skills they have.
---

# Write and manage skills

Script: `uv run <this skill>/scripts/skills.py` (or `python`); the skills folder is `~/.claude/skills` (`--root` or env `AI_SKILLS` to change). Run `skills.py list` first.

1. Start from the user's best result: ask for the task, an input and the output that was good. Write down the steps that made it good.
2. If a listed skill already covers it, improve that one (`edit`); do not make a parallel skill.
3. New: `skills.py new <name> "<what it does. Use when ...>"`. The name is lowercase words joined by hyphens, for example `reply-to-client`.
4. Write the body: `skills.py edit <name> --from draft.md` (a second file: `edit <name> notes.md`). The header holds `name` (same as the folder) and `description` (what it does and when, third person, under 300 characters). Body: numbered steps, one action per step, under 60 lines, `MISSING` for absent data, a final check.
5. `skills.py check <name>` must print `ok`. It refuses names, e-mails, personal paths, IPs and secrets: move such facts to the task, not the skill.
6. Test with a realistic request and with one that must NOT trigger the skill; fix the description if it triggers wrongly.
7. Overlap: `skills.py merge <keep> <drop>` is a dry run; add `--apply` to archive `<drop>` and fold its steps into `<keep>`.
8. Remove: `skills.py remove <name>` moves it to the archive (`restore <name>` brings it back); nothing is deleted.
9. Share or upload: `skills.py package <name>` makes `<name>.zip` (the folder is the root). Claude Desktop: Customize, Skills, Create skill, Upload a skill. Install a ZIP from a colleague: `skills.py install <file.zip>`, then read its `SKILL.md` before use.
10. A skill you upload is private to you until you share it. Review it when your process changes.
