# Architecture

EnvEvidence is a single-user local Python/Streamlit app. The CLI and the existing evidence pipeline remain compatible with v0.1.

## Data boundaries

- Evidence `Project` JSON stays at schema version 1. Parsing, providers, quote location, scientific review and export remain separate modules.
- `Workspace` schema version 1 contains `Preferences` and, since 0.3, only retains `LearningGoal`/`Step`, `DailyTask` and `Note` from 0.2 so existing files load and save unchanged; nothing displays or edits them. It is stored in the data root's `workspace/state.json`, outside the evidence-project discovery pattern.
- Writes use a same-directory temporary file, flush/fsync, and atomic replace. Read/validation failures preserve the original file. There is no concurrent-edit merging or cloud synchronization.

## Presentation

`ui.py` is the application shell; `workbench_ui.py` holds the sidebar and appearance page, and `evidence_ui.py` the evidence workflow. Stable item IDs are used as widget keys. A per-render language context localizes application strings and known legacy diagnostics without rewriting saved scientific records. Widget formatters capture their render language to remain stable across reruns.

Themes use validated six-digit hex colors and application CSS; no private Streamlit configuration API is used. Foreground colors are chosen for contrast. Standard input controls and cards remain neutral. Language and appearance are persisted locally.

## Network boundary

Evidence extraction uses fixed official endpoints only after the user grants consent in the UI or uses CLI `--send-text`. One completed study is checkpointed before proceeding. Original model fields and human revisions are retained separately. A located quote is not proof of scientific support.

There is no OCR, plot digitization, automatic unit conversion, external module loading, account system or multi-user editing. Bench timing and sample records are in the separate EnvBench Android app.
