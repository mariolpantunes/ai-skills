# ai-skills

Generic skills and hints for office work with Claude. Course-independent: no client names, no dates, only fictional examples. Courses pin a release tag.

## Plugins (marketplace `ai-skills`)

| Plugin | Skills |
|:--|:--|
| `core` | `prompt-brief`, `step-check`, `markdown-first`, `office-checklist`, `write-a-skill` |
| `office` | `triage-mailbox`, `reply-to-client`, `summarise-with-sources`, `find-contradictions`, `extract-and-count-fields`, `score-with-rubric`, `improve-writing` |
| `data` | `consolidate-order-files`, `check-totals`, `powerbi-starter` (PBIP generator; opens empty until Refresh) |
| `privacy` | `mask-sensitive`, `scan-before-sharing` |

## Install (Windows 11)

`powershell -ExecutionPolicy Bypass -File install\install.ps1` installs Claude Desktop, uv and Git (winget), gets this repo, links the skills for Claude Code, and creates `%USERPROFILE%\ai\{private,work,tools,hints}`. Add `-WithCli` for Claude Code. It is idempotent. In Claude Desktop: Customize, Plugins, Add marketplace, `mariolpantunes/ai-skills`.

## Privacy design

The agent never sees originals. The user converts and masks locally (`tools\mask.cmd`): IBAN, tax number (NIF), phone, e-mail, card, plate, postal code, street, passwords, and the names in `private\terms.txt` become tokens (`<NIF_1>`). The agent works on `work\masked`; `restore.cmd` puts the real values back into a result, in `private\restored`; `scan.cmd` proves the work folder is clean. The private folder is under `%USERPROFILE%\ai`, not `Documents`, because OneDrive may sync Documents.
Limits: pattern and word-list based; no context, image or scan understanding; masking with a local map is pseudonymisation, not anonymisation.

## Layout and tests

`plugins/*/skills/<name>/SKILL.md`, `hints/` (instructions to paste), `install/`, `tests/` (`uv run --no-project --with pytest --with 'markitdown[docx]==0.1.9' pytest -q tests`). Licence MIT.
