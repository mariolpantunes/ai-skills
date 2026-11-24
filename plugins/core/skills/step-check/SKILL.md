---
name: step-check
description: Runs a multi-step check (totals, rules, comparisons) as numbered steps with a shown intermediate result for each, then derives the verdict from the steps and re-checks it. Use when a task needs arithmetic, rule application, or comparing figures with a source.
---

# Step check (chain of thought for office tasks)

1. Split the task into numbered steps before doing any of them. Each step has one input, one operation and one result that a person can verify.
2. Do the steps in order. Write each intermediate result on its own line with its source (file and place). Do not skip a step because the answer looks obvious.
3. For arithmetic, show every partial sum. For rules, quote the rule and the value it was applied to.
4. Write the verdict last, in one fixed word (RIGHT, WRONG, DIFFERENT, NOT FOUND), only from the results written above it.
5. Re-check: read the verdict against the steps. If a step contradicts the verdict, say so and correct the verdict; shown steps are not proof.
6. List what the user must verify by hand: the one or two figures the verdict depends on most.
7. Never write a number that is in no source. If a figure is missing, write NOT FOUND and stop that step.

Use it for: an invoice against an order, budget subtotals, rule exceptions, a column total against a report. Do not use it for plain rewriting or summaries.
