"""Recorded synthetic fixture; never presented as a live LLM extraction."""

import json
from importlib.resources import files

from .models import Extraction, Project, Study
from .parsing import parse_pdf
from .providers import ProviderError, ProviderResult
from .templates import water_treatment_fields


def assets():
    return files("envevidence").joinpath("assets")


def demo_project() -> Project:
    docs = [
        parse_pdf(assets().joinpath(name).read_bytes(), name, role)
        for name, role in [
            ("synthetic_main.pdf", "main"),
            ("synthetic_supplement.pdf", "supplement"),
        ]
    ]
    return Project(
        name="示例 · 水处理实验的证据核验",
        provider="demo",
        model="recorded-fixture-v1",
        fields=water_treatment_fields(),
        studies=[Study(name="Synthetic water-treatment study", documents=docs)],
    )


class DemoProvider:
    def extract(self, study, fields):
        expected = demo_project().studies[0]
        if {d.sha256 for d in study.documents} != {d.sha256 for d in expected.documents}:
            raise ProviderError("离线演示仅支持附带的合成资料；真实论文请选择 API 提取。")
        raw = json.loads(assets().joinpath("recorded_extraction.json").read_text(encoding="utf-8"))
        by_role = {d.role: d for d in study.documents}
        selected = {f.key for f in fields}
        for exp in raw["experiments"]:
            exp["fields"] = [f for f in exp["fields"] if f["key"] in selected]
            for field in exp["fields"]:
                for source in field["sources"]:
                    role, page = source["block_id"].split(":")
                    source["block_id"] = f"{by_role[role].id}:{page}"
        return ProviderResult(
            Extraction.model_validate(raw), {"input_tokens": 0, "output_tokens": 0}
        )
