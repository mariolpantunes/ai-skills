# Hints: where each file goes

| File | Paste or copy it to | What it does |
|:--|:--|:--|
| `global-instructions.md` | Claude Desktop: Settings, Cowork, Global instructions, Edit (newer builds: Settings, Your Claude, Instructions for Claude) | Language, truth, format and safety rules for every task |
| `workspace-instructions.md` | Folder instructions when you select `ai\work`; with Claude Code save it as `CLAUDE.md` in that folder | Rules for the masked work folder |
| `claude-code-settings.json` | Claude Code only: merge into `~/.claude/settings.json` | Denies reading the private folder and the map |

Keep each hint file under about 25 lines: long rules are forgotten (context rot).
Labels of the Claude menus change between versions; check them in the app.
`install.ps1` copies these files to `%USERPROFILE%\ai\hints` so you can open and paste them.
