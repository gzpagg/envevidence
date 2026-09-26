from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_offline_demo_review_save_and_reload(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVEVIDENCE_DATA_DIR", str(tmp_path))
    app = AppTest.from_file(
        str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=30
    ).run()
    assert not app.exception
    app.selectbox(key="locale").select("zh").run()
    app.button(key="nav_evidence").click().run()
    app.button(key="evidence_demo").click().run()
    assert not app.exception
    assert [m.value for m in app.metric] == ["1", "3", "27", "0"]
    next(s for s in app.selectbox if s.label == "核验状态").select("verified")
    next(t for t in app.text_area if t.label == "核验说明 / 修改理由").set_value(
        "Checked the synthetic source and condition."
    )
    next(b for b in app.button if b.label == "保存核验记录").click().run()
    assert not app.exception
    assert app.metric[3].value == "1"
    next(b for b in app.button if b.label == "新建提取项目").click().run()
    next(b for b in app.button if b.label == "打开项目").click().run()
    assert not app.exception
    assert app.metric[3].value == "1"
