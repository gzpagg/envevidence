# EnvEvidence

**EnvBench, the Android app, is a bench companion for reaction runs:** [Install and use](android/README.md) · [Screenshots and validation](docs/ANDROID.md) · [Samples CSV](docs/BENCH_CSV.md). A countdown to every sampling checkpoint, a sample sheet that requires a quench, the water matrix with SUVA₂₅₄, and a k_obs fit from C/C₀. Version 0.5.0 is in source; the latest signed APK is [0.4.0](https://github.com/gzpagg/envevidence/releases/tag/v0.4.0-android-preview.1). Android 8.0+; no account or server required.

<img src="docs/images/envbench-run-en.png" alt="EnvBench run page with the next-sample countdown and sampling checkpoints" width="320">

The desktop app below is EnvEvidence 0.3.0. It now covers literature evidence only. The planning tools from 0.2 are gone from the interface, and their data is kept.

## Desktop literature evidence

**Turn water-treatment papers into source-checked evidence tables.**

[简体中文](README.zh-CN.md) · [Demo](docs/DEMO.md) · [Architecture](docs/ARCHITECTURE.md) · [Validation](docs/VALIDATION.md)

EnvEvidence imports text PDFs and their supplements, extracts experimental conditions with OpenAI or Anthropic, locates every quotation in the parsed pages, and keeps a reviewer's corrections next to the model's original values. It opens in English and has a complete Chinese interface. You need an API key only to extract from your own papers.

![English literature evidence page](docs/images/workspace-en.png)

| Step | What you can do |
|---|---|
| Import | Text PDFs and supplements, with explicit main/supplement links and page-coverage warnings. |
| Extract | Water-treatment or custom fields, one record per experimental condition. |
| Review | Check each value against its located quote; save corrections with reviewer, reason and time. |
| Export | CSV, Excel and complete project JSON. |

Version 0.3 removes the learning goals, daily tasks and sticky notes added in 0.2. They duplicated general-purpose apps and pulled the tool away from evidence. Nothing is deleted: existing items stay in `data/workspace/state.json`, and the sidebar shows how many are kept. Timed sampling, quench records and the water matrix of your own runs belong to the [EnvBench Android app](android/README.md).

## Install and run

Requires Python 3.11+. Clone this repository and enter its directory:

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

Open <http://127.0.0.1:8501>. **Load evidence demo** on the evidence page adds a synthetic evidence project. It makes no API calls.

The sidebar **Language / 语言** selector switches English and Chinese. Your language and saved colors survive restarts. Paper text, model output and revision records are not translated or rewritten.

## Appearance

| Palette | Accent | Background |
|---|---|---|
| Forest (default) | `#147D73` | `#F6F8F7` |
| Ocean | `#1D4ED8` | `#F4F7FB` |
| Sand | `#A84D18` | `#FAF7F2` |
| Graphite | `#6D4ACF` | `#F7F5FB` |

Choose **Custom** for your own accent and background. Text colors adapt; standard inputs and cards remain neutral for readability. Changes preview immediately; **Save appearance** makes them persistent.

![English appearance settings](docs/images/settings-en.png)

## Storage and upgrading from v0.1

Evidence projects retain their existing version-1 JSON format. Language and color preferences, and any planning items kept from 0.2, live separately at `data/workspace/state.json`. Both stores use atomic writes. `ENVEVIDENCE_DATA_DIR` changes the data root; back up the entire directory while the app is stopped. A damaged workspace file is reported and preserved, never silently reset. Avoid editing the same data from multiple browser tabs or app processes.

The app sends only the text you explicitly approve for extraction. Runtime data, virtual environments and credentials are excluded from Git and source packages. Export field keys and evidence audit history remain stable across language changes; historical/user-authored labels are preserved.

![English evidence review](docs/images/review-en.png)

## Workflow and API setup

1. Create a project, select OpenAI or Anthropic, and enter a model ID available to your account with structured-output support.
2. Import main papers and associate each supplement with its paper. Select extraction fields or add custom ones.
3. Parse locally and inspect page coverage and warnings.
4. Provide a session-only key, or configure `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`. Model defaults can be supplied through `OPENAI_MODEL` / `ANTHROPIC_MODEL`. `.env` files are not automatically loaded.
5. Explicitly accept sending the parsed text to the selected service. A provider error stops subsequent calls; completed papers remain saved and are skipped on resume.
6. Review each condition and field against the original source. Save corrections with reviewer, reason, and timestamp. Export CSV, Excel, or complete project JSON.

Water-treatment fields cover pollutant, matrix, initial concentration, treatment, reagent dose, pH, reaction time, pollutant removal, and mineralization/TOC removal as a separate endpoint. Each experiment has its own fields; raw model values remain unchanged after human revisions.

Custom field format: `key | label | extraction instruction | unit` (omit the last segment for unitless fields).

## Accuracy and privacy

**A located quotation is not a scientifically verified result.** It only means the quoted text exists on the specified page. All extracted values initially require human review. Check experimental association, value, unit, and endpoint interpretation.

- Text PDFs only, up to 30 MB and 250 pages per file; no OCR, plot digitization, or inferred unit conversion. Complex layouts and tables may parse incorrectly.
- Page numbers are physical PDF page indices, starting at 1, not printed journal page numbers.
- Missing means not found in the imported, successfully parsed material, not necessarily absent from the paper.
- Each study is sent in one request, with a 160,000-character preflight limit. No silent truncation. Provider context/output limits may be lower.
- Parsing and saving are local. Live extraction sends the parsed page text and field definitions to the selected API, not the original PDFs. Usage is billed to the user's provider account.
- OpenAI requests set `store=false`; this is not a zero-retention guarantee. Provider/account data policies still apply.
- Keys are not persisted. Project JSON contains source text, extraction results, token usage, model name, and reviewer history. `data/` is Git-ignored; configure another local location with `ENVEVIDENCE_DATA_DIR`.
- The app binds to loopback, disables Streamlit usage telemetry through the launch command, and is designed for one user. Avoid concurrent edits of the same project in multiple tabs.

Excel includes Evidence, Experiments, Revisions, Documents, and Runs sheets. The long-form CSV includes model/current values, citations, and review status; full JSON retains all parsed text and history.
Excel cells exceeding its length limit are explicitly marked as truncated; full values remain in JSON/CSV. Unsupported XML control characters are displayed as Unicode markers.

## Development

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
python -m ruff check .
python -m build
```

Tests use invented, redistributable examples, not real scientific findings. API contracts are tested with mocked HTTP; see [validation status](docs/VALIDATION.md) for what has and has not been verified. Report problems through the issue template without credentials, private papers, or unpublished data.

Code and original synthetic fixtures are [MIT licensed](LICENSE). Dependencies retain their own licenses; see [third-party notices](THIRD_PARTY_NOTICES.md). OCR, cross-paper comparability analysis, and MCP integration are future work, not v0.3 features.
