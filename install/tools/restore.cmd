@echo off
rem Usage: restore.cmd "ai\work\masked\result.md"  (or drag the file onto this icon)
set "AI_HOME=%USERPROFILE%\ai"
uv run "%AI_HOME%\tools\sensitive.py" restore %*
pause
