# Architecture

[简体中文](ARCHITECTURE.zh-CN.md)

The repository contains two local applications: **EnvEvidence**, a Python/Streamlit literature evidence app, and **EnvBench**, an Android experiment notebook. They share an open repository and export-oriented workflow, while maintaining separate runtime storage.

## Desktop evidence pipeline

Evidence `Project` JSON remains at schema version 1. Document parsing, model adapters, quotation location, scientific review and export are separate modules. The CLI remains compatible with the original evidence workflow.

`Workspace` schema version 1 stores language and appearance preferences. It also retains version-0.2 learning goals, tasks and notes so existing files can be read and written unchanged. It lives at `workspace/state.json` under the data root, outside evidence-project discovery.

Writes use a same-directory temporary file, flush/fsync and atomic replacement. Failed reads or validation preserve the original file. Use one editor process per project.

`ui.py` supplies the shell, `workbench_ui.py` the sidebar and appearance page, and `evidence_ui.py` the evidence workflow. Stable IDs provide widget keys. Per-render language context changes interface strings while preserving scientific content and audit records. Themes use validated hex colors and application CSS; foregrounds are selected for contrast.

The OpenAI and Anthropic adapters call their official endpoints only after the user confirms sending the text, or the CLI receives `--send-text`. Completed studies are checkpointed separately. Model values and reviewer revisions remain distinct.

## Android experiment notebook

Bundled HTML/CSS/JavaScript runs through WebViewAssetLoader. `lab-domain.js` contains experiment, timer, sample, water-matrix and numerical rules; `lab.js` handles the notebook controls, and `bench.js` the reaction-run presentation. Native Java bridges private storage, Android clocks, alarms, notifications, camera/file operations and ZIP archives.

Lab schema version 2 stores experiments, timers, counters, observations, events and samples. Upgrades add missing sample audit fields without discarding older data. Legacy measurement values are labelled unknown rather than retrospectively classified as measured.

Sample corrections retain prior values, measurement sources, timing intervals and reasons. Original button-event timestamps remain intact. Corrected elapsed time drives sample offsets, fitting and fluence calculations. CSV keeps stable machine column names and adds audit columns; full ZIP backups retain complete history and original photos.

Peak-area parsing validates the complete batch before applying changes. Labelled and ordered formats are distinct; errors retain row locations. Fits use positive, included ratios. Exclusions retain reasons; curvature is a model-deviation diagnostic.

Within one device boot, timers use Android monotonic time. Saved wall-clock time supports restart recovery after reboot or device transfer. Imported active timers are paused.

## Data boundaries

Android experiments run locally. Photos and notebook records remain in private storage. Desktop extraction sends parsed text and field instructions to the selected model provider; keys are not stored in project JSON. Runtime data, API credentials and private signing material are excluded from Git and source packages.

There is no direct synchronization between the Android notebook and desktop evidence projects. CSV and ZIP exports provide explicit transfer and backup paths.
