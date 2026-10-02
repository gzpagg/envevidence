# EnvBench for Android: screenshots and validation

## 0.6.0 preview (unreleased)

These captures come from the **browser preview** of the bundled interface (Chromium, 390 px wide) with the invented demo run. They are not native Android screenshots. The emulator workflow regenerates native ones when it runs on a pull request.

| View / 页面 | English | 简体中文 |
|---|---|---|
| Run / 反应 | <img src="images/envbench-run-en.png" alt="EnvBench run page with next-sample countdown and checkpoints" width="280"> | <img src="images/envbench-run-zh.png" alt="EnvBench 反应页：下一次取样倒计时与取样点" width="280"> |
| Sample sheet / 取样 | <img src="images/envbench-sample-en.png" alt="Sample sheet with quench chips and pH, temperature and volume steppers" width="280"> | <img src="images/envbench-sample-zh.png" alt="取样面板：淬灭剂选择与 pH、温度、体积调节" width="280"> |
| Paste LC areas / 粘贴峰面积 | <img src="images/envbench-paste-en.png" alt="Paste dialog converting LC peak areas to C/C0 with a preview and a rejected malformed line" width="280"> | <img src="images/envbench-paste-zh.png" alt="粘贴 LC 峰面积：预览 C/C0 并列出无法识别的行" width="280"> |
| Samples and fit / 样品与拟合 | <img src="images/envbench-samples-en.png" alt="Pseudo-first-order fit of ln(C/C0) with k_obs, confidence interval, curvature check and fluence-based k'E" width="280"> | <img src="images/envbench-samples-zh.png" alt="准一级动力学拟合与 k_obs、置信区间、半衰期、R²" width="280"> |

What was checked for 0.6.0 (which includes the unreleased 0.5.0):

- **41 JavaScript tests** (`node --test android/tests/*.test.cjs`): the 25 earlier ones plus 16 for runs. The 6 added in 0.6.0 cover upgrading 0.5.0 samples, lag/tailing/linear curvature (and no verdict below 5 points), fit exclusion, fluence and dose normalisation, peak-area parsing (labels, order, header row, `9 200` rejected, duplicates, extra lines) with C/C₀ conversion and history, and the new CSV columns. The 10 from 0.5.0 cover version 1 → 2 upgrade and import, pull time vs plan, required quench, no samples after a run ends, correction history, ready/due/late transitions, the fit (exact k, half-life, CI, fewer than three points), water validation and SUVA₂₅₄, unpulled checkpoints logged as skipped when a run ends, the CSV (negative offsets, formula neutralising, per-run filtering) and orphan rejection.
- **Browser preview flow** (Playwright, 390 px, English and Chinese): demo load, run page, sample sheet locked until a quench is chosen, steppers, C/C₀ edit and refit, rejection of an invalid C/C₀, live SUVA₂₅₄, CSV download, new run with a plan, due and late states, taking a checkpoint from the Timers tab, reload persistence; for 0.6.0 also pasting areas with a preview and listed errors, a typed reference, the Fit switch and hollow excluded points, the sample editor's area and fit fields, the lag warning, the photo button's preview notice, the new CSV columns and the Chinese paste dialog. No console errors and no horizontal overflow.
- **Android lint, APK build and the emulator test** run in the Android workflow on the pull request; see its result there. They could not be run in the environment used to write this change, because the Android SDK could not be downloaded. The emulator test now expects the demo run's 5 samples in a single-experiment ZIP.
- **Not checked:** a physical phone, the camera path for sample photos, and real LC exports beyond the pasted formats above.

## 0.4.0

