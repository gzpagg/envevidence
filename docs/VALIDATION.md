# Validation record

[简体中文](VALIDATION.zh-CN.md) · [Android checks](ANDROID.md) · [Project introduction](../README.md)

## Current desktop 0.5.0 / Android 0.8.0

Local Windows/Python 3.13 passed **199 Python tests and Ruff**. The mobile domain suite passed **94 JavaScript tests**. New cases cover Glacier defaults, one-time migration of the original Mineral preference triple, preservation of custom colors, explicit selection of Mineral after upgrading, material settings and old-backup compatibility. Existing scientific, evidence, timer and media regressions remain included.

[Desktop CI 37310677562](https://github.com/gzpagg/envevidence/actions/runs/37310677562) passed on **Windows/Linux with Python 3.11/3.13**: all four environments passed **199 tests**, Ruff, the offline CLI demo and source/wheel builds. [Android CI 37310677615](https://github.com/gzpagg/envevidence/actions/runs/37310677615) passed **94 JavaScript tests, 13 JVM tests and 8 Android 15 emulator instrumentation tests**, Android lint, and debug/release APK builds. The signed 0.8.0 APK passed v2/v3 signature verification and byte-for-byte checks of all 25 bundled assets; its checksum is in the [Android release record](ANDROID.md#published-apk--080-preview). The 0.4.1 / 0.7.0 links below remain historical baselines.

The added Android appearance test verifies migration from the original default, reduced-transparency persistence across activity restart, preservation of legacy notes, and selecting Mineral again after upgrading. Existing native recording, playback, media ZIP, import and background-alert tests also passed.

The actual Chromium checks in `scripts/check_glacier_ui.js` passed in English and Chinese with isolated synthetic records:

- Twenty timers running together; visible digit updates, focus switching, pause/resume and manual-stage waiting. The home sampling countdown advances while the page remains open.
- Empty views, multiple experiments, long unbroken labels, dated observations, and photo/audio/text layout at **360, 390 and 768 px**. A **460 px** viewport simulates keyboard-constrained dialogs and verifies the save control remains reachable.
- Glass, solid and reduced-transparency settings saved and restored after reload. System reduced-motion and reduced-transparency preferences activate their fallbacks.

The 90-frame browser samples had a 6.2 ms 95th-percentile interval in both languages, with no interval above 100 ms. These measurements describe this local Chromium session, not Android-device frame rates. Photo thumbnails were scoped browser fixtures; this check exercises media layout rather than native capture or playback.

The desktop browser run in `scripts/check_desktop_layouts.js` passed **both languages, seven palettes and all six analysis tabs** at widths **1440, 360, 390 and 768 px**. It also checked material controls, preference persistence and reset, system reduced transparency, reduced motion, and evidence columns stacking on narrow screens.

Existing mobile workflow and capture scripts also passed the template, linked-step, sampling, LC import, revision and seven-palette scenarios. The refreshed screenshots use the Glacier design; their sources and dimensions are listed below.

## Historical baseline · desktop 0.4.1 / Android 0.7.0

[Desktop CI](https://github.com/gzpagg/envevidence/actions/runs/37188040439) passed on **Windows and Linux with Python 3.11 and 3.13**: each of the four environments passed **188 tests**, Ruff, the offline CLI demo and source/wheel builds. Local Windows/Python 3.13 also passed 188 tests and Ruff. [Android CI](https://github.com/gzpagg/envevidence/actions/runs/37188040448) passed **87 JavaScript tests**, **13 JVM unit tests**, Android lint, debug/release APK builds and **7 Android 15 emulator instrumentation tests**. The local JavaScript suite also passed 87 tests.

New coverage checks shared fonts/tokens, saved and legacy appearance, stage-timer boundaries, template snapshots, step histories, media manifests and desktop import compatibility. Native emulator checks cover recording and lifecycle recovery, seekable playback, media ZIP integrity and preservation of native media after a stale browser save.

Browser scenarios use actual running interfaces and isolated synthetic data. Both languages cover fresh experiments, linked timers and observations, reasoned skips, repeated steps, manual cycles, editable phrases and restart persistence. That release used the Mineral teal design.

## EnvEvidence desktop · 0.4.0

The local Windows/Python 3.13 check passes **132 tests**, Ruff, the literature CLI demo and source/wheel builds. The [four-environment desktop workflow](https://github.com/gzpagg/envevidence/actions/workflows/ci.yml) records Windows/Linux and Python 3.11/3.13 results for each published revision.

New coverage includes known-parameter decay, adsorption and Monod curves; fixed parameters, weights, transformations, weak identifiability and numerical scales; explicit corrections and units; original-byte/hash preservation; mobile CSV/ZIP and assay IDs; atomic persistence and audited revisions; compatible SOP templates; accepted-fit selection; PNG/TIFF/SVG dimensions, Chinese fonts and full legend identities; and an actual CLI replay with matching parameters. The original literature regression suite remains included.

The numerical fixtures are self-created. Laboratory validation on independent real measurements is a separate evaluation activity; parameter intervals describe the recorded fitting assumptions.

## EnvEvidence desktop · 0.3.0 baseline

The desktop evidence app passed [CI for the published revision](https://github.com/gzpagg/envevidence/actions/runs/36954317903): Windows/Linux with Python 3.11/3.13. Each of the four environments passed **46 tests**, Ruff, the offline CLI demo and source/wheel builds. The current local run also passed all 46 tests and Ruff.

Coverage includes:

- Separate experimental conditions and pollutant/TOC endpoints, supplement provenance, fabricated-quote detection, missing units and reviewer history.
- Mocked OpenAI/Anthropic HTTP contracts, refusal/truncation handling and interrupted extraction recovery.
- CSV/Excel/JSON exports, spreadsheet formula protection and package exclusions for runtime data.
- Atomic workspace persistence, corrupted-file preservation, saved language and appearance.
- Opening directly on literature evidence, and preserving version-0.2 learning, task and note data through language/appearance saves.

The planning interface was removed in 0.3.0. Four planning-interface tests were replaced or removed as appropriate; the evidence pipeline and its regression checks continue unchanged.

## EnvBench Android · 0.6.1

The [signed 0.6.1 preview](https://github.com/gzpagg/envevidence/releases/tag/v0.6.1-android-preview.1) is published. [Android CI](https://github.com/gzpagg/envevidence/actions/runs/36954317866) passed **56/56 JavaScript tests**, Android lint, JVM unit tests, debug/release APK compilation and **2/2 Android 15 emulator instrumentation tests**. The local JavaScript suite also passed 56/56 tests.

New regressions cover invalid/empty LC-row alignment, whole-batch validation, sample measurement sources, audited timing corrections, reasoned exclusions, planned versus unplanned sampling and CSV audit columns. The native import test checks invalid/empty input, successful application and restart persistence. The notebook test covers legacy migration, counters, language/activity recreation, original-photo ZIP round-trips and background alerts. APK checksum, signature and source-asset checks are recorded in [Android checks](ANDROID.md).

The recorded 0.6.0 baseline passed 41 JavaScript tests plus [Android lint, APK builds and emulator instrumentation](https://github.com/gzpagg/envevidence/actions/runs/36945435012). Android tests use synthetic experiments and generated images.

## Interface and demo material

English and Chinese demos use original synthetic fixtures. The current 26 Android screenshots come from the actual bundled 0.8.0 interface in a local Chromium preview: 390 × 844 pixels for both the viewport and exported PNGs. The twelve desktop captures come from the running EnvEvidence 0.5.0 Streamlit interface at 1440 × 1080, including analysis, fitting, chart controls, evidence and appearance. Both use the Glacier design and isolated synthetic data. The captures explicitly enable glass rendering; the separate browser checks verify the reduced-transparency alternative. The desktop demo provider checks fixture hashes and uses recorded extraction results; loading a demo makes no model call.

The 0.4.0 browser check exercised all six analysis tabs in both languages and all four palettes at 1440 × 1080, plus both languages at 390 × 844. It found no application exceptions or page overflow. The script is saved in `scripts/check_desktop_layouts.js`. Earlier acceptance checks also covered a custom dark background. Native Android 15 baseline checks covered image storage, ZIP round-trips, background notifications and activity recreation. Current Android screenshots and release checks are tracked in the Android record.

## Research and device evaluation

Live API extraction and scientific accuracy on real papers have not been benchmarked. The quotation locator checks whether cited text exists on the parsed page; the reviewer assesses experimental association, units and interpretation.

Bench numerical checks use synthetic ratios and known curves. Physical-phone camera providers, long-running/reboot behavior, vendor battery policies and independent laboratory use remain separate evaluation work. These are distinct from unit tests and successful package builds.

## Reproduce automated checks

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
python -m ruff check .
python -m envevidence demo --output data/demo
python -m build
node --test android/tests/*.test.cjs
```

The exact outcome for a revision is shown by its workflow run. [Desktop workflow](https://github.com/gzpagg/envevidence/actions/workflows/ci.yml) · [Android workflow](https://github.com/gzpagg/envevidence/actions/workflows/android.yml)
