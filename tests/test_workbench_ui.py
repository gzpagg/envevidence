from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from envevidence.workspace import LearningGoal, Note, Step, Workspace, WorkspaceStore

ENTRY = str(Path(__file__).resolve().parents[1] / "app.py")


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVEVIDENCE_DATA_DIR", str(tmp_path))
    return AppTest.from_file(ENTRY, default_timeout=30).run()


def find(elements, label):
    return next(e for e in elements if e.label == label)


def click(app, label):
    find(app.button, label).click().run()
    assert not app.exception


def test_opens_on_analysis_without_planning_modules(app):
    assert not app.exception
    assert app.header[0].value == "Experiment analysis"
    keys = {b.key for b in app.button}
    assert {"nav_analysis", "nav_evidence", "nav_settings"} <= keys
    assert not {"nav_home", "nav_learning", "nav_tasks", "nav_notes", "workspace_demo"} & keys


def test_language_and_themes_persist_and_keep_earlier_planning_data(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVEVIDENCE_DATA_DIR", str(tmp_path))
    store = WorkspaceStore(tmp_path)
    earlier = Workspace(
        goals=[LearningGoal(title="Kinetics", steps=[Step(title="Read", done=True)])],
        notes=[Note(title="Mine", body="Private", pinned=True)],
    )
    store.save(earlier)
    app = AppTest.from_file(ENTRY, default_timeout=30).run()
    assert any("2 learning goals, tasks and notes" in c.value for c in app.caption)
    app.button(key="nav_settings").click().run()
    for palette in ["glacier", "ocean", "sand", "graphite", "forest", "clay", "mineral", "custom"]:
        app.selectbox(key="palette_draft").select(palette).run()
        app.button(key="save_appearance").click().run()
        assert not app.exception
        assert store.load().preferences.palette == palette
    app.button(key="reset_colors").click().run()
    assert app.selectbox(key="palette_draft").value == "glacier"
    app.selectbox(key="locale").select("zh").run()
    assert store.load().preferences.language == "zh"
    assert not app.exception
    fresh = AppTest.from_file(ENTRY).run()
    assert fresh.selectbox(key="locale").value == "zh"
    saved = store.load()
    assert saved.goals == earlier.goals and saved.notes == earlier.notes


def test_english_evidence_review_and_locale_preserve_value(app):
    app.button(key="nav_evidence").click().run()
    app.button(key="evidence_demo").click().run()
    find(app.selectbox, "Review status").select("verified")
    find(app.text_area, "Review note / reason").set_value("Checked against Trial A source.")
    click(app, "Save review")
    assert app.metric[3].value == "1"
    app.selectbox(key="locale").select("zh").run()
    assert find(app.selectbox, "核验状态").value == "verified"
    app.selectbox(key="locale").select("en").run()
    assert app.metric[3].value == "1"
    assert not app.exception




def test_material_preferences_persist_across_restart_and_reset(app, tmp_path):
    app.button(key="nav_settings").click().run()
    app.radio(key="visual_style_draft").set_value("solid")
    app.checkbox(key="reduce_transparency_draft").check().run()
    app.button(key="save_appearance").click().run()
    assert not app.exception
    prefs = WorkspaceStore(tmp_path).load().preferences
    assert prefs.visual_style == "solid" and prefs.reduce_transparency
    restarted = AppTest.from_file(ENTRY, default_timeout=30).run()
    restarted.button(key="nav_settings").click().run()
    assert restarted.radio(key="visual_style_draft").value == "solid"
    assert restarted.checkbox(key="reduce_transparency_draft").value
    restarted.button(key="reset_colors").click().run()
    restored = WorkspaceStore(tmp_path).load().preferences
    assert restored.palette == "glacier" and restored.visual_style == "glass"
    assert not restored.reduce_transparency
    assert restarted.selectbox(key="palette_draft").value == "glacier"
    assert restarted.radio(key="visual_style_draft").value == "glass"
    assert not restarted.checkbox(key="reduce_transparency_draft").value
