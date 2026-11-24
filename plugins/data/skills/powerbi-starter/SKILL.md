---
name: powerbi-starter
description: Builds a Power BI Project (.pbip) from a checked clean CSV: a model with measures and a one-page report with a card and a bar chart, to open in Power BI Desktop on Windows. Use when the user wants a Power BI report, dashboard or model from a table.
---

# Power BI starter

1. Start only from a table that passed the skill `check-totals` (rows and totals proven). Never build a report on an unchecked file.
2. The CSV needs one header row, a dot as decimal mark and ISO dates. If not, run the skill `consolidate-order-files` first.
3. Write the project: `uv run <skill folder>/scripts/make_pbip.py <clean.csv> --out <work folder>/powerbi --name <Name> --table <table> --csv-path "<full Windows path of the CSV>"`. If the script cannot run, write the same three measures by hand (below) and tell the user to paste them in Power BI.
4. Tell the user to open `<Name>.pbip` in Power BI Desktop (double-click). The project has no data cache, so the report is empty until the user clicks Refresh (Home, Refresh). If the CSV moved, change the parameter `CsvPath` under Transform data first.
5. The measures are `Total EUR` (sum of the amount), `Order count` (distinct count of the key) and `Average order`. The report shows the total as a card and the total per category as a bar chart.
6. Ask the user to compare the card with the total proven in step 1. The card abbreviates (152 205.77 shows as 152.21K; Display units None shows the full figure). A different number means a different file or a wrong refresh: stop and look at the rows.
7. Never publish to the Power BI service for the user: that needs a work or school licence and the user's decision. Do not put personal data in the model: use the masked table (skill `mask-sensitive`).

Measures by hand: `Total EUR = SUM(table[amount])`; `Order count = DISTINCTCOUNT(table[order])`; `Average order = DIVIDE([Total EUR], [Order count])`.
Limits: one table, no relationships, no date hierarchy; extra visuals are added by hand or by asking for a change of the files.
