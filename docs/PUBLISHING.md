# Publishing

Publish only the standalone EnvEvidence project directory to https://github.com/gzpagg/envevidence. Never upload the parent research workspace.

Before publishing:

1. Review the exact changed files and run `python -m ruff check .`, `python -m pytest -q`, the offline demo and `python -m build`.
2. Capture the English and Chinese interface using invented data. Check README links and source-package contents.
3. Keep `data/`, virtual environments, `.env`, Streamlit secrets, caches and credentials excluded. The source ZIP uses an explicit allow-list.
4. Update versions and CHANGELOG. Preserve the MIT license and synthetic-fixture provenance.
5. Push to the existing repository without force-pushing or overwriting unrelated work. Verify the exact commit and all four CI jobs.

`python scripts/package_source.py` produces a shareable source ZIP in `dist/`. Build artifacts are local until explicitly published; this project is not published on PyPI. The GitHub repository contains source code, not a hosted multi-user web service.

Live provider integration and real-paper accuracy are still unverified. Do not represent a release tag or passing mocked tests as scientific validation.
