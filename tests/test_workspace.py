from datetime import date

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
)


def test_version_02_planning_data_loads_and_saves_unchanged(tmp_path):
    store = WorkspaceStore(tmp_path)
    earlier = Workspace(
        goals=[
            LearningGoal(
                title="Science",
                resources=["https://example.org"],
                steps=[Step(title="A", done=True)],
            )
        ],
        tasks=[
            DailyTask(
                title="Prior", planned_date=date(2026, 9, 25), status="doing", priority="high"
            )
        ],
        notes=[Note(title="Mine", body="Private", pinned=True, color="lavender")],
        demo_loaded=True,
    )
    store.save(earlier)
    loaded = store.load()
    loaded.preferences.language = "zh"
    store.save(loaded)
    again = store.load()
    assert (again.goals, again.tasks, again.notes) == (earlier.goals, earlier.tasks, earlier.notes)
    assert again.demo_loaded and again.preferences.language == "zh"
    with pytest.raises(ValidationError):
        LearningGoal(title="  ")
    with pytest.raises(ValidationError):
        LearningGoal(title="Bad link", resources=["javascript:alert(1)"])


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
