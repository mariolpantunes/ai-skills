@echo off
rem Checks ai\work for real values and binary files (never prints values)
set "AI_HOME=%USERPROFILE%\ai"
uv run "%AI_HOME%\tools\sensitive.py" scan %*
pause
