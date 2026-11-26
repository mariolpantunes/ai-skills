# Changelog

All notable changes to this project are documented here. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning: [SemVer](https://semver.org/).

## [Unreleased]

### Added
- `write-a-skill` now ships `scripts/skills.py` (standard library only): list, new, edit, check (refuses names, e-mails, personal paths, secrets), merge, remove (archive, never deletes), restore, package (ZIP for Claude Desktop), install.
- Automatic detection of names, organisations, labelled ids (NISS, SNS, ID documents) and birth dates (`pii_auto.py`: context rules + local spaCy Portuguese NER, aliases, review file `terms.auto.txt`); PDF normalisation (`normalize.py`, PyMuPDF layout analysis); `restore --docx` writes the real-value summary as a Word file. Tests: `tests/test_auto.py`.
- `install.ps1 -Agent goose|both`: installs goose Desktop (winget `AgenticAIFoundation.gooseDesktop`), links the skills into `~\.agents\skills`, copies the global instructions to goose's `.goosehints` (a different existing file is kept as `.bak`), and with `-RegisterMcp` adds the masked-reader extension to goose's `config.yaml` (backup first; needs goose started once). Run on Windows 11 over SSH; the live model call was not tested.
- `masked_reader.py`: MCP server that returns only masked text (5 tools, no restore); `install.ps1 -RegisterMcp`; tests; verified in Claude Code, goose and on Windows 11.
- `powerbi-starter` skill and `make_pbip.py`: Power BI project (TMDL + PBIR) from a clean CSV; files checked against Microsoft's JSON schemas; opened in Power BI Desktop 2.160 on Windows 11 (needs Refresh for data).
- Marketplace with plugins `core`, `office`, `data`, `privacy` (11 skills moved from `iap-office-skills`, 5 new: `prompt-brief`, `step-check`, `markdown-first`, `mask-sensitive`, `scan-before-sharing`).
- `sensitive.py` (mask, restore, scan) with tests; `mask.cmd`, `restore.cmd`, `scan.cmd`.
- `hints/` and `install/install.ps1` (tested on Windows 11 over SSH, run twice).
