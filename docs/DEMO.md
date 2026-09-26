# Reproducible demo

Start the app as described in the README. A fresh data directory starts in English with all four modules enabled and the Forest palette.

1. Click **Load workspace demo**. It appends invented goals, dated tasks, a pinned note and a synthetic evidence project. Existing data is preserved; the workspace seed is only applied once.
2. Open **Learning goals**. Complete a step: one of three becomes two of three. Rename it and confirm the completion state remains. Archive the goal, switch on **Show archived**, then restore it.
3. Open **Daily tasks**. Change a task from To do to Done, then reopen it. Overdue tasks keep their original dates and do not affect today's denominator.
4. Open **Sticky notes**. Edit, pin, choose a color, save, archive and restore a note.
5. Open **Literature evidence** and open the synthetic project. Select **Evidence review**. Trial A has 85% pollutant removal and 20% TOC removal; Trial B has 12% and 2%; Trial C has 64% removal with TOC not found. A/B reagent doses are in the supplement.
6. Review one field against its source, provide a reviewer and reason, save, then export. Source matching alone is not scientific verification.
7. Open **Appearance & modules**. Preview a palette, save it, hide a module, reorder another and restart. Restore the layout and confirm hidden data returns.
8. Switch to Chinese and back. Application labels change; notes, quotations and saved audit records remain intact.

The PDFs and recorded extraction are invented, MIT-licensed fixtures. Their hashes are checked by the demo provider. No live model is called. Screenshots use isolated synthetic data, never personal research records.

CLI compatibility check:

```bash
python -m envevidence demo --output data/demo
```
