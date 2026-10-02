# Validation record

[简体中文](VALIDATION.zh-CN.md) · [Android checks](ANDROID.md) · [Project introduction](../README.md)

## EnvEvidence desktop · 0.3.0

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

English and Chinese demos use original synthetic fixtures. The current 16 Android screenshots come from the actual bundled 0.6.1 interface in a local Chromium preview: 390 × 844 pixels for both the viewport and exported PNGs. The six desktop captures come from the running EnvEvidence 0.3.0 Streamlit interface at 1440 × 1080. Both use isolated synthetic data. The desktop demo provider checks fixture hashes and uses recorded extraction results; loading a demo makes no model call.

Earlier desktop acceptance checks exercised 1440 px and 390 px layouts, all four palettes and a custom dark background. Native Android 15 baseline checks covered image storage, ZIP round-trips, background notifications and activity recreation. Current screenshots and release checks are tracked in the Android record.

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
