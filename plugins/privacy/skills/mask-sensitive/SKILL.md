---
name: mask-sensitive
description: Works on documents that were masked on the user's PC (tokens like <NIF_1>, <NAME_2>) and keeps real identities out of the conversation. Use whenever documents may hold personal, financial or confidential data, or when the user asks to protect, mask, anonymise or restore data.
---

# Work on masked documents

The user masks documents locally with `mask.cmd` (script `scripts/sensitive.py`). You only ever get the masked copy in the connected work folder. Tokens such as `<IBAN_1>` stand for the same real value everywhere, so tables, counts and cross-references still work.

1. Open only files in the connected work folder. Never ask for, look for or open the private folder (`private`, `in`, `map.json`, `terms.txt`, `restored`).
2. If a file in the work folder holds what looks like a real e-mail, phone, IBAN, tax number, card number, password or a name, stop. Say which file and which kind, do not repeat the value, and ask the user to run `scan.cmd` and mask again.
3. If the user pastes or attaches raw sensitive data in the chat, say it is already shared, and ask them to use the masked route from now on.
4. Work on the tokens as if they were the data: keep each token exactly as written, never guess or "fill in" the real value, never write a token you were not given.
5. After the first read, list residual risks in the masked text without quoting them: a job title that names one person, a rare event, an address written in words, a name the masker missed. Give the file and line, and ask the user to add the term to `terms.txt` and mask again.
6. Write results in the work folder with the tokens unchanged. Tell the user to run `restore.cmd` on a result to put the real values back; the restored file lands in the private folder, never next to the masked copy.
7. Before the user shares a result outside, ask for `scan.cmd` on the work folder: it must say CLEAN.

Limits to say out loud when relevant: masking finds patterns (tax number, IBAN, phone, e-mail, card, plate, postal code, street, passwords) and the names in `terms.txt`; it does not understand context, images or scanned pages. Masked data with a map on the same PC is pseudonymised, not anonymous; the data-protection officer decides what may leave the company.
