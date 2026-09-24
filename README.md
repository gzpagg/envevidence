# EnvEvidence

**把环境科学论文中的实验条件和结果整理成可核验的证据表，让每条记录都能回到原文。**

[English](README.en.md) · [演示与验收](docs/DEMO.md) · [技术说明](docs/ARCHITECTURE.md) · [验证状态](docs/VALIDATION.md)

EnvEvidence 是面向环境科研人员的本地应用。上传主文献与补充材料，选择提取字段，通过自己的 OpenAI 或 Claude API 提取，再逐项核对原文、修订、导出。内置完全离线的合成演示，无需 API 密钥。

![EnvEvidence 界面](docs/images/workspace.png)

## 已实现

- 批量导入文本型 PDF，补充材料显式关联主文献；保留 PDF 页码、文件哈希和解析警告。
- 按实验条件区分记录；水处理模板包含污染物、水体、浓度、工艺、剂量、pH、反应时间、污染物去除率、TOC/矿化指标。
- 支持自定义字段。OpenAI Responses API 与 Anthropic Messages API 共用结构化输出定义。
- 检查引用片段是否出现在指定页面；缺失、歧义、未定位或缺少单位时给出提示。
- 人工核验、修改值/单位/出处，保留模型原值与追加式修订历史。
- 每篇论文结束后原子保存。发生 API 故障时停止后续调用；重新打开项目可继续，已完成论文不重发。
- CSV、Excel（实验表、字段证据、修订、文档、运行记录）与完整 JSON 导出。

## 安装和启动

需要 Python 3.11 或更新版本。下载本仓库并进入项目目录。

**Windows PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m envevidence serve
```

**macOS / Linux**

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python -m envevidence serve
```

在浏览器打开 <http://127.0.0.1:8501>。点击 **载入离线演示**，无需注册或付费，即可核验、修订、导出。命令行也支持：

```bash
python -m envevidence demo --output data/demo
```

上述 `python` 指虚拟环境中的 Python；未激活环境时使用相应完整路径。

## 使用自己的论文

1. 点击“新建提取项目”，填写名称、服务商和模型 ID；模型必须在你的账户中可用并支持结构化输出。
2. 选择主文献和补充材料，逐个指定补充材料所属主文献；选择或添加字段。
3. 点击“解析并建立项目”。检查成功解析的页数、解析警告和本地文本。
4. 在“资料与提取”中输入 API 密钥，确认文本发送范围后开始提取。
5. 在“证据核验”中选择实验和字段，查看引用原句与整页上下文；填写核验人和说明，保存记录。
6. 在“导出与记录”下载结果。关闭应用后重新启动，仍可打开已保存项目。

密钥也可通过环境变量提供。`.env.example` 仅作说明，应用**不会自动读取 `.env` 文件**。不要把真实密钥写入仓库。

```powershell
$env:OPENAI_API_KEY = "你的密钥"
$env:OPENAI_MODEL = "你账户中可用的模型ID"
# 或：
$env:ANTHROPIC_API_KEY = "你的密钥"
$env:ANTHROPIC_MODEL = "你账户中可用的模型ID"
```

自定义字段每行使用 `英文键名 | 显示名称 | 提取说明 | unit`；第四项仅在需要单位时填写。

```text
temperature | 温度 | 本实验的反应温度 | unit
catalyst | 催化剂 | 催化剂名称和组成
```

命令行真实提取（需显式允许发送文本）：

```bash
python -m envevidence extract main.pdf --supplement supplement.pdf --provider openai --model YOUR_MODEL_ID --send-text --output data/my-study
```

如有跳过的页面，CLI 默认停止。检查后可加 `--allow-partial`。批量工作、恢复中断和人工核验使用界面。

## 科研边界和数据去向

**“原句已定位”只表示文字在指定页存在，不证明模型理解、实验归属或结论正确。**模型提取后所有字段均为待人工核验，不提供未经校准的置信概率。不要把已定位当作已验证。

- 第一版只解析文本型 PDF；不做 OCR、图像读数或自动单位换算。双栏、公式和复杂表格可能产生错误，需检查整页上下文和原 PDF。
- “未找到”仅针对已经导入并成功解析的资料，不能推出原论文未报告。
- 页码指 PDF 文件页序（从 1 开始），可能不同于期刊印刷页码。
- 每组主文献及补充材料上限为 160,000 字符；超限在发送前拒绝，不静默截断。模型上下文或输出上限仍可能更低。
- 单用户本地应用，不支持多用户协同；同一项目请勿在多个标签页同时修改。
- PDF 解析、字段核验、结果保存和导出均在本机完成。API 提取发送全部成功解析页面的文本及字段说明；不上传原 PDF。API 使用按服务商规则计费。
- OpenAI 请求使用 `store=false`；这不等于服务商承诺零保留。数据处理仍取决于用户账户与服务条款。
- 密钥仅保留在进程环境或当前界面会话，不写入项目。项目 JSON 包含解析原文、模型结果、模型名称、用量、核验人与修订记录。
- Excel 遇到超出单元格长度上限的内容会显式标记截断，完整内容保留在 JSON/CSV 中；不支持的控制字符以 Unicode 标记展示。
- 默认数据目录为启动位置下的 `data/`，可用 `ENVEVIDENCE_DATA_DIR` 改变。该目录被 Git 忽略，备份和分享前请检查内容。
- 没有遥测或自动上传功能，启动命令关闭 Streamlit 使用统计。应用监听 `127.0.0.1`。

## 开发与验证

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
python -m ruff check .
python -m build
```

合成案例生成脚本为 `scripts/build_demo.py`。测试覆盖实验分离、指标区别、补充材料、原文定位、缺少单位、人工修订、API 中断恢复、拒绝/截断响应以及表格公式注入防护。两家 API 使用模拟 HTTP 响应验证，真实 API 验证状态见 [VALIDATION](docs/VALIDATION.md)。

## 开源与后续方向

代码与自制合成示例采用 [MIT 许可](LICENSE)；第三方组件保留各自许可，详见 [THIRD_PARTY_NOTICES](THIRD_PARTY_NOTICES.md)。仓库不包含真实科研论文、个人实验数据或 API 密钥。

欢迎通过 Issue 提交可复现的错误案例，尤其是实验条件串行、错误单位、指标混淆或引用归属错误。请仅附可以公开分发的材料。

后续方向为本地 OCR/复杂表格解析、实验可比性检查、MCP 接口。它们尚未在 v0.1.0 实现。GitHub 发布说明见 [发布指南](docs/PUBLISHING.md)。
