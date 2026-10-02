# Changelog

## EnvEvidence (desktop) 0.4.0 — 2026-10-01

- Add a local experiment-analysis workflow: conditions, measurements, explicit processing, kinetic fitting, figure settings and SOP export, alongside the existing literature-evidence workflow.
- Import pasted CSV/TSV, mapped CSV/Excel and EnvBench CSV/ZIP. Preserve original bytes, SHA-256 hashes, phone records/photos and manual revisions; connect quantified assays by sample ID.
- Process blank/dilution corrections, compatible unit conversion, normalization and confirmed adsorption mass balances. Keep censored/missing data, independent runs and technical-repeat provenance explicit.
- Fit zero-, first-, integrated second-order and plateau decay, adsorption PFO/PSO/intraparticle diffusion and Monod substrate–rate curves. Add applicable linearizations, fixed C₀/qₑ, raw-scale weighting and fit intervals.
- Show original-scale metrics, point predictions/residuals, transformed metrics and parameter diagnostics. Scale objectives for numerical stability and withhold unreliable confidence intervals.
- Export physical-size PNG/TIFF/SVG with adjustable DPI and a licensed Chinese font. Save reusable SOP settings and unique packages with CSV/XLSX tables, figures, hashes and complete configurations.
- Add `envevidence analyze --config … --output …` to validate and replay exported analysis snapshots into a separate output directory.
- Add bilingual analysis guides and actual experiment/fitting/chart screenshots. Preserve evidence schema, review histories and original CLI commands. Validation coverage is recorded in [desktop validation](docs/VALIDATION.md).

电脑版新增完整的本地实验分析流程，支持多模型比较、可设置尺寸／DPI 的科研图和可重跑 SOP 成果包。手机样品通过导出档案与检测结果关联，文献核验继续独立使用。安卓安装包保持 0.6.1。

## EnvBench (Android) 0.6.1 preview — 2026-10-01

**Published:** [signed APK and checksum](https://github.com/gzpagg/envevidence/releases/tag/v0.6.1-android-preview.1). Android 8.0+, using the existing maintainer signing identity for in-place upgrades. Release checks passed 56 JavaScript tests, Android lint/build, two Android 15 instrumentation tests and the four desktop CI environments. Detailed records are in [Android validation](docs/ANDROID.md) and [desktop validation](docs/VALIDATION.md).

**已发布：**[签名 APK 与校验文件](https://github.com/gzpagg/envevidence/releases/tag/v0.6.1-android-preview.1)。支持 Android 8.0+，沿用维护者签名，可直接覆盖升级。新版导入、样品来源、时间修订和导出已完成回归检查，验证详情见上方记录。

- Keep peak-area rows matched to their samples when a middle row is invalid or empty. The preview blocks the entire paste until all rows are valid; labelled and ordered formats cannot be mixed. Validate every sample before applying a batch.
- Label pH, temperature and volume by their source: measured, carried forward, unmeasured, legacy source unknown or synthetic demo. Confirming a fresh measurement updates its source; corrections keep earlier values and sources.
- Correct sampling offsets and quench delays with a reason while preserving the original button-click times. The samples CSV includes current and original times, measurement sources and correction reasons.
- Require a reason to exclude a point from the fit. Show the fit interval, excluded points and reasons; preserve zero ratios in the table and explain their omission from the logarithmic fit.
- Describe curvature as a diagnostic of the selected data, and centre/scale the time axis for numerical stability. Keep the chosen fit interval under the researcher's control.
- Add an unplanned-sample action alongside the next checkpoint, including baseline samples without consuming a scheduled checkpoint.
- Refresh the English/Chinese product guides and actual interface screenshots. Keep code, examples and validation details together in the repository.
- Add Android WebView regression coverage for invalid/empty LC rows, successful import and restart persistence.
- Disable automatic Claude commit/PR attribution for this project.

## EnvBench (Android) 0.6.0 · archived source preview

Historical analysis update on top of 0.5.0. These source previews preceded the first signed EnvBench APK, 0.6.1; the revised behavior is documented in the release above.

- Paste LC peak areas, labelled (`S-003  12345`) or in sample order, and convert them to C/C₀ against a reference sample or a typed reference area. A live preview shows each line's result; malformed lines are listed rather than guessed (`9 200` is rejected, not read as 200). Areas are stored with each sample.
- Flag lag and tailing: with 5 or more points, a quadratic term in ln(C/C₀) against time is tested at 95%. Accelerating decay suggests a lag phase, slowing decay suggests tailing.
- Leave individual points out of the fit with a per-sample switch; excluded points are drawn hollow and the change is kept in the sample history.
- Show k_obs normalised to the run: the fluence-based rate constant k′E (cm² mJ⁻¹, with its 95% interval) when a fluence rate is set, and k_obs ÷ [oxidant]₀ as a dose comparison.
- Attach photos to a sample from the samples table; they are saved as observations carrying the sample label.
- Samples CSV adds `fluence_mj_cm2`, `peak_area` and `fit_excluded`. Data written by 0.5.0 previews is upgraded on load and import.
- The demo run now uses peak areas and a fluence rate.

## EnvBench (Android) 0.5.0 · archived source preview

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
- Historical validation at this source-preview stage used Node tests and browser checks. Signed packaging and native lint/build/emulator verification were completed for 0.6.1, as recorded above.

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

## 0.3.0 (desktop) · source update

- Focus the desktop app on literature evidence. It opens on the evidence page; the sidebar has Literature evidence and Appearance only.
- Remove learning goals, daily tasks, sticky notes, the module layout settings and the workspace demo from the interface. Existing items stay in `data/workspace/state.json` and are written back unchanged; the sidebar shows how many are kept.
- Remove the planning helpers that only those screens used (`tasks_for_day`, `overdue_tasks`, `task_progress`, `add_demo`, `LearningGoal.progress`) and the note colors.
- Replace the desktop screenshots. Evidence extraction, review, export, the project format and the CLI are unchanged.

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
