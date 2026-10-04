# EnvBench screenshots and validation

[English guide](../android/README.md) · [中文说明](../android/README.zh-CN.md) · [Samples CSV](BENCH_CSV.md)

## Current interface · 0.7.0

All 26 Android screenshots show the actual bundled 0.7.0 interface running in a local Chromium browser preview at 390 × 844 pixels. Isolated synthetic UV/PDS experiments supply the procedures, samples and analytical values. Both languages use the Mineral teal design. The twelve desktop screenshots show the running EnvEvidence 0.4.1 app at 1440 × 1080.

| New tool / 新功能 | English | 简体中文 |
|---|---|---|
| Experiment steps / 实验步骤 | <img src="images/envbench-steps-en.png" alt="Current step and linked countdown" width="240"> | <img src="images/envbench-steps-zh.png" alt="当前步骤与关联倒计时" width="240"> |
| Templates / 模板 | <img src="images/envbench-templates-en.png" alt="Reusable template" width="240"> | <img src="images/envbench-templates-zh.png" alt="可复用实验模板" width="240"> |
| Stage setup / 阶段配置 | <img src="images/envbench-stage-setup-en.png" alt="Stages, cycles and delay" width="240"> | <img src="images/envbench-stage-setup-zh.png" alt="阶段、循环与延迟" width="240"> |
| Stage timers / 阶段计时 | <img src="images/envbench-stage-timers-en.png" alt="Stage confirmation controls" width="240"> | <img src="images/envbench-stage-timers-zh.png" alt="阶段计时与确认" width="240"> |
| Observations / 现象 | <img src="images/envbench-observation-en.png" alt="Observation with audio and speech actions" width="240"> | <img src="images/envbench-observation-zh.png" alt="现象、录音与语音操作" width="240"> |

| View / 页面 | English | 简体中文 |
|---|---|---|
| Run / 反应 | <img src="images/envbench-run-en.png" alt="Reaction page, sampling schedule and water-matrix summary" width="280"> | <img src="images/envbench-run-zh.png" alt="反应页、取样计划与水体基质摘要" width="280"> |
| Sample sheet / 取样 | <img src="images/envbench-sample-en.png" alt="Sample sheet with quench selection and measurement-source controls" width="280"> | <img src="images/envbench-sample-zh.png" alt="取样面板、淬灭剂与测量来源" width="280"> |
| LC import / 峰面积导入 | <img src="images/envbench-paste-en.png" alt="LC peak-area import with sample assignments and validation" width="280"> | <img src="images/envbench-paste-zh.png" alt="LC 峰面积导入、样品对应与校验" width="280"> |
| Samples and fit / 样品与拟合 | <img src="images/envbench-samples-en.png" alt="Sample table, concentration trend and fitted interval" width="280"> | <img src="images/envbench-samples-zh.png" alt="样品记录、浓度趋势与拟合范围" width="280"> |

These are browser interface captures. Native camera, storage, notification and activity behavior have separate Android instrumentation coverage described below.

## Release checks · 0.7.0

