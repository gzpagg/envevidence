# Architecture

[简体中文](ARCHITECTURE.zh-CN.md)

The repository contains two local applications: **EnvEvidence 0.4.0**, a Python/Streamlit experiment-analysis and literature-evidence app, and **EnvBench 0.6.1**, an Android experiment notebook. They share an open repository and explicit export/import workflow, while maintaining separate runtime storage.

## Desktop experiment pipeline

Experiment `AnalysisProject` schema version 1 is independent of the evidence schema. It contains series, quantified observations, immutable source descriptors, processing and figure settings, fit requests/results, mobile archives and audit history. Projects live under `analysis/<project-id>/` in the configured data root. Content-addressed raw files retain SHA-256 hashes; manual input is stored as an initial snapshot. JSON saves use temporary files and atomic replacement.

`analysis_data.py` owns strict input validation, table/phone import, sample-ID assay attachment, unit families, correction stages and technical aggregation. All observations survive processing, with a fit inclusion mask and reason. Technical repeats aggregate only within the same run, sample and independent-variable value; independent run IDs remain separate. Mobile ZIP paths and expanded sizes are validated before extraction, and the phone's experiment history and photographs remain attached to its imported snapshot.

`analysis_fitting.py` owns original-scale and eligible linearized models. SciPy bounded float64 fits enforce nonnegative rates and plateau constraints; fitting objectives and supplied sigma are scaled together for unit-independent numerical tolerances. Returned parameters remain in physical units. Fixed values reduce the free-parameter count. Every fit requires at least four points and p+2 points; invalid included values fail the fit. Rank, condition, correlation, boundaries and response variation control confidence-interval diagnostics. Predictions and residuals retain each run's point mask.

`analysis_export.py` builds fixed-dimension Matplotlib figures, CSV/XLSX tables and independent ZIP packages. Raster width/height are rounded to pixels from millimetres and DPI, with preallocation limits. The bundled Noto font supplies Chinese glyphs; SVG uses outlines. Figures use accepted results while tables retain candidate fits. Manifests record hashes, versions and font provenance; configurations contain relative originals and the full processing/fit snapshot.

The additive `analyze --config … --output …` CLI validates original hashes, restores them into a separate store, recalculates processing and fits, restores accepted selections and writes a new package. Existing `serve`, `demo` and `extract` commands remain compatible. The UI provides Conditions, Measurements, Processing, Fitting, Charts and SOP export within one experiment project, with shared language/appearance controls.

## Desktop evidence pipeline

Evidence `Project` JSON remains at schema version 1. Document parsing, model adapters, quotation location, scientific review and export are separate modules. The CLI remains compatible with the original evidence workflow.

`Workspace` schema version 1 stores language and appearance preferences. It also retains version-0.2 learning goals, tasks and notes so existing files can be read and written unchanged. It lives at `workspace/state.json` under the data root, outside evidence-project discovery.

Writes use a same-directory temporary file, flush/fsync and atomic replacement. Failed reads or validation preserve the original file. Use one editor process per project.

`ui.py` supplies the shell, `workbench_ui.py` the sidebar and appearance page, `analysis_ui.py` the experiment workflow and `evidence_ui.py` the evidence workflow. Stable IDs provide widget keys. Per-render language context changes interface strings while preserving scientific content and audit records. Themes use validated hex colors and application CSS; foregrounds are selected for contrast.

The OpenAI and Anthropic adapters call their official endpoints only after the user confirms sending the text, or the CLI receives `--send-text`. Completed studies are checkpointed separately. Model values and reviewer revisions remain distinct.

## Android experiment notebook

Bundled HTML/CSS/JavaScript runs through WebViewAssetLoader. `lab-domain.js` contains experiment, timer, sample, water-matrix and numerical rules; `lab.js` handles the notebook controls, and `bench.js` the reaction-run presentation. Native Java bridges private storage, Android clocks, alarms, notifications, camera/file operations and ZIP archives.

Lab schema version 2 stores experiments, timers, counters, observations, events and samples. Upgrades add missing sample audit fields without discarding older data. Legacy measurement values are labelled unknown rather than retrospectively classified as measured.

Sample corrections retain prior values, measurement sources, timing intervals and reasons. Original button-event timestamps remain intact. Corrected elapsed time drives sample offsets, fitting and fluence calculations. CSV keeps stable machine column names and adds audit columns; full ZIP backups retain complete history and original photos.

Peak-area parsing validates the complete batch before applying changes. Labelled and ordered formats are distinct; errors retain row locations. Fits use positive, included ratios. Exclusions retain reasons; curvature is a model-deviation diagnostic.

Within one device boot, timers use Android monotonic time. Saved wall-clock time supports restart recovery after reboot or device transfer. Imported active timers are paused.

## Data boundaries

Android experiments run locally. Photos and notebook records remain in private storage. Desktop extraction sends parsed text and field instructions to the selected model provider; keys are not stored in project JSON. Runtime data, API credentials and private signing material are excluded from Git and source packages.

EnvBench CSV and ZIP snapshots import one way into desktop analysis, where sample IDs connect quantified assay data. Original phone timestamps and histories remain intact. Literature evidence projects retain their own schema and storage. Runtime analysis never calls model APIs; explicit document extraction is the API boundary.
