# EnvBench 与 EnvEvidence

**为水处理研究准备的两个工具：在实验台记录反应过程，在电脑上整理文献证据。**

[English](README.md) · [安卓应用](android/README.zh-CN.md) · [体验演示](docs/DEMO.zh-CN.md) · [验证记录](docs/VALIDATION.zh-CN.md)

| 应用 | 使用场景 | 能够获得什么 |
|---|---|---|
| **EnvBench · 安卓** | 水与污水实验中的取样、淬灭和现象记录 | 多计时器、样品记录、水体基质、照片、浓度变化与 CSV 导出 |
| **EnvEvidence · 电脑** | 阅读和整理水处理文献 | 实验条件表、引用原文、页面位置与人工修订记录 |

两个应用均提供中英文界面、可保存的外观设置和本地数据存储。

## EnvBench：把一次反应实验记录完整

将取样计划、现场操作与分析结果放在同一次实验中。EnvBench 围绕高级氧化与 DOM 研究设计，提供 UV/PDS、UV/H₂O₂、臭氧、芬顿等工艺选项。

- **掌握取样节奏。** 醒目的倒计时展示下一取样点，计划时间与实际记录时间分别保存。
- **记录每个样品。** 保存淬灭剂、pH、温度、体积和简短说明，并为样品添加照片。字段标签区分实测值与沿用值。
- **保留水体背景。** 记录 DOC、UV₂₅₄、碱度、主要离子及其他基质信息，由 DOC 和 UV₂₅₄ 计算 SUVA₂₅₄。
- **查看浓度变化。** 粘贴带样品编号的 LC 峰面积或填写 C/C₀，核对导入预览，查看准一级拟合及 k_obs、95% 置信区间、t½ 和 R²。
- **导出实验资料。** 导出整洁的样品 CSV、单次实验 ZIP，或包含原始照片的完整备份。

秒表、倒计时、取样提醒与计数器可以并行使用；计时器数量没有固定上限。设置、语言、外观和备份入口集中在 **我的**。

<img src="docs/images/envbench-run-zh.png" alt="EnvBench 反应页与下一取样点" width="300"> <img src="docs/images/envbench-samples-zh.png" alt="EnvBench 样品记录与浓度变化" width="300">

**Android 8.0+ · 离线运行 · 无需账号**

安卓当前源码版本为 **0.6.1**，可下载的 APK 与升级方式见[安装说明](android/README.zh-CN.md)。在 **我的 → 载入实验演示** 中，可体验一组自制 UV/PDS 反应、样品与水质记录。

## EnvEvidence：让文献数值带着出处

导入论文与补充材料，提取实验条件，并在引用原文旁逐项核验。EnvEvidence 将模型原始值与人工修订一同保存，方便之后回查判断依据。

| 步骤 | 使用流程 |
|---|---|
| **导入** | 添加文本型 PDF，将补充材料关联到主文献，检查解析页面覆盖情况。 |
| **提取** | 使用水处理模板或自定义字段；OpenAI 和 Anthropic 适配器共用同一记录结构。 |
| **核验** | 对照引用原句与页面上下文，检查数值、单位和实验归属，保存核验人、理由与时间。 |
| **导出** | 下载长表 CSV、Excel 或包含原文和修订历史的完整项目 JSON。 |

污染物去除率与矿化／TOC 去除率分别记录。不同实验条件独立成行；每个关键字段均有出处位置或明确的缺失状态。

![EnvEvidence 中文原文核验界面](docs/images/review-zh.png)

### 安装电脑版

需要 **Python 3.11+**。克隆仓库并建立虚拟环境：

```bash
git clone https://github.com/gzpagg/envevidence.git
cd envevidence
python -m venv .venv
```

Windows PowerShell：

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m envevidence serve
```

macOS / Linux：

```bash
.venv/bin/python -m pip install -e .
.venv/bin/python -m envevidence serve
```

打开 <http://127.0.0.1:8501>，在侧栏选择“简体中文”。点击 **载入离线演示**，无需 API 密钥即可体验自制论文及补充材料。电脑版当前版本为 **0.3.0**。

### 提取自己的论文

1. 新建项目，选择 OpenAI 或 Anthropic，填写账户支持的模型 ID。
2. 导入主文献及补充材料，选择提取字段。
3. 在本机解析文件并检查页面覆盖情况。
4. 输入会话内使用的 API 密钥，或设置环境变量 `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`。确认要发送的文本后开始提取。
5. 核验提取字段，保存修订，再导出结果。

`OPENAI_MODEL` 与 `ANTHROPIC_MODEL` 可设置默认模型 ID。应用不会自动读取 `.env` 文件。自定义字段格式为 `英文键名 | 显示名称 | 提取说明 | 单位`，单位项可省略。

支持每份最多 30 MB、250 页的文本型 PDF。[演示指南](docs/DEMO.zh-CN.md)介绍核验流程，[验证记录](docs/VALIDATION.zh-CN.md)说明解析与模型评估的覆盖范围。

## 语言、外观与数据

切换语言会改变界面文字，保留论文原文、样品名称、模型结果和修订记录。安卓默认采用暖白与陶土色；电脑版提供森林绿、海洋蓝、暖灰橙、石墨紫及自定义配色。

EnvBench 将记录与照片保存在安卓应用私有目录。卸载或换机前，先导出完整 ZIP 备份。EnvEvidence 将项目与偏好保存在 `data/`，可通过 `ENVEVIDENCE_DATA_DIR` 指定其他本地目录；关闭应用后备份整个目录。兼容升级会保留早期版本的数据。

实验功能在本机运行。电脑版文献提取会将解析文本和字段说明发送到你选择的 API 服务，密钥不写入项目文件。运行数据与密钥已排除在仓库之外。

## 开发与文档

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
python -m ruff check .
python -m build
node --test android/tests/*.test.cjs
```

[安卓截图与检查](docs/ANDROID.md) · [样品 CSV](docs/BENCH_CSV.md) · [技术结构](docs/ARCHITECTURE.zh-CN.md) · [验证记录](docs/VALIDATION.zh-CN.md) · [更新日志](CHANGELOG.md)

可通过 Issue 模板提交可复现的问题。代码与自制合成示例采用 [MIT 许可](LICENSE)，组件许可见[第三方说明](THIRD_PARTY_NOTICES.md)。
