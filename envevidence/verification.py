import re
import unicodedata

from .models import (
    EvidenceField,
    Experiment,
    Extraction,
    FieldSpec,
    LocatedSource,
    RawField,
    Revision,
    SourceRef,
    Study,
)


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text)).strip()


def locate(sources: list[SourceRef], study: Study) -> list[LocatedSource]:
    lookup = {b.id: (d, b) for d in study.documents for b in d.blocks}
    output = []
    for source in sources:
        item = LocatedSource(block_id=source.block_id, quote=source.quote)
        if source.block_id in lookup:
            doc, block = lookup[source.block_id]
            item.document_id, item.filename, item.page = doc.id, doc.filename, block.page
            quote = normalize(source.quote)
            item.matched = bool(quote) and quote in normalize(block.text)
        output.append(item)
    return output


def validate_extraction(raw: Extraction, study: Study, specs: list[FieldSpec]) -> list[Experiment]:
    keys = {s.key for s in specs}
    output = []
    for experiment in raw.experiments:
        field_keys = [f.key for f in experiment.fields]
        if len(set(field_keys)) != len(field_keys) or set(field_keys) != keys:
            raise ValueError("模型返回了重复、未知或缺失字段，结果未保存。")
        by_key = {f.key: f for f in experiment.fields}
        fields = []
        for spec in specs:
            f = by_key.get(spec.key) or RawField(
                key=spec.key, value=None, unit=None, status="not_found", sources=[]
            )
            sources = locate(f.sources, study)
            issues = []
            if f.status == "not_found":
                issues.append("在已导入且成功解析的资料中未找到；不代表论文没有报告。")
                if f.value is not None or f.unit is not None or f.sources:
                    raise ValueError("未找到的字段包含数值或出处，返回结果不一致。")
            else:
                if not sources or not all(s.matched for s in sources):
                    issues.append("原文定位未通过，请核对来源。")
                if not f.value:
                    issues.append("字段有标记但没有可用值。")
                if spec.requires_unit and not f.unit:
                    issues.append("缺少单位，不执行自动推断或换算。")
                if f.status == "unclear":
                    issues.append("上下文存在歧义，需人工判断。")
            fields.append(
                EvidenceField(
                    key=spec.key, label=spec.label, original=f, sources=sources, issues=issues
                )
            )
        output.append(Experiment(study_id=study.id, label=experiment.label, fields=fields))
    return output


def revise_field(
    field: EvidenceField,
    study: Study,
    *,
    value: str | None,
    unit: str | None,
    status: str,
    note: str,
    reviewer: str,
    sources: list[SourceRef],
) -> None:
    if not note.strip() or not reviewer.strip():
        raise ValueError("请填写核验人和修订理由。")
    located = locate(sources, study)
    if status == "verified" and (not value or not located or not all(s.matched for s in located)):
        raise ValueError("确认字段前，需要非空值和能定位的原文出处。")
    field.revisions.append(
        Revision(
            value=value,
            unit=unit,
            status=status,
            note=note.strip(),
            reviewer=reviewer.strip(),
            sources=located,
        )
    )