[Android CI](https://github.com/gzpagg/envevidence/actions/runs/37188040448) passed **87 JavaScript tests**, **13 JVM unit tests**, Android lint, debug/release APK builds and **7 Android 15 emulator instrumentation tests**. [Desktop CI](https://github.com/gzpagg/envevidence/actions/runs/37188040439) passed **188 tests in each of the four Windows/Linux and Python 3.11/3.13 environments**, together with Ruff, the offline CLI demo and source/wheel builds. Local checks also passed 87 JavaScript tests and 188 desktop tests, plus Ruff.

English/Chinese browser scenarios exercise new template runs, timed steps, skip/repeat history, linked observations, manual timer cycles, phrases and restart persistence. Layout checks cover five palettes and 360/390 px phone widths, plus the 768 px procedure layout.

Native coverage includes recording and lifecycle recovery, seekable playback, original-media ZIP integrity and retention of native media after a stale browser save. These checks use an emulator and synthetic records. System speech recognition depends on the installed service and may send speech to that service.

## Published APK · 0.7.0 preview

[Download APK](https://github.com/gzpagg/envevidence/releases/download/v0.7.0-android-preview.1/envbench-0.7.0-android.apk) · [SHA-256 file](https://github.com/gzpagg/envevidence/releases/download/v0.7.0-android-preview.1/envbench-0.7.0-android.apk.sha256) · [Release notes](https://github.com/gzpagg/envevidence/releases/tag/v0.7.0-android-preview.1)

The signed APK is 13,558,841 bytes. Package `io.github.gzpagg.envevidence`, version 0.7.0 / code 8, minimum API 26 and target API 36. Signature schemes v2/v3 passed verification, with the same maintainer certificate as previous releases. All 25 bundled assets match the merged Git tree byte for byte.

The APK was built by [Android CI 37187667580](https://github.com/gzpagg/envevidence/actions/runs/37187667580) from source `2ab018ee515b0beae32dd72e2f76d98eb1c384ce`, merged through [PR #7](https://github.com/gzpagg/envevidence/pull/7). Its assets also match main `3b62192269f4a967a8cb6e4fe8a1bf753ed71871`. Comparing Git blobs avoids Windows checkout newline conversion.

APK SHA-256:

```text
0847bc0e223fcb80ec3e5c014d473069bc8037bbb1f6e9ad513ac7e2583adf6d
```

Signing-certificate SHA-256:

```text
1833c322295af3aee2edee378713ba8f970671165cff9532a9165d02108de28f
```

## Previously published APK · 0.6.1 preview

[Download APK](https://github.com/gzpagg/envevidence/releases/download/v0.6.1-android-preview.1/envbench-0.6.1-android.apk) · [SHA-256 file](https://github.com/gzpagg/envevidence/releases/download/v0.6.1-android-preview.1/envbench-0.6.1-android.apk.sha256) · [Release notes](https://github.com/gzpagg/envevidence/releases/tag/v0.6.1-android-preview.1)

The published APK is 10,272,894 bytes. Its package is `io.github.gzpagg.envevidence`, version 0.6.1 / code 7, minimum Android API 26 and target API 36. APK signature schemes v2/v3 passed verification; the signing certificate matches the 0.4.0 maintainer-signed app. Bundled app assets match source revision `ca4b6b545d40dde9c1e28e7bf1cdc7d7575aca4e`, merged through PR #5.

APK SHA-256:

```text
e8d0d1b944cdaad78d7a1c00301779aef3372598a5e683c24e482ba00b804f52
```

Signing-certificate SHA-256:

```text
1833c322295af3aee2edee378713ba8f970671165cff9532a9165d02108de28f
```

## Release checks · 0.6.1

[Android CI](https://github.com/gzpagg/envevidence/actions/runs/36954317866) completed successfully for the published source revision: **56/56 JavaScript tests**, Android lint, JVM unit tests, debug/release APK builds, and **2/2 Android 15 emulator instrumentation tests**. The new native test covers invalid/empty LC rows, successful import and restart persistence; the notebook test covers timing, image storage, backups, legacy data and background alerts.

[Desktop CI](https://github.com/gzpagg/envevidence/actions/runs/36954317903) passed Windows/Linux × Python 3.11/3.13: each environment passed **46 tests**, Ruff, the offline CLI demo and source/wheel builds. Local checks also passed 56 JavaScript tests, 46 Python tests and Ruff.

Version 0.6.1 adds regression coverage for peak-area assignment, rejected batches, measurement sources, timing revisions, exclusions and CSV audit columns.

The automated and interface checks cover:

- Invalid and internal empty area rows retain their positions; every error blocks applying the batch. Duplicate, extra and mixed-format assignments are rejected before data changes.
- Measured, carried-over, unmeasured and legacy-unknown sample sources survive save, import and export.
- Timing corrections preserve original events, require a reason and update the time used by the fit.
- Unplanned sampling leaves the scheduled checkpoint intact.
- Fit exclusions retain their reasons. Zero ratios remain recorded and are identified as ineligible for logarithmic fitting.
- Curvature checks use centered/scaled time and describe model deviation. The interface displays the fitted interval and exclusion count.
- English/Chinese sample sheets, imports, corrections and exports render with the default warm-paper/terracotta appearance.

## Recorded baseline · 0.6.0 / desktop 0.3.0

The merged implementation passed [Android CI](https://github.com/gzpagg/envevidence/actions/runs/36945435012) and [desktop CI](https://github.com/gzpagg/envevidence/actions/runs/36945434951). Android CI ran lint, JavaScript checks, APK compilation and Android 15 emulator instrumentation. The desktop matrix ran on Windows/Linux with Python 3.11/3.13.

The 41 Android JavaScript tests covered timers, counters, records, legacy migration and reaction-run features: checkpoints, sample/quench records, correction history, water validation, SUVA₂₅₄, curve fitting, exclusions, area conversion and CSV exports. Version 0.6.1 extends this baseline with the cases above.

Android instrumentation checked legacy data migration, count/undo, language and activity recreation, native image display, original-photo ZIP round-trip, experiment export isolation, background countdown notifications, notification routing and retained PDF parsing. The previous suite did not cover every new reaction-run interaction; the 0.6.1 native import regression now covers row alignment, rejected input, successful import and persistence.

## Device and research coverage

The emulator uses generated images through the native photo-storage path. Physical-phone camera/gallery providers, long-duration runs, reboot recovery and manufacturer battery policies need separate device checks. System notification and alarm permissions govern background alerts.

Bench calculations are tested with synthetic numerical examples. Real LC datasets and independent use during laboratory experiments have not been evaluated as a validation dataset. Literature extraction has its own [validation record](VALIDATION.md).

## Backups and upgrades

Maintainer-signed updates retain the application ID and existing data. Export a full ZIP with original photos before uninstalling or moving devices. Import adds new IDs and pauses imported running timers; conflicting photo bytes are rejected. Archives support up to 512 MB uncompressed content, so larger notebooks can be split by experiment.

Version 0.6.1 keeps the lab schema at version 2 and adds CSV audit columns. Earlier nonempty measurement values have an unknown source until confirmed; empty values stay unmeasured. Existing evidence and planning data remain in full backups.

## Experiment notebook views · 0.7.0

The remaining eight captures show the current experiment notebook, timers, observations and My space pages in the same Chromium preview. They use isolated synthetic records and the same 390 × 844 viewport and PNG dimensions.

| View / 页面 | English | 简体中文 |
|---|---|---|
| Experiments / 实验 | <img src="images/lab-home-en.png" alt="Current English experiment notebook" width="240"> | <img src="images/lab-home-zh.png" alt="当前中文实验手记" width="240"> |
| Timers / 计时 | <img src="images/lab-timers-en.png" alt="Current English timers" width="240"> | <img src="images/lab-timers-zh.png" alt="当前中文计时" width="240"> |
| Records / 记录 | <img src="images/lab-records-en.png" alt="Current observation with a synthetic photo" width="240"> | <img src="images/lab-records-zh.png" alt="当前现象记录与演示图" width="240"> |
| My space / 我的 | <img src="images/lab-my-en.png" alt="Current settings and backup controls" width="240"> | <img src="images/lab-my-zh.png" alt="当前设置与备份" width="240"> |

[Android workflow](https://github.com/gzpagg/envevidence/actions/workflows/android.yml) · [Desktop workflow](https://github.com/gzpagg/envevidence/actions/workflows/ci.yml)
