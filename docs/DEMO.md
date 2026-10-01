# Reproducible demo

Start the app as described in the README. A fresh data directory opens on **Literature evidence**, in English, with the Forest palette.

1. Click **Load evidence demo**. It adds a synthetic evidence project and makes no API call.
2. Select **Evidence review**. Trial A has 85% pollutant removal and 20% TOC removal; Trial B has 12% and 2%; Trial C has 64% removal with TOC not found. A/B reagent doses are in the supplement.
3. Review one field against its source, provide a reviewer and reason, save, then export. Source matching alone is not scientific verification.
4. Open **Appearance**. Preview a palette, save it and restart; the palette is kept.
5. Switch to Chinese and back. Application labels change; quotations, model output and saved audit records remain intact.

If the data directory holds learning goals, tasks or notes from version 0.2, the sidebar shows how many are kept. They are not displayed or changed.

The PDFs and recorded extraction are invented, MIT-licensed fixtures. Their hashes are checked by the demo provider. No live model is called. Screenshots use isolated synthetic data, never personal research records.

CLI compatibility check:

```bash
python -m envevidence demo --output data/demo
```
