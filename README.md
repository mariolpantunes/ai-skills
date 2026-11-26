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

`powershell -ExecutionPolicy Bypass -File install\install.ps1` installs Claude Desktop, uv and Git (winget), gets this repo, links the skills for Claude Code, and creates `%USERPROFILE%\ai\{private,work,tools,hints}`. Add `-WithCli` for Claude Code. It is idempotent. In Claude Desktop: Customize, Plugins, Add marketplace, `mariolpantunes/ai-skills`. For goose use `-Agent goose` (or `both`): it installs goose Desktop, links the skills into `~\.agents\skills`, and sets the global hints in goose's config folder; goose has no folder fence, so keep `private` out of its working folder.

## Privacy design

The agent never sees originals. The user converts and masks locally (`tools\mask.cmd`): IBAN, tax number (NIF), phone, e-mail, card, plate, postal code, street, passwords, and the names in `private\terms.txt` become tokens (`<NIF_1>`). The agent works on `work\masked`; `restore.cmd` puts the real values back into a result, in `private\restored`; `scan.cmd` proves the work folder is clean. The private folder is under `%USERPROFILE%\ai`, not `Documents`, because OneDrive may sync Documents.
Names and organisations are found automatically (`pii_auto.py`: honorifics, `Name <e-mail>`, header fields, signatures, labelled ids, birth dates, and a local Portuguese NER model); everything found is written to `private\terms.auto.txt` for you to review, and the surname and first name of each full name are masked too. `AI_AUTO=0` switches this off. PDFs are normalised first (`normalize.py`: clean Markdown, no headers, footers or page numbers, words and paragraphs repaired). After the agent's summary: `restore.cmd summary.md --docx` puts the real values back and writes one Word file in `private\restored`.
Limits: no image or scan understanding (a scanned PDF is refused, not guessed); NER misses some names and masks some words, so review `terms.auto.txt` and run `scan.cmd`; masking with a local map is pseudonymisation, not anonymisation.

## Masked reader (MCP)

`plugins/privacy/mcp/masked_reader.py` is an MCP server that reads the documents in `%USERPROFILE%\ai\private\in` and returns **only masked text**: `list_documents`, `open_document`, `read_pages`, `read_section`, `search_document`. File names are masked too, a search for a real value finds nothing, and there is no tool that restores values (only the user does, with `restore.cmd`). `install.ps1 -RegisterMcp` registers it in Claude Desktop (the config is backed up, other settings are kept). Claude Code: `claude mcp add masked-reader -e AI_HOME=~/ai -- uv run --script <path>/masked_reader.py`. goose (trainer): `make goose-skynet` in the iap repo loads it. Protection holds only if the originals folder is not connected to the agent.

## Manage your own skills

`write-a-skill` carries `scripts/skills.py` (standard library only): `list`, `new`, `edit`, `check` (refuses names, e-mails, paths, secrets), `merge`, `remove` (archive, never deletes), `restore`, `package` (ZIP for Claude Desktop), `install`.

## Layout and tests

`plugins/*/skills/<name>/SKILL.md`, `hints/` (instructions to paste), `install/`, `tests/` (`uv run --no-project --python 3.13 --with pytest --with mcp==2.3.0 --with 'markitdown[docx,xlsx,pdf,pptx]==0.1.9' --with pymupdf4llm==2.2 --with pypandoc_binary==1.17 --with spacy==3.8.18 --with 'pt-core-news-sm @ https://github.com/explosion/spacy-models/releases/download/pt_core_news_sm-3.8.0/pt_core_news_sm-3.8.0-py3-none-any.whl' pytest -q tests`). Licence MIT.
