# Changelog

All notable changes to this project are documented here. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning: [SemVer](https://semver.org/).

## [Unreleased]

### Added
- Marketplace with plugins `core`, `office`, `data`, `privacy` (11 skills moved from `iap-office-skills`, 5 new: `prompt-brief`, `step-check`, `markdown-first`, `mask-sensitive`, `scan-before-sharing`).
- `sensitive.py` (mask, restore, scan) with tests; `mask.cmd`, `restore.cmd`, `scan.cmd`.
- `hints/` and `install/install.ps1` (tested on Windows 11 over SSH, run twice).
