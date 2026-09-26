# 发布说明

[English](PUBLISHING.md)

仅上传独立 EnvEvidence 项目至 https://github.com/gzpagg/envevidence，不上传上一级科研目录。

1. 检查全部变更，运行 python -m ruff check .、python -m pytest -q、离线演示和 python -m build。
2. 使用自制资料截取中英文界面，核查 README 链接与发布包内容。
3. 排除 data/、虚拟环境、.env、Streamlit secrets、缓存和凭据；源码 ZIP 采用显式白名单。
4. 同步版本与变更记录，保留 MIT 许可和示例来源说明。
5. 更新现有仓库，不强制推送或覆盖无关修改。核查最终提交及全部四项 CI。

python scripts/package_source.py 在 dist/ 生成源码 ZIP。构建产物在明确发布前仅保存在本地；项目尚未发布到 PyPI。GitHub 提供源码，不是已托管的多人服务。

真实 API 与真实论文准确性仍未核验；发布标签或模拟测试通过不能表述为科研验证通过。
