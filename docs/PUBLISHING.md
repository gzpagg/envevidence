# GitHub 发布

只发布这个独立项目目录。不要从上级科研目录执行整体上传；上级可能包含真实论文、数据和其他工作成果。

## 发布前

1. 阅读 `docs/VALIDATION.md`，如实区分离线测试、真实 API 测试与同行试用。
2. 确认作者署名、仓库名和 MIT 许可符合你的意愿及所在机构要求。
3. 检查待发布文件；`.env`、`.venv/`、`data/`、测试临时目录和密钥不得上传。
4. 保留自制合成 PDF 及许可声明，不添加未经许可的论文全文。
5. 运行测试、离线演示和构建；准备 README 截图和演示步骤。

## 在你选定的空仓库发布

创建 GitHub 仓库后，将下面的 `<YOUR_REPOSITORY_URL>` 替换为真实地址。在本项目根目录运行：

```bash
git init -b main
git add .
git status --short
git commit -m "Initial EnvEvidence 0.1.0"
git remote add origin <YOUR_REPOSITORY_URL>
git push -u origin main
```

如果目录已经初始化，跳过 `git init`；如果已有 remote，先检查地址。此处不覆盖任何已有远端仓库。

首次 CI 通过并完成一次真实 API 验证后，再创建 `v0.1.0` 标签及 GitHub Release。Release 说明应引用 CHANGELOG，并明确扫描件、复杂表格与人工核验的限制。Python 包构建并不意味着已经发布到 PyPI；不要在 README 声称可从 PyPI 安装，除非确实完成发布。

项目简介建议：**Source-linked environmental research evidence extraction and human review. Local-first, bring your own OpenAI/Anthropic API key.**

建议 topics：`environmental-science`、`evidence-extraction`、`research-tools`、`streamlit`、`openai`、`anthropic`。

