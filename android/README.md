# EnvBench for Android · 0.6.0 preview

[简体中文](README.zh-CN.md) · [Desktop literature tools](../README.md) · [Screenshots and validation](../docs/ANDROID.md) · [Samples CSV schema](../docs/BENCH_CSV.md)

EnvBench (formerly EnvEvidence Lab) is an offline companion for reaction runs at the bench, built for advanced-oxidation and DOM work in water and wastewater. It counts down to each sampling checkpoint, will not save a sample without a quench, records the real pull time next to the planned one, keeps the water matrix with the run, and fits k_obs once C/C₀ values are in. Timers, counters, photo observations and the timeline from 0.4 remain. The main tabs are **Experiments, Timers, Records and My space**.

The phone app does one job: the run. Literature extraction and review live in the [EnvEvidence desktop app](../README.md). Learning goals, tasks and notes from earlier versions are no longer shown, but their data is kept and included in every full backup.

## Install

**0.6.0 has no signed release yet.** The Android workflow on each pull request builds a test APK (artifact `envbench-android-0.6.0`, file `app-debug.apk`). It is signed with a debug key, so it cannot install over a signed 0.3/0.4 app: export a full backup first, uninstall, install the test APK, then import the backup. The [signed 0.4.0 preview APK](https://github.com/gzpagg/envevidence/releases/tag/v0.4.0-android-preview.1) remains the latest release. Android 8.0+ with an up-to-date Android System WebView. 0.6.0 keeps the same application ID, so once signed with the maintainer key it installs as an update over 0.3 and 0.4 and migrates their data. Export a backup before uninstalling; uninstalling removes app data.

No account, Python installation or server is needed. **My space → Load lab demo** adds an invented UV/PDS run with samples and water data, without replacing your own records. The mobile features make no API calls.

## A reaction run

1. Tap **New reaction run** when the lamp goes on or the oxidant goes in. Saving starts the run clock at t = 0. Choose the process (UV/PDS, UV/H₂O₂, O₃, Fenton and others), target, oxidant dose, wavelength and fluence rate, and enter the sampling plan in minutes, for example `1, 2, 5, 10, 20, 30`.
2. The run page opens with the next checkpoint as the largest thing on screen. It turns to the accent color 30 s before the checkpoint, amber when it is due, and red once it is more than 30 s late. A late sample can still be taken; its real time is kept.
3. **Take sample** freezes the pull time and opens a sheet. Tap the quench agent you used (Na₂S₂O₃, MeOH, EtOH, catalase, ascorbic acid, none, or type another); the moment you tap it is stored as the quench time. **Save sample** stays disabled until a quench is chosen. pH, temperature and volume use large − / + steppers and start from the previous sample's values. Samples are labelled S-001, S-002 … in pull order.
4. **Water matrix** records the matrix class, lot, 0.45 µm filtration, spiking, DOC, UV₂₅₄, alkalinity, Cl⁻, NO₃⁻-N, Br⁻, conductivity and pH. SUVA₂₅₄ is computed and labelled as computed. Unmeasured fields stay empty and count against the 8-field completeness bar.
5. After the LC run, tap **Paste LC peak areas** and paste the export: `S-003  12345` per line (tab, comma or spaces), or just the areas in sample order. Choose the reference (by default S-001, or type a C₀ area) and check the preview; lines that cannot be read are listed, not guessed. C/C₀ can also be typed directly. The pseudo-first-order fit (least squares of ln(C/C₀) against real pull time) updates with k_obs, its 95% confidence interval, t½ and R². With 5 or more points it tests for curvature and warns about a **lag phase** or **tailing**; untick **Fit** on a row to leave that point out. When the run has a fluence rate, the fluence-based k′E (cm² mJ⁻¹) is shown; with an oxidant dose, k_obs ÷ [oxidant]₀ is shown for comparing doses. Corrections keep the earlier value in the sample's history; the pull time and quench are never edited. The camera button on a row adds a photo labelled with that sample.
6. **Samples CSV** exports one row per sample in the [shared schema](../docs/BENCH_CSV.md), with the run and water columns on every row.

Checkpoints can also be taken from the Timers tab. Ordinary experiments without a process still work as in 0.4.

## Other experiments, timers and observations

1. Start an experiment with a name. Sample labels and descriptions are optional.
2. Add stopwatches or countdowns, name/color them, and start or pause a group. There is no fixed timer-count cap; practical capacity depends on device memory and storage. Laps, finishes and resets retain their history. Expired countdowns show overtime until handled.
3. Add a sampling plan in minutes after the experiment starts. **Take sample** opens the sample sheet described above and records the actual time separately from the planned point. Pausing a sampling reminder does not move its original target; resuming catches up to the original experiment clock.
4. Use counters with +1, undo and separate rounds. Resetting keeps prior events.
5. Tap **Take photo** or **Add observation** inside an experiment. Observations keep their creation time, experiment elapsed time, sample label and earlier text revisions. Photos also have their own time of addition; this is not a claim about the original camera shutter time.
6. Review the combined timeline. Export CSV, an individual experiment ZIP, or a full backup including original photos.

## Timer alerts

Open **My space → Enable timer alerts** and allow Android notifications and alarms. The UI shows when these permissions are incomplete. A system alarm handles the next due countdown; multiple due timers are grouped in one notification. Notification taps open Timers. There is no continuously running background service.

Within one device boot, elapsed time uses Android's monotonic clock and survives activity/process recreation. After reboot or transfer to another device, recovery falls back to saved wall-clock times. Changing the system clock across a reboot can therefore affect recovery. Imported running timers are paused to avoid unexpectedly rearming old reminders.

Force-stop, muted notification channels and manufacturer power-management policies can suppress alerts. Android 15 emulator checks cover a background notification; physical-device camera behavior, long-duration/reboot scenarios and vendor battery policies still need testing. This is a preview, not a calibrated timing instrument or a Google Play listing.

## Photos, backups and compatibility

- Camera and gallery use Android's own apps/picker. JPEG, PNG and WebP images up to 30 MB each are supported. Originals and their metadata are retained; smaller previews are used only for display.
- Data and photos live in private app storage. Cloud/device backup is disabled. Photos and observations are never uploaded by these features.
- Full ZIP backups include workspace JSON, original photos and display previews. Single-experiment ZIPs include only that experiment and its associated records; unrelated learning items and literature projects are excluded.
- ZIP export/restore supports up to 512 MB of uncompressed content per archive. Larger notebooks can be exported as separate experiments. Existing IDs are kept when importing; conflicting photo bytes are rejected.
- Existing 0.3.0 evidence and planning data are preserved during migration. Literature extraction/review now belongs in the desktop app; old evidence projects remain in full backups. Desktop project/workspace JSON can still be imported.
- No OCR, photo interpretation, speech recognition, accounts, cloud sync or AI service is used by the experiment workflow.

## Build and checks

Use JDK 17+, Android SDK 36 and build-tools 35.0.0. The official Gradle 8.13 wrapper is included.

```sh
cd android
./gradlew lintDebug testDebugUnitTest assembleDebug assembleRelease
cd ..
node --test android/tests/*.test.cjs
```

On Windows use `gradlew.bat`. The [Android workflow](../.github/workflows/android.yml) builds debug/unsigned-release APKs and runs domain checks plus Android 15 emulator checks. Released APKs are signed locally with a stable private key. Keep the signing identity backed up privately; future updates require it. It is never included in Git or the APK.

The app uses bundled HTML/CSS/JavaScript through WebViewAssetLoader. Java handles private atomic storage, monotonic clocks, system alarms, notifications, camera/file access and ZIP/photo preservation. No remote webpage is loaded into the app. The localhost browser preview supports interface checks; camera and background alarms require Android.

See [recorded validation](../docs/ANDROID.md) for tested behavior and remaining limits. The warm-paper/terracotta presentation follows the requested visual direction, with original EnvEvidence branding and controls. Interaction references: [Time Timer](https://support.timetimer.com/hc/en-us/articles/29258432418203-Time-Timer-App-Free-vs-Paid-Premium-Features), [LabArchives entries](https://help.labarchives.com/hc/en-us/articles/11729082137364-Adding-and-Editing-Entries), and [Claude Android](https://claude.com/blog/android-app). No affiliation is implied.

Code and invented fixtures: MIT. See [third-party notices](../THIRD_PARTY_NOTICES.md).
