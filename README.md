# EnvBench & EnvEvidence

**Two tools for water-treatment research: capture reaction runs at the bench, and build literature evidence tables at your desk.**

[简体中文](README.zh-CN.md) · [Android app](android/README.md) · [Try the demo](docs/DEMO.md) · [Validation](docs/VALIDATION.md)

| App | Where it fits | What you get |
|---|---|---|
| **EnvBench · Android** | Sampling, quenching and observations during water and wastewater experiments | Timers, sample records, water-matrix data, photos, concentration trends and CSV exports |
| **EnvEvidence · Desktop** | Reading and organizing water-treatment papers | Experimental-condition tables, source quotations, page locations and reviewer corrections |

Both apps have English and Chinese interfaces, saved appearance settings and local data storage.

## EnvBench: your reaction run, in one place

Keep the sampling plan, sampling events and analytical results together. EnvBench is designed around advanced oxidation and DOM research, with process presets including UV/PDS, UV/H₂O₂, ozone and Fenton.

- **Stay on the sampling schedule.** A prominent countdown shows the next checkpoint; planned and recorded times remain separate.
- **Record each sample.** Capture the quench agent, pH, temperature, volume and a short note, then attach a photo. Field labels distinguish measured values from values carried over from another sample.
- **Keep the water matrix with the run.** Store DOC, UV₂₅₄, alkalinity, major ions and other matrix properties; SUVA₂₅₄ is calculated from DOC and UV₂₅₄.
- **Review concentration trends.** Paste labelled LC peak areas or enter C/C₀, inspect the import preview and see a pseudo-first-order fit with k_obs, its 95% confidence interval, t½ and R².
- **Export your experiment.** Share tidy sample CSVs, an individual experiment ZIP or a full backup with original photos.

Stopwatches, countdowns, sampling reminders and counters can run in parallel. There is no fixed cap on the number of timers. Settings, language, appearance and backup controls are grouped under **My space**.

<img src="docs/images/envbench-run-en.png" alt="EnvBench reaction run with the next sampling checkpoint" width="300"> <img src="docs/images/envbench-samples-en.png" alt="EnvBench sample records and concentration trend" width="300">

**Android 8.0+ · Offline · No account required**

**[Download EnvBench 0.6.1 for Android](https://github.com/gzpagg/envevidence/releases/download/v0.6.1-android-preview.1/envbench-0.6.1-android.apk)** · [Release notes](https://github.com/gzpagg/envevidence/releases/tag/v0.6.1-android-preview.1) · [Installation guide](android/README.md). Install the signed preview APK to start using the experiment notebook. Open **My space → Load lab demo** to explore an invented UV/PDS run with samples and water-matrix data.

## EnvEvidence: literature values with their sources

Import a paper and its supplements, extract the experimental conditions, and review every field beside the quoted source. EnvEvidence keeps the model's original value and the reviewer's correction together, so you can revisit the decision later.

| Step | Workflow |
|---|---|
| **Import** | Add text PDFs and associate supplements with their main papers. Inspect parsed page coverage. |
| **Extract** | Select the water-treatment template or define your own fields. OpenAI and Anthropic adapters use the same record structure. |
| **Review** | Check values, units and experiment associations against the source quotation and page context. Save the reviewer, reason and time. |
| **Export** | Download long-form CSV, Excel or the complete project JSON with source text and revision history. |

Pollutant removal and mineralization/TOC removal have separate fields. Different experimental conditions produce separate records, and each key field carries a source location or a clear missing-value status.

![EnvEvidence source review in English](docs/images/review-en.png)

### Install the desktop app

Requires **Python 3.11+**. Clone the repository and create a virtual environment:

```bash
git clone https://github.com/gzpagg/envevidence.git
cd envevidence
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m envevidence serve
```

macOS / Linux:

```bash
.venv/bin/python -m pip install -e .
.venv/bin/python -m envevidence serve
```

Open <http://127.0.0.1:8501>. Choose **Load evidence demo** to explore a synthetic paper and supplement without an API key. The current desktop version is **0.3.0**.

### Extract from your own papers

1. Create a project, choose OpenAI or Anthropic and enter a model ID supported by your account.
2. Import the main paper and supplements, then select extraction fields.
3. Parse the files locally and check page coverage.
4. Enter a session-only API key, or set `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` in the environment. Confirm the text to send and start extraction.
5. Review the extracted fields and save corrections before exporting.

`OPENAI_MODEL` and `ANTHROPIC_MODEL` provide default model IDs. `.env` files are not loaded automatically. Custom fields use `key | label | extraction instruction | unit`; the unit segment is optional.

Text PDFs are supported up to 30 MB and 250 pages per file. The [demo guide](docs/DEMO.md) explains the review workflow; the [validation record](docs/VALIDATION.md) describes parsing and model-evaluation coverage.

## Language, appearance and your data

Switching language changes interface labels while preserving paper text, sample names, model results and revision records. Android uses a warm-paper and terracotta palette; the desktop app offers Forest, Ocean, Sand and Graphite presets plus custom colors.

EnvBench stores records and photos in private Android storage. Use a full ZIP backup before uninstalling or moving devices. EnvEvidence stores projects and preferences under `data/`; `ENVEVIDENCE_DATA_DIR` selects another local directory. Back up that directory while the desktop app is stopped. Data from earlier versions is retained during compatible upgrades.

The experiment workflow runs locally. Desktop extraction sends the parsed text and field definitions to the API service you choose; the API key stays out of project files. Runtime data and credentials are excluded from this repository.

## Development and documentation

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
python -m ruff check .
python -m build
node --test android/tests/*.test.cjs
```

[Android screenshots and checks](docs/ANDROID.md) · [Samples CSV](docs/BENCH_CSV.md) · [Architecture](docs/ARCHITECTURE.md) · [Validation](docs/VALIDATION.md) · [Changelog](CHANGELOG.md)

Report reproducible problems through the issue templates. Code and original synthetic examples are [MIT licensed](LICENSE); dependency licenses are listed in [third-party notices](THIRD_PARTY_NOTICES.md).
