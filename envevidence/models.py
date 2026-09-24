from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


def uid() -> str:
    return uuid4().hex


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class FieldSpec(StrictModel):
    key: str = Field(pattern=r"^[a-z][a-z0-9_]{0,49}$")
    label: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=1000)
    requires_unit: bool = False


class Block(StrictModel):
    id: str
    page: int = Field(ge=1)
    text: str


class Document(StrictModel):
    id: str
    filename: str
    sha256: str
    role: Literal["main", "supplement"]
    page_count: int
    blocks: list[Block]
    warnings: list[str] = Field(default_factory=list)
    parser: str = "pypdf"


class Study(StrictModel):
    id: str = Field(default_factory=uid)
    name: str
    documents: list[Document]


class SourceRef(StrictModel):
    block_id: str
    quote: str


class RawField(StrictModel):
    key: str
    value: str | None
    unit: str | None
    status: Literal["found", "not_found", "unclear"]
    sources: list[SourceRef]


class RawExperiment(StrictModel):
    label: str
    fields: list[RawField]


class Extraction(StrictModel):
    experiments: list[RawExperiment]


class LocatedSource(StrictModel):
    block_id: str
    quote: str
    document_id: str | None = None
    filename: str | None = None
    page: int | None = None
    matched: bool = False


class Revision(StrictModel):
    timestamp: str = Field(default_factory=now)
    reviewer: str
    value: str | None
    unit: str | None
    status: Literal["pending", "verified", "rejected"]
    note: str
    sources: list[LocatedSource]


class EvidenceField(StrictModel):
    id: str = Field(default_factory=uid)
    key: str
    label: str
    original: RawField
    sources: list[LocatedSource]
    issues: list[str] = Field(default_factory=list)
    revisions: list[Revision] = Field(default_factory=list)

    @property
    def value(self) -> str | None:
        return self.revisions[-1].value if self.revisions else self.original.value

    @property
    def unit(self) -> str | None:
        return self.revisions[-1].unit if self.revisions else self.original.unit

    @property
    def review_status(self) -> str:
        return self.revisions[-1].status if self.revisions else "pending"

    @property
    def current_sources(self) -> list[LocatedSource]:
        return self.revisions[-1].sources if self.revisions else self.sources


class Experiment(StrictModel):
    id: str = Field(default_factory=uid)
    study_id: str
    label: str
    fields: list[EvidenceField]


class Run(StrictModel):
    study_id: str
    status: Literal["running", "completed", "failed"]
    started_at: str = Field(default_factory=now)
    finished_at: str | None = None
    error: str | None = None
    usage: dict[str, int] = Field(default_factory=dict)


class Project(StrictModel):
    schema_version: Literal[1] = 1
    id: str = Field(default_factory=uid)
    name: str
    created_at: str = Field(default_factory=now)
    updated_at: str = Field(default_factory=now)
    provider: Literal["demo", "openai", "anthropic"]
    model: str
    fields: list[FieldSpec]
    studies: list[Study]
    experiments: list[Experiment] = Field(default_factory=list)
    runs: list[Run] = Field(default_factory=list)
    prompt_version: str = "1.0"
