# Architecture

EnvEvidence is a single-user local Python/Streamlit app. The CLI and the existing evidence pipeline remain compatible with v0.1.

## Data boundaries

- Evidence `Project` JSON stays at schema version 1. Parsing, providers, quote location, scientific review and export remain separate modules.
- `Workspace` schema version 1 contains `Preferences`, `LearningGoal`/`Step`, `DailyTask`, and `Note`. It is stored in the data root's `workspace/state.json`, outside the evidence-project discovery pattern.
- Writes use a same-directory temporary file, flush/fsync, and atomic replace. Read/validation failures preserve the original file. There is no concurrent-edit merging or cloud synchronization.
- Progress uses step counts and tasks' planned dates, excluding archived records. Empty denominators produce empty states, not percentages. Dates follow the host computer.

## Presentation

`ui.py` is the application shell; the workbench and evidence UI are separate. Stable item IDs are used as widget keys. A per-render language context localizes application strings and known legacy diagnostics without rewriting saved scientific records. Widget formatters capture their render language to remain stable across reruns.

Themes use validated six-digit hex colors and application CSS; no private Streamlit configuration API is used. Foreground colors are chosen for contrast. Standard input controls and cards remain neutral. Notes are HTML-escaped before rendering. Language, appearance, visibility and ordering are persisted locally.

## Network boundary

Planning and note-taking do not call models. Evidence extraction uses fixed official endpoints only after the user grants consent in the UI or uses CLI `--send-text`. One completed study is checkpointed before proceeding. Original model fields and human revisions are retained separately. A located quote is not proof of scientific support.

There is no OCR, plot digitization, automatic unit conversion, external module loading, timer, habit recurrence, notification scheduler, account system or multi-user editing.
