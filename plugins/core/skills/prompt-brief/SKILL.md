---
name: prompt-brief
description: Turns a rough request into a short brief with role, context, task, format, examples and checks, asking at most three questions first. Use when the user's request is vague, when a prompt gave a poor answer, or when the user wants a prompt to reuse.
---

# Prompt brief

1. Read the request. Do not start the task yet.
2. Ask at most three questions, only for what is missing and cannot be guessed: the goal, the input files, the format of the result. Skip any question the request already answers.
3. Write the brief in this order, one line each, plain words:
   - **Role**: who the assistant is for this task.
   - **Context**: the files to use and what they are; "use only these files".
   - **Task**: one verb and one object.
   - **Format**: the exact shape of the result (a table with named columns, N bullets, a file name). Paste one finished example if the shape is unusual.
   - **Checks**: what to write when data is missing (MISSING, never a guess), what to count, what to quote.
4. If the task has several steps that can be verified, add the steps as a numbered list (see the skill `step-check`).
5. Show the brief and ask "Run it as written?". Run it only after a yes.
6. After the answer, say what was wrong, not "try again": change one line of the brief per round and name the line you changed.
7. When a brief works twice, offer to save it as a skill (skill `write-a-skill`) or as a line in the user's instructions.

Write the brief in the language the user wrote the request in.
