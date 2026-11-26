---
name: write-a-skill
description: Writes, improves, merges and checks the user's own skills (a folder with a SKILL.md) from a task they repeat, and tells them how to install it. Use when the user wants to turn a repeated task into a skill or tidy the skills they have.
---

# Write a skill

A skill is a folder named like the skill, holding one text file `SKILL.md`. No program is needed: you write the file, the user zips and installs it.

1. Ask for the task, one input and one output that was good. Write down the steps that made it good.
2. If the user already has a skill that covers it, improve that one; do not make a parallel skill.
3. Create the folder `<name>` in the folder the user works in (name: lowercase words joined by hyphens, for example `reply-to-client`) with `<name>/SKILL.md`, plain UTF-8 text:
   ```
   ---
   name: <name>
   description: <what it does, third person. Use when ...>
   ---
   1. <one action per step>
   ```
4. `name` is the folder name. `description` says what the skill does and when to use it, under 300 characters: it is the line Claude reads to decide to load the skill.
5. Body: numbered steps, one action per step, at most 60 lines, `MISSING` for absent data, a last step that checks the result.
6. Check before you hand it over: header with exactly `name` and `description`; name equals the folder; no person's name, e-mail, personal path, IP address or secret (a skill is a method, not data: put such facts in the task).
7. Test with a realistic request and with one that must NOT trigger the skill; fix the description if it triggers wrongly.
8. Overlap: two skills that do nearly the same become one. Copy the steps of the second into the first, widen the description, then remove the second.
9. Install, Claude Desktop: zip the folder so that `<name>/SKILL.md` is inside the ZIP (File Explorer: right-click the folder, Send to, Compressed (zipped) folder), then Customize, Skills, upload the ZIP. Claude Code: put the folder in `~/.claude/skills/`.
10. Share: send the ZIP. Before installing a skill from someone else, read its `SKILL.md`: Claude will follow it.
