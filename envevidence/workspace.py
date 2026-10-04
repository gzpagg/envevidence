"""Local preferences, plus planning data kept from version 0.2.

Version 0.3 no longer shows learning goals, tasks or notes. Their models stay so an
existing state.json loads and saves without losing anything.
"""

import json
import os
import tempfile
from datetime import date
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
    palette: Literal["mineral", "clay", "forest", "ocean", "sand", "graphite", "custom"] = "mineral"
    accent: str = "#186B62"
    background: str = "#F4F7F6"
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


class WorkspaceStore:
    def __init__(self, root):
        self.path = Path(root) / "workspace" / "state.json"

    def load(self):
        if not self.path.exists():
            return Workspace()
        # An existing file that omitted preferences used the original forest defaults.
        # Only an absent workspace file adopts the new mineral palette.
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            if "preferences" not in raw:
                raw["preferences"] = {}
            if isinstance(raw["preferences"], dict):
                for key, value in {
                    "palette": "forest", "accent": "#147D73", "background": "#F6F8F7"
                }.items():
                    raw["preferences"].setdefault(key, value)
        return Workspace.model_validate(raw)

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


