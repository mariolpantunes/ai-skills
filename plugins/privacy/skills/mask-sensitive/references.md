Commands (run by the user, in PowerShell or by double-click):
- `mask.cmd`: masks everything in `ai\private\in` into `ai\work\masked`.
- `restore.cmd <file>`: puts real values back into a masked result; output in `ai\private\restored`.
- `scan.cmd`: checks `ai\work` for real values and for binary files; never prints values.
Own names: one per line in `ai\private\terms.txt` (`ORG: Acme Lda` sets the type).
