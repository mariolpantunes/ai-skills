---
name: markdown-first
description: Converts Word, Excel, PowerPoint, PDF or HTML inputs into Markdown, works on the Markdown, and writes the result as Markdown, Word or CSV on request. Use when documents are the input of a task, or when a Markdown file must become a Word document.
---

# Markdown first

Agents read plain text best. Markdown keeps headings, lists and tables, and costs few tokens.

1. List the input files and their formats. Never change the originals.
2. Convert each non-text input: `uv run <skill folder>/scripts/to_md.py <file or folder> --out <folder>/md`. One `.md` per file, tables kept as Markdown tables.
3. If the script cannot run (no uv, no network), ask the user to export each file as Markdown, text or CSV and continue with those.
4. Read the converted files. Check that headings, tables and numbers survived: compare one table and one total against the original and say what you compared. Scanned PDFs and images give no text: report them, do not guess.
5. Do the task on the Markdown. Cite the file and the heading for every fact.
6. Write the result as `.md` first. Only if the user asks for Word: `uv run <skill folder>/scripts/from_md.py <result.md> --out <result.docx>`. For tables to Excel use CSV.
7. Say which files were converted, which failed, and what was lost (images, comments, tracked changes, hidden sheets).

Markdown syntax in short: `#` heading, `-` list item, `| a | b |` table row with a `|---|---|` line under the header, `**bold**`, a line of code between backticks.
