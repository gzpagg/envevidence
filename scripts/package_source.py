"""Build a shareable source ZIP from an explicit allow-list, never from the parent workspace."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
TOP_FILES = [
    "pyproject.toml",
    "MANIFEST.in",
    "README.md",
    "README.en.md",
    "README.zh-CN.md",
    "LICENSE",
    "CHANGELOG.md",
    "THIRD_PARTY_NOTICES.md",
    "requirements-lock.txt",
    ".gitignore",
    ".gitattributes",
    ".env.example",
    "app.py",
]
FOLDERS = ["envevidence", "tests", "scripts", "docs", ".github", ".streamlit"]
ALLOWED_SUFFIXES = {".py", ".md", ".png", ".pdf", ".json", ".toml", ".yml"}


def main():
    output = ROOT / "dist" / "envevidence-0.2.0-source.zip"
    output.parent.mkdir(exist_ok=True)
    files = [ROOT / name for name in TOP_FILES]
    for folder in FOLDERS:
        files.extend(
            p
            for p in (ROOT / folder).rglob("*")
            if p.is_file()
            and p.suffix in ALLOWED_SUFFIXES
            and "__pycache__" not in p.parts
            and p.name != "secrets.toml"
        )
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for file in sorted(files):
            if not file.is_file():
                raise FileNotFoundError(file)
            archive.write(file, Path("envevidence-0.2.0") / file.relative_to(ROOT))
    print(f"Source ZIP: {output.name}; {len(files)} files")


if __name__ == "__main__":
    main()
