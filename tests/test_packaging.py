import importlib.util
from pathlib import Path
from zipfile import ZipFile


def test_source_zip_excludes_local_data_and_streamlit_secrets(tmp_path):
    script = Path(__file__).resolve().parents[1] / "scripts" / "package_source.py"
    spec = importlib.util.spec_from_file_location("package_source", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ROOT = tmp_path
    for name in module.TOP_FILES:
        (tmp_path / name).write_text("public", encoding="utf-8")
    for folder in module.FOLDERS + ["data", ".venv"]:
        (tmp_path / folder).mkdir()
    (tmp_path / ".streamlit" / "config.toml").write_text("public", encoding="utf-8")
    (tmp_path / ".streamlit" / "secrets.toml").write_text("SECRET", encoding="utf-8")
    (tmp_path / ".env").write_text("SECRET", encoding="utf-8")
    (tmp_path / "data" / "paper.json").write_text("PRIVATE", encoding="utf-8")
    module.main()
    with ZipFile(tmp_path / "dist" / "envevidence-0.2.0-source.zip") as archive:
        assert not any(
            "secrets.toml" in p or "/data/" in p or p.endswith("/.env") for p in archive.namelist()
        )
        assert all(b"SECRET" not in archive.read(p) for p in archive.namelist())
