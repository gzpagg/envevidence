import json
import os
import re
import tempfile
from pathlib import Path

from .models import Project, now


class ProjectStore:
    """One atomic JSON snapshot per local project, including source text and audit history."""

    def __init__(self, root: str | Path = "data"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def path(self, project_id: str) -> Path:
        if not re.fullmatch(r"[a-f0-9]{32}", project_id):
            raise ValueError("Invalid project id")
        return self.root / f"{project_id}.json"

    def save(self, project: Project) -> Path:
        target = self.path(project.id)
        project.updated_at = now()
        fd, name = tempfile.mkstemp(dir=self.root, prefix=".save-", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(project.model_dump_json(indent=2))
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(name, target)
        finally:
            if os.path.exists(name):
                os.unlink(name)
        return target

    def load(self, project_id: str) -> Project:
        return Project.model_validate_json(self.path(project_id).read_text(encoding="utf-8"))

    def list_projects(self) -> list[dict]:
        items = []
        for path in self.root.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if path == self.path(data["id"]):
                    items.append({k: data[k] for k in ("id", "name", "updated_at")})
            except (ValueError, KeyError, OSError):
                continue
        return sorted(items, key=lambda item: item["updated_at"], reverse=True)
