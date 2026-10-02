# Reproducible demos

[简体中文](DEMO.zh-CN.md) · [Project introduction](../README.md)

## EnvBench: reaction to sample export

1. Install the Android app and open **My space → Load lab demo**. The demo adds an invented UV/PDS reaction with samples, water-matrix data and observations; existing records remain intact.
2. Open the demo reaction. Review its process, target, oxidant dose, sampling checkpoints and matrix data.
3. Use a separate new run to try the live workflow. Add sampling times, take a planned or unplanned sample, choose a quench agent, and record field sources for pH, temperature and volume.
4. Open **Paste LC peak areas**. Use labelled rows such as `S-001 10000` and `S-002 8200`, then inspect the sample-to-value preview. Try an invalid row and confirm that it must be corrected before the batch can be applied.
5. Review C/C₀ and the fitted time range. If excluding a point, save the reason. Correct a sample time with an explanation and inspect the retained original values.
6. Export **Samples CSV** and a full ZIP backup. The CSV includes measurement sources and both original and corrected timing; the ZIP preserves full revision history and photos.
7. Switch languages in **My space**. Interface labels change while your sample names and observations remain as entered.

## EnvEvidence: paper to reviewed evidence

Start the desktop app as described in the README. A fresh data directory opens on **Literature evidence**, in English, with the Forest palette.

1. Click **Load evidence demo** to add a synthetic paper, supplement and recorded extraction. No API call is made.
2. Open **Evidence review**. Trial A has 85% pollutant removal and 20% TOC removal; Trial B has 12% and 2%; Trial C has 64% removal with TOC not found. A/B reagent doses are in the supplement.
3. Select one field, compare the extracted value with its quotation and page context, and save a review with reviewer name and reason.
4. Export CSV, Excel or the full project JSON. Inspect the separation of model values, current values and review history.
5. Open **Appearance**, save a palette and restart. Switch to Chinese and back; quotations, model output and audit records retain their original text.

The PDFs, sample data and recorded extraction are original MIT-licensed fixtures. The desktop demo verifies fixture hashes. Published screenshots use isolated synthetic data.

CLI demo:

```bash
python -m envevidence demo --output data/demo
```
