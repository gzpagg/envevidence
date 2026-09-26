from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from envevidence.i18n import LANGUAGE, field_label, tr
from envevidence.themes import PALETTES, colors, contrast
from envevidence.workspace import (
    DailyTask,
    LearningGoal,
    Note,
    Preferences,
    Step,
    Workspace,
    WorkspaceStore,
    add_demo,
    overdue_tasks,
    task_progress,
    tasks_for_day,
)


def test_goal_progress_and_resource_validation():
    goal = LearningGoal(title="Science")
    assert goal.progress is None
    goal.steps = [Step(title="A", done=True), Step(title="B")]
    assert goal.progress == 0.5
    goal.steps.pop()
    assert goal.progress == 1
    with pytest.raises(ValidationError):
        LearningGoal(title="  ")
    with pytest.raises(ValidationError):
        LearningGoal(title="Bad link", resources=["javascript:alert(1)"])


def test_task_dates_overdue_reopen_and_archive():
    today = date(2026, 9, 26)
    current = DailyTask(title="Today", planned_date=today, status="done")
    prior = DailyTask(title="Prior", planned_date=today - timedelta(days=1))
    future = DailyTask(title="Future", planned_date=today + timedelta(days=1))
    ws = Workspace(tasks=[current, prior, future])
    assert task_progress(tasks_for_day(ws, today)) == 1
    assert overdue_tasks(ws, today) == [prior]
    prior.status = "done"
    assert not overdue_tasks(ws, today)
    prior.status = "todo"
    prior.archived = True
    assert not overdue_tasks(ws, today)
    current.archived = True
    assert task_progress(tasks_for_day(ws, today)) is None
    assert prior.planned_date == today - timedelta(days=1)


def test_atomic_roundtrip_and_failed_save_preserves_file(tmp_path, monkeypatch):
    store = WorkspaceStore(tmp_path)
    ws = store.load()
    ws.notes.append(Note(title="研究笔记", body="85% ≠ 20%", pinned=True))
    store.save(ws)
    before = store.path.read_bytes()
    assert store.load() == ws

    def fail(*args):
        raise OSError("simulated disk failure")

    monkeypatch.setattr("envevidence.workspace.os.replace", fail)
    ws.notes[0].body = "changed"
    with pytest.raises(OSError):
        store.save(ws)
    assert store.path.read_bytes() == before
    assert not list(store.path.parent.glob("*.tmp"))


def test_corrupt_workspace_not_overwritten(tmp_path):
    store = WorkspaceStore(tmp_path)
    store.path.parent.mkdir(parents=True)
    store.path.write_text("invalid", encoding="utf-8")
    with pytest.raises(ValueError):
        store.load()
    assert store.path.read_text() == "invalid"


def test_demo_appends_once_without_changing_existing_data():
    ws = Workspace(notes=[Note(title="Mine", body="Private")])
    original = ws.notes[0].model_copy(deep=True)
    add_demo(ws)
    snapshot = ws.model_dump()
    add_demo(ws)
    assert ws.model_dump() == snapshot
    assert ws.notes[0] == original


@pytest.mark.parametrize("palette", list(PALETTES) + ["custom"])
def test_theme_foregrounds_are_readable(palette):
    c = colors(Preferences(palette=palette, accent="#FFFF00", background="#001122"))
    assert contrast(c["accent"], c["on_accent"]) >= 4.5
    assert contrast(c["background"], c["text"]) >= 4.5


def test_preferences_validate_color_and_module_order():
    with pytest.raises(ValidationError):
        Preferences(accent="red; background:url(https://invalid.example)")
    with pytest.raises(ValidationError):
        Preferences(order=["evidence", "evidence", "tasks", "notes"])


def test_legacy_diagnostics_display_without_mutation():
    token = LANGUAGE.set("en")
    try:
        assert tr("第 2 页解析失败，未参与提取。") == "Page 2 failed to parse and was excluded."
        assert tr("缺少单位，不执行自动推断或换算。").startswith("Missing unit")
        assert field_label("pollutant", "污染物") == "Pollutant"
        assert field_label("pollutant", "My custom label") == "My custom label"
    finally:
        LANGUAGE.reset(token)