[Download APK](https://github.com/gzpagg/envevidence/releases/tag/v0.4.0-android-preview.1) · [English guide](../android/README.md) · [中文安装说明](../android/README.zh-CN.md)

The 0.4 Android app focused on experiments, multiple timers, counters and photo observations. Settings appear only under **My space**. The desktop literature workflow remains available separately.

These unedited screenshots come from the running app on an Android 15 emulator, with invented demo records and a deliberately synthetic image. They contain no private research or API keys. Interface language changes do not translate user-entered text.

安卓现以实验计时、计数和拍照记录为主，设置集中在“我的”。下方是 Android 15 模拟器实际运行的原始截图；示例文字及样品图均为自制演示，不是真实科研数据。切换界面语言不会改写用户输入。

| View / 页面 | English | 简体中文 |
|---|---|---|
| Experiments / 实验 | <img src="images/lab-home-en.png" alt="English experiment notebook" width="280"> | <img src="images/lab-home-zh.png" alt="中文实验首页" width="280"> |
| Timers / 计时 | <img src="images/lab-timers-en.png" alt="English simultaneous timers and sampling reminder" width="280"> | <img src="images/lab-timers-zh.png" alt="中文多计时器与取样提醒" width="280"> |
| Records / 记录 | <img src="images/lab-records-en.png" alt="English observation with synthetic photo" width="280"> | <img src="images/lab-records-zh.png" alt="中文现象记录与自制样品图" width="280"> |
| My space / 我的 | <img src="images/lab-my-en.png" alt="English settings, alerts and backups in My space" width="280"> | <img src="images/lab-my-zh.png" alt="中文集中设置、提醒与备份" width="280"> |

### Validation

- **25 JavaScript tests** cover timer anchors, wall-clock changes within a boot, reboot fallback, overtime, lap/reset history, fixed sampling targets, actual sample times, counters, revisions, archive behavior, import validation and retained literature/planning rules. A 1,200-timer domain case checks the absence of an arbitrary count cap; it is not a physical-phone performance benchmark.
- **50 Python regression tests** pass on Windows/Linux with Python 3.11/3.13. The desktop package and CLI remain version 0.2.0.
- Android lint and debug/release compilation pass. Android 15 emulator instrumentation checks legacy data migration, count/undo, language and activity recreation, native image display, original-photo ZIP round-trip, individual-experiment export isolation, a background countdown notification, notification routing, and retained PDF parsing.
- Browser interface checks cover English/Chinese, four palettes, narrow and wide layouts, observation revisions, archive/restore and saved preferences. The eight native screenshots above show the default warm-white/terracotta palette.
- The published APK is signed with the same private maintainer key as Android 0.3.0 and verified with APK signature schemes v2/v3. The release includes its SHA-256 checksum. Private signing material is excluded from Git and release assets.

See [Android CI](https://github.com/gzpagg/envevidence/actions/workflows/android.yml) and [desktop CI](https://github.com/gzpagg/envevidence/actions/workflows/ci.yml) for recorded runs.

### Remaining validation / 尚未验证

The emulator test uses a generated PNG through the native photo-storage path; it does **not** validate a real camera, gallery provider or manufacturer-specific permission flow. Physical-device camera capture, long-running/reboot alarm behavior and vendor battery-management policies remain untested. Notification/alarm permissions are needed for background alerts; force-stop or muted notification channels can prevent delivery. This is a preview release, not a calibrated timing instrument or a Google Play listing.

已验证模拟器后台倒计时通知、图片保存与备份恢复；尚未用实体手机验证相机、相册、长时间运行、重启后的系统提醒及各厂商省电策略。请在“我的”中启用计时提醒，确认通知和闹钟权限。强行停止应用或关闭通知会影响提醒。

The experiment workflow is entirely local and makes no model calls. Real API calls and scientific accuracy on real papers remain unverified for the separate literature workflow. Existing mobile evidence projects stay in full backups; the mobile primary navigation no longer offers literature extraction/review.

### Data and upgrades / 数据与升级

Install the signed 0.4 APK over 0.3 to preserve local data. Avoid uninstalling first. Export a full ZIP backup, including original photos, before uninstalling or moving devices. Single-experiment ZIPs omit unrelated experiments, personal planning items and literature projects. Archives support up to 512 MB of uncompressed data; split larger collections by experiment. Import adds new IDs and pauses imported running timers.

直接覆盖安装可保留旧数据。卸载前先导出含照片的完整 ZIP 备份；单个实验 ZIP 仅含所选实验及关联记录。每份备份的未压缩内容上限为 512 MB，可按实验分开导出。导入不会覆盖已有编号，导入的运行中计时会暂停。

Photos retain their original bytes and metadata; displayed previews are smaller copies. Recorded photo times describe when the image was added, not when an imported photo was originally taken. Exports contain your research content and should be shared intentionally.
