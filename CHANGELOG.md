# Changelog

## EnvBench (Android) 0.5.0 preview · unreleased

The Android app is now **EnvBench**, a bench companion for advanced-oxidation and DOM runs. The application ID is unchanged, so it updates 0.3/0.4 in place.

- Add reaction runs: process (UV/PDS, UV/H₂O₂, O₃, Fenton and others), target, oxidant dose, wavelength and fluence rate. Saving starts the run clock at t = 0, with an optional sampling plan.
- Show the next checkpoint as a large countdown that changes state 30 s before it (ready), at it (due) and 30 s after it (late), plus a checkpoint rail with each sample's offset from plan.
- Add a sample sheet that freezes the pull time, requires a quench (the tap time is stored as the quench time), and records pH, temperature and volume with steppers prefilled from the previous sample. Samples are labelled S-001, S-002 … and corrections keep earlier values.
- Add water matrix details per run (class, lot, filtration, spiking, DOC, UV₂₅₄, alkalinity, Cl⁻, NO₃⁻-N, Br⁻, conductivity, pH) with computed SUVA₂₅₄ and a completeness bar.
- Add C/C₀ entry and a pseudo-first-order fit (k_obs with 95% CI, t½, R²) on real pull times.
- Add the samples CSV, schema `envbench-samples-v1` ([spec](docs/BENCH_CSV.md)); single-experiment ZIPs now include that run's samples.
- Retire learning goals, tasks and notes from the phone UI. Their data and literature projects stay unchanged in storage and full backups.
- Lab data moves to version 2; version 1 notebooks and backups are upgraded on load and import.
- Fix: finishing an experiment no longer logs its unpulled sampling checkpoints as "Sample taken"; they are logged as closed without a sample.
- Start the interface after all scripts load, which removes a race in the first render.
- Not yet done: a signed APK, Android lint/build and emulator runs for this version, and checks on a physical phone. Tested with Node domain tests and the browser preview.

## Android 0.4.0 preview — 2026-09-27

- Refocus mobile navigation on Experiments, Timers, Records and My space. Move settings and retained learning/task/note tools into My space.
- Add simultaneous stopwatches/countdowns, lap history, overtime, group controls, fixed sampling targets and counters with undo/round history.
- Add native camera/gallery observations, original-photo preservation, note revisions, experiment timelines and CSV/ZIP export/import.
- Use native monotonic clock anchors, permission-aware system alarms, grouped notifications and notification links to the timer page.
- Adopt a consistent warm-paper/terracotta interface with English/Chinese support and existing/custom color preferences.
- Preserve 0.3.0 evidence and planning data on upgrade. Physical-device camera/power-management validation remains open.


## Android 0.3.0 preview — 2026-09-27

- Add a standalone Android app with an offline bilingual workspace, learning checklists, dated tasks and notes.
- Add four palettes, custom colors, module visibility/order, archive/restore and private atomic storage.
- Parse text PDFs locally, attach supplements, call OpenAI/Anthropic with a run-only user key, and checkpoint completed papers.
- Preserve source quotes, page metadata, original values and append-only human review; export CSV/project JSON/full backups.
- Import desktop project/workspace JSON and additive Android backups without overwriting existing IDs.
- Add domain tests, Android lint/build and Android 15 emulator workflow. Desktop Python/CLI stays at 0.2.0.
- This preview has not been validated against live model APIs, real research papers or physical Android devices.

## 0.2.0 — 2026-09-26

- Add a configurable research workspace with learning checklists, dated tasks and colored sticky notes.
- Add archive/restore, persistent module visibility/order and four palettes plus custom colors.
- Default to English with persistent Chinese language switching and localized evidence review.
- Preserve v0.1 evidence schemas, model values, citations and audit history.
- Add bilingual documentation and actual interface screenshots.
- Add tests for progress calculations, persistence, archive/restore, themes and language switching.
- Live provider calls and accuracy on real papers remain unverified.


## 0.1.0

- Local text-PDF import with explicit main/supplement associations and page coverage warnings.
- Water-treatment and custom extraction fields; OpenAI/Anthropic structured-output adapters.
- Per-condition evidence records and deterministic quotation location checks.
- Human review and append-only correction history; atomic project snapshots and study-level resume.
- CSV, Excel, and full JSON export; offline synthetic demo and automated regression tests.
- Chinese interface, bilingual README, packaging, CI workflow, and issue template.

