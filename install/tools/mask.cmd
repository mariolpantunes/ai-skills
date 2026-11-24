@echo off
rem Masks every document in ai\private\in into ai\work\masked
set "AI_HOME=%USERPROFILE%\ai"
uv run "%AI_HOME%\tools\sensitive.py" mask %*
pause
