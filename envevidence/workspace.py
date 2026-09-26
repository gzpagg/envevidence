"""Local planning data, deliberately independent of scientific evidence snapshots."""

import os
import tempfile
from datetime import date, timedelta
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from pydantic import Field, field_validator, model_validator

from .models import StrictModel, now, uid

MODULES = ["evidence", "learning", "tasks", "notes"]


class Step(StrictModel):
    id: str = Field(default_factory=uid)
    title: str = Field(min_length=1, max_length=300)
    done: bool = False


class Item(StrictModel):
    id: str = Field(default_factory=uid)
    title: str = Field(min_length=1, max_length=300)
    archived: bool = False

    @field_validator("title")
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError("A title is required")
        return value.strip()


class LearningGoal(Item):
    description: str = Field(default="", max_length=20000)
    resources: list[str] = Field(default_factory=list)
    steps: list[Step] = Field(default_factory=list)

    @field_validator("resources")
    @classmethod
    def safe_links(cls, values):
        for value in values:
            parsed = urlparse(value)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise ValueError("Resource links must use http or https")
        return values

    @property
    def progress(self) -> float | None:
        return sum(s.done for s in self.steps) / len(self.steps) if self.steps else None


class DailyTask(Item):
    planned_date: date = Field(default_factory=date.today)
    priority: Literal["high", "normal", "low"] = "normal"
    status: Literal["todo", "doing", "done"] = "todo"


class Note(Item):
    body: str = Field(default="", max_length=20000)
    pinned: bool = False
    color: Literal["sage", "sky", "sand", "lavender"] = "sand"


class Preferences(StrictModel):
    language: Literal["en", "zh"] = "en"
    palette: Literal["forest", "ocean", "sand", "graphite", "custom"] = "forest"
    accent: str = "#147D73"
    background: str = "#F6F8F7"
    order: list[str] = Field(default_factory=lambda: MODULES.copy())
    hidden: list[str] = Field(default_factory=list)

    @field_validator("accent", "background")
    @classmethod
    def valid_color(cls, value):
        import re

        if not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
            raise ValueError("Expected a six-digit hex color")
        return value.upper()

    @model_validator(mode="after")
    def valid_modules(self):
        if sorted(self.order) != sorted(MODULES) or not set(self.hidden) <= set(MODULES):
            raise ValueError("Invalid module configuration")
        return self


class Workspace(StrictModel):
    schema_version: Literal[1] = 1
    updated_at: str = Field(default_factory=now)
    preferences: Preferences = Field(default_factory=Preferences)
    goals: list[LearningGoal] = Field(default_factory=list)
    tasks: list[DailyTask] = Field(default_factory=list)
    notes: list[Note] = Field(default_factory=list)
    demo_loaded: bool = False


def tasks_for_day(workspace, day):
    return [t for t in workspace.tasks if not t.archived and t.planned_date == day]


def overdue_tasks(workspace, day):
    return [
        t for t in workspace.tasks if not t.archived and t.planned_date < day and t.status != "done"
    ]


def task_progress(tasks):
    return sum(t.status == "done" for t in tasks) / len(tasks) if tasks else None


class WorkspaceStore:
    def __init__(self, root):
        self.path = Path(root) / "workspace" / "state.json"

    def load(self):
        if not self.path.exists():
            return Workspace()
        return Workspace.model_validate_json(self.path.read_text(encoding="utf-8"))

    def save(self, workspace):
        # Validate before writing; malformed files are never silently reset on load.
        Workspace.model_validate(workspace.model_dump())
        self.path.parent.mkdir(parents=True, exist_ok=True)
        workspace.updated_at = now()
        fd, name = tempfile.mkstemp(dir=self.path.parent, prefix=".save-", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(workspace.model_dump_json(indent=2))
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(name, self.path)
        finally:
            if os.path.exists(name):
                os.unlink(name)


def add_demo(workspace, language="en", today=None):
    """Append invented planning examples once, never replace the user's records."""
    if workspace.demo_loaded:
        return
    today = today or date.today()
    zh = language == "zh"
    workspace.goals.append(
        LearningGoal(
            title="示例 · 学习水处理反应动力学" if zh else "Demo · Learn water-treatment kinetics",
            description="自制演示目标，可自由修改。"
            if zh
            else "An invented learning plan. Make it your own.",
            resources=["https://docs.python.org/3/tutorial/"],
            steps=[
                Step(title=s, done=i == 0)
                for i, s in enumerate(
                    ["复习一级反应", "绘制衰减曲线", "比较处理条件"]
                    if zh
                    else [
                        "Review first-order reactions",
                        "Plot a decay curve",
                        "Compare treatment conditions",
                    ]
                )
            ],
        )
    )
    for i, title in enumerate(
        ["示例 · 整理阅读计划", "示例 · 核验 Trial A 的出处", "示例 · 整理实验笔记"]
        if zh
        else [
            "Demo · Outline the reading plan",
            "Demo · Verify the source for Trial A",
            "Demo · Organize lab notes",
        ]
    ):
        workspace.tasks.append(
            DailyTask(
                title=title,
                planned_date=today,
                status=["done", "doing", "todo"][i],
                priority="high" if i == 1 else "normal",
            )
        )
    workspace.tasks.append(
        DailyTask(
            title="示例 · 回顾待办事项" if zh else "Demo · Review pending work",
            planned_date=today - timedelta(days=1),
        )
    )
    workspace.notes.append(
        Note(
            title="示例 · 阅读提醒" if zh else "Demo · A reading reminder",
            pinned=True,
            color="sage",
            body="污染物去除率与 TOC 去除率应分别核验。"
            if zh
            else "Review pollutant removal and TOC removal separately. A located quote still needs scientific review.",
        )
    )
    workspace.demo_loaded = True
