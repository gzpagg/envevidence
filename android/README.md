# EnvEvidence for Android · 0.3.0 preview

[简体中文](README.zh-CN.md) · [Desktop app](../README.md)

A standalone, offline-first research workspace. No server, Streamlit installation or new account is needed on your phone. English and Chinese, four palettes and custom colors, configurable module order, learning checklists, dated tasks and sticky notes are included.

## Install and use

Download the [signed preview APK](https://github.com/gzpagg/envevidence/releases/tag/v0.3.0-android-preview.1), transfer it to your Android phone and open it. Allow installation from that file source if Android asks. Requires Android 8.0+ with an up-to-date Android System WebView. This preview is distributed directly; it is not a Google Play listing.

1. Open **Settings → Load synthetic demo** for an offline example.
2. Create goals and steps, change task status, or write and pin notes. Changes save locally; archive/restore is available in each module.
3. In **Evidence**, create a project and select a text PDF with Android's file picker. Attach supplements to the correct paper. Inspect parsed pages before extracting.
4. Choose OpenAI or Anthropic, enter a supported structured-output model ID and your own API key, and explicitly confirm sending text. Keep the app open until the run finishes.
5. Review each condition/field against the parsed page and original paper. Record reviewer, reason, value, unit and quotes. Original model output is retained.
6. Export a project as JSON or CSV using Android's save dialog. Use **Settings → Export full backup** regularly.

Planning, PDF parsing, quote location checks and data saving work locally. Only an explicit extraction sends page text and field definitions to the selected provider's official API. API keys are held in memory for that run only and excluded from backups. There is no analytics, remote web UI, account sync or background notification. Provider fees and data policies apply; OpenAI requests set `store=false`, which is not a zero-retention guarantee.

## Data and compatibility

- Private app storage uses Android `AtomicFile` writes. Uninstalling removes it. Cloud backup is disabled; export your own backup first.
- Import accepts desktop project JSON, desktop workspace JSON or a full Android backup. New IDs are merged; existing IDs and current preferences are kept. This is additive import, not bidirectional sync.
- Exported project JSON retains the desktop schema, source pages and revision history. Desktop CLI and Python version remain 0.2.0.
- Completed papers are checkpointed and skipped on retry. An interrupted unfinished request may still have been billed by the provider.
- Main/supplement inputs are locked after the first run begins; create a new project to change extraction inputs.
- Text PDFs only, at most 30 MB / 250 pages, with a 1,000,000-character local parse cap and 160,000-character request cap per paper plus supplements. No silent truncation, OCR or chart reading.
- CSV and JSON export are available on Android. Excel export remains in the desktop app.
- A quote found on a page is **not** scientific verification. Check experiment identity, time, units and endpoint yourself. Pollutant removal and mineralization remain separate fields.

## Build and validation

Open this directory in Android Studio, or use JDK 17+, Gradle 8.13 and Android SDK 36 / build-tools 35.0.0:

```sh
cd android
./gradlew lintDebug testDebugUnitTest assembleDebug assembleRelease
cd ..
node --test android/tests/*.test.cjs
```

Start the commands above from the repository root; on Windows use `gradlew.bat` instead of `./gradlew`. The official Gradle 8.13 wrapper is included with a distribution checksum. The [Android workflow](../.github/workflows/android.yml) builds both a debug APK and an unsigned release APK, runs domain checks and an Android 15 emulator test. GitHub Releases provides a release APK signed locally with a stable private key. The Actions debug APK is only for testing; different runners can use different debug certificates.

For maintainers, `tools/SignApk.java` signs and verifies an unsigned release using Google's `com.android.tools.build:apksig:8.13.2`, a PKCS12 keystore with alias `envevidence` and `ENVEVIDENCE_SIGNING_PASSWORD`. Keep an offline backup of your signing key; future updates require the same identity. Signing material never goes into source control or the APK.

The UI is bundled HTML/CSS/JavaScript, displayed through `WebViewAssetLoader`; Java handles private storage, Android's file picker, PDFBox parsing and HTTPS. External resources and WebView navigation are blocked. Resource links open in the system browser. The browser preview is for interface QA only; native PDF/API features require the APK.

Live API calls, real-paper extraction accuracy and physical-device compatibility are not yet validated. Tests use invented redistributable PDFs and recorded output. See the workflow for actual build/device results rather than treating available test code as a pass.

## Licenses

App code and synthetic fixtures: MIT. AndroidX WebKit and PDFBox-Android: Apache-2.0. The PDFs under `app/src/main/assets` are copies of this repository's original synthetic examples. See [third-party notices](../THIRD_PARTY_NOTICES.md).
