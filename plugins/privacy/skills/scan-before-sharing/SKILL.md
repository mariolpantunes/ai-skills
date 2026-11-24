---
name: scan-before-sharing
description: Checks a draft, table or file the user is about to send or upload for personal and confidential data that must not leave, and reports types and places without repeating values. Use before sending, publishing or uploading any text, even when the data was not masked.
---

# Scan before sharing

1. Read the text to be shared (not the private originals). List each place that holds: a person's name, e-mail, phone, address, tax or ID number, bank account, card number, password or key, salary, health or legal detail, a client or supplier name, an internal price or contract term.
2. Output a table: place (file and line, or heading), kind, what to do (remove, replace with a token, ask the owner). Never copy the value into the table.
3. Mark each row MUST (identifies a person or gives access) or CHECK (business-sensitive; the owner decides).
4. If the file is in a masked work folder, tell the user to run `scan.cmd` as the final test; your reading does not replace it.
5. Finish with the count per kind and the sentence "Not sent. A person decides."
