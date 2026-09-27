# EnvEvidence Lab for Android · 0.4.0 preview

[简体中文](README.zh-CN.md) · [Desktop literature tools](../README.md) · [Screenshots and validation](../docs/ANDROID.md)

An offline companion for the laboratory bench: keep several processes timed, count actions, photograph changes and record observations in context. The main tabs are **Experiments, Timers, Records and My space**. Appearance and settings live under My space; learning goals, daily tasks and sticky notes remain available as additional tools.

## Install

Download the [signed preview APK](https://github.com/gzpagg/envevidence/releases/tag/v0.4.0-android-preview.1) and open it on Android 8.0+ with an up-to-date Android System WebView. It uses the same application ID and signing identity as 0.3.0, so install it as an update. Export a backup before uninstalling; uninstalling removes app data.

No account, Python installation or server is needed. **My space → Load lab demo** adds invented examples without replacing your own records. The mobile experiment features make no API calls.

## At the bench

1. Start an experiment with a name. Sample labels and descriptions are optional.
2. Add stopwatches or countdowns, name/color them, and start or pause a group. There is no fixed timer-count cap; practical capacity depends on device memory and storage. Laps, finishes and resets retain their history. Expired countdowns show overtime until handled.
3. Add a sampling plan in minutes after the experiment starts. Mark **Sample taken** to record the actual time separately from the planned point. Pausing a sampling reminder does not move its original target; resuming catches up to the original experiment clock.
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
