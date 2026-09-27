# EnvEvidence 安卓版 · 0.3.0 预览版

[English](README.md) · [电脑版](../README.zh-CN.md)

独立安装、离线管理科研计划的 APK。手机无需安装 Python、启动 Streamlit 服务或注册新账号。提供中英文、四套预设与自定义配色、模块排序，以及学习清单、日期任务和便利贴。

## 安装与使用

下载[已签名的预览版 APK](https://github.com/gzpagg/envevidence/releases/tag/v0.3.0-android-preview.1)，传到安卓手机并打开；系统询问时，允许从该文件来源安装。需要 Android 8.0 或以上及较新的 Android System WebView。当前直接提供安装包，尚未上架 Google Play。

1. 在“设置 → 载入自制演示”体验离线示例。
2. 创建学习目标、增删与勾选步骤，修改任务状态，编辑与置顶便签。各模块可归档和恢复。
3. 在“文献证据”中新建项目，通过系统文件选择器导入文本型 PDF，给对应文献添加补充材料。提取前检查各页解析文本。
4. 选择 OpenAI 或 Anthropic，填写支持结构化输出的模型名称和自己的 API 密钥，确认发送文本后提取。完成前保持应用开启。
5. 核对实验、字段和原文，填写核验人、理由、数值、单位及出处。模型原始值会保留。
6. 使用系统保存对话框导出项目 JSON / CSV，并定期在设置中导出完整备份。

计划管理、PDF 解析、原文定位和保存都在手机本地完成。只有主动提取时，才把页面文本和字段定义发送到所选服务商的官方 API。密钥仅在本次调用期间保留，不写入备份。无遥测、远程网页界面、账号同步和后台通知。API 按服务商计费；OpenAI 使用 `store=false`，但这不等于零保留承诺。

## 数据与兼容

- 本地数据使用 Android `AtomicFile` 原子写入。卸载会删除本地数据。已关闭云备份，请自行导出备份。
- 可导入电脑版文献项目 JSON、工作台 JSON 和安卓完整备份。按 ID 合并新增记录，已有记录及当前偏好不覆盖；这不是双向同步。
- 导出的项目 JSON 保持原有 schema、页码和修订历史，电脑版 CLI 与 Python 包仍为 0.2.0。
- 每篇完成后保存；重试跳过已完成文献。中断请求仍可能已被服务商计费。
- 首次开始提取后锁定文献输入。更换文献或提取字段时请新建项目。
- 只支持文本型 PDF，每文件最多 30 MB / 250 页，本地解析最多 100 万字符；每篇含补充材料的 API 输入最多 16 万字符。不会静默截断，不做 OCR 或图表读数。
- 安卓导出 CSV 和 JSON；Excel 导出保留在电脑版。
- 原文定位成功不等于科研核验成功。实验归属、时间、单位、去除率与矿化率仍需人工确认。

## 构建和验证

使用 Android Studio 打开此目录，或配置 JDK 17+、Gradle 8.13、Android SDK 36 / build-tools 35.0.0。在仓库根目录执行：

```sh
cd android
./gradlew lintDebug testDebugUnitTest assembleDebug assembleRelease
cd ..
node --test android/tests/*.test.cjs
```

Windows 将 `./gradlew` 替换为 `gradlew.bat`。仓库已包含官方 Gradle 8.13 Wrapper 及分发校验值。[自动检查](../.github/workflows/android.yml)构建 debug APK 和未签名 release APK，运行数据规则测试及 Android 15 模拟器测试。GitHub Releases 提供使用本机固定私有密钥签名的 release APK；Actions 的 debug 包仅用于测试，不同构建机的证书可能不同。

维护者可使用 `tools/SignApk.java`、Google 官方 `com.android.tools.build:apksig:8.13.2`、别名为 `envevidence` 的 PKCS12 密钥库和环境变量 `ENVEVIDENCE_SIGNING_PASSWORD` 签名、核验 release APK。请离线备份签名密钥，以后升级必须使用同一身份。签名材料不进入源码仓库或 APK。

界面随 APK 打包，使用 WebView 展示；Java 负责本地存储、文件选择、PDFBox 解析和 HTTPS。外部资源和 WebView 导航被禁止，学习链接使用系统浏览器打开。浏览器预览仅用于界面检查，原生 PDF / API 功能须在 APK 中使用。

真实 API、真实论文准确性及实体手机兼容性尚未验证。测试只使用自制 PDF 和录制输出。构建与模拟器是否通过，以自动检查的实际结果为准。

代码和自制资料采用 MIT 许可；AndroidX WebKit、PDFBox-Android 采用 Apache-2.0，见[第三方声明](../THIRD_PARTY_NOTICES.md)。
