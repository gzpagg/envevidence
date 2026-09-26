from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from envevidence.workspace import WorkspaceStore

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


def test_learning_crud_and_restart(app, tmp_path):
    app.button(key="nav_learning").click().run()
    app.text_input(key="new_goal_title").set_value("My kinetics plan")
    click(app, "Create goal")
    app.text_input(key="new_step_title").set_value("Read chapter one")
    click(app, "Add step")
    find(app.checkbox, "Read chapter one").check().run()
    find(app.text_input, "Step title").set_value("Summarize chapter one")
    click(app, "Save step")
    store = WorkspaceStore(tmp_path)
    assert store.load().goals[0].progress == 1
    assert store.load().goals[0].steps[0].title == "Summarize chapter one"
    click(app, "Archive")
    assert store.load().goals[0].archived
    app.toggle(key="archived_goals").set_value(True).run()
    click(app, "Restore")
    app.toggle(key="archived_goals").set_value(False).run()
    click(app, "Remove step")
    assert store.load().goals[0].progress is None
    fresh = AppTest.from_file(ENTRY).run()
    fresh.button(key="nav_learning").click().run()
    assert find(fresh.text_input, "Title").value == "My kinetics plan"


def test_task_reopen_and_note_edit_archive(app, tmp_path):
    app.button(key="nav_tasks").click().run()
    app.text_input(key="new_task_title").set_value("Review results")
    click(app, "Create task")
    find(app.selectbox, "Status").select("done")
    click(app, "Save task")
    assert WorkspaceStore(tmp_path).load().tasks[0].status == "done"
    find(app.selectbox, "Status").select("todo")
    click(app, "Save task")
    assert WorkspaceStore(tmp_path).load().tasks[0].status == "todo"
    app.button(key="nav_notes").click().run()
    app.text_input(key="new_note_title").set_value("A useful reminder")
    app.text_area(key="new_note_body").set_value("Keep raw data.")
    click(app, "Create note")
    find(app.checkbox, "Pin to top").check()
    find(app.selectbox, "Note color").select("lavender")
    find(app.text_input, "Title").set_value("Keep original data")
    click(app, "Save note")
    note = WorkspaceStore(tmp_path).load().notes[0]
    assert note.pinned and note.color == "lavender" and note.title == "Keep original data"
    click(app, "Archive")
    app.toggle(key="archived_notes").set_value(True).run()
    click(app, "Restore")
    assert not WorkspaceStore(tmp_path).load().notes[0].archived


def test_language_themes_layout_demo_and_restart(app, tmp_path):
    app.button(key="workspace_demo").click().run()
    before = WorkspaceStore(tmp_path).load()
    assert before.demo_loaded and len(before.goals) == 1
    assert app.button(key="workspace_demo").disabled
    app.button(key="nav_settings").click().run()
    for palette in ["ocean", "sand", "graphite", "forest", "custom"]:
        app.selectbox(key="palette_draft").select(palette).run()
        app.button(key="save_appearance").click().run()
        assert not app.exception
        assert WorkspaceStore(tmp_path).load().preferences.palette == palette
    app.button(key="reset_colors").click().run()
    assert app.selectbox(key="palette_draft").value == "forest"
    app.checkbox(key="visible_notes").uncheck().run()
    app.button(key="up_tasks").click().run()
    saved = WorkspaceStore(tmp_path).load()
    assert "notes" in saved.preferences.hidden
    assert saved.preferences.order == ["evidence", "tasks", "learning", "notes"]
    assert saved.notes == before.notes
    app.button(key="reset_layout").click().run()
    assert app.checkbox(key="visible_notes").value
    app.selectbox(key="locale").select("zh").run()
    assert WorkspaceStore(tmp_path).load().preferences.language == "zh"
    assert not app.exception
    fresh = AppTest.from_file(ENTRY).run()
    assert fresh.selectbox(key="locale").value == "zh"
    assert WorkspaceStore(tmp_path).load().notes == before.notes


def test_all_modules_hidden_keeps_settings(app, tmp_path):
    app.button(key="workspace_demo").click().run()
    before = WorkspaceStore(tmp_path).load()
    app.button(key="nav_settings").click().run()
    for module in ["evidence", "learning", "tasks", "notes"]:
        app.checkbox(key=f"visible_{module}").uncheck().run()
    app.button(key="nav_home").click().run()
    assert any("All modules are hidden" in x.value for x in app.info)
    assert app.button(key="nav_settings")
    assert WorkspaceStore(tmp_path).load().goals == before.goals
    assert not app.exception


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
