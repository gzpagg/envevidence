from __future__ import annotations

import os
from pathlib import Path

import streamlit as st
from pydantic import ValidationError

from envevidence.demo import DemoProvider, assets, demo_project
from envevidence.exporting import csv_bytes, evidence_rows, xlsx_bytes
from envevidence.i18n import field_label, fixed_format, state_label, t, tr
from envevidence.models import FieldSpec, Project, SourceRef, Study
from envevidence.parsing import ParseError, parse_pdf
from envevidence.pipeline import run_project
from envevidence.providers import APIProvider, ProviderError, input_text
from envevidence.templates import water_treatment_fields
from envevidence.verification import revise_field


def evidence_page(store):
    st.header(t("Literature evidence", "文献证据"))
    left, right = st.columns(2)
    if left.button(tr("新建提取项目"), key="evidence_new", width="stretch"):
        st.session_state.pop("project", None)
        st.rerun()
    if right.button(tr("载入离线演示"), key="evidence_demo", width="stretch"):
        project = demo_project()
        project.name = t("Demo · Water-treatment evidence", "示例 · 水处理实验的证据核验")
        run_project(project, store, DemoProvider())
        st.session_state.project = project
        st.rerun()
    projects = store.list_projects()
    if projects:
        labels = {p["id"]: p["name"] for p in projects}
        chosen = st.selectbox(
            tr("已保存的项目"),
            list(labels),
            format_func=fixed_format(labels.get),
            key="saved_project",
        )
        if st.button(tr("打开项目"), key="open_evidence"):
            try:
                st.session_state.project = store.load(chosen)
                st.rerun()
            except (ValueError, OSError):
                st.error(tr("项目无法读取或版本不兼容。原文件未修改。"))
    project = st.session_state.get("project")
    if project is None:
        new_project(store)
        return
    st.subheader(project.name)
    fields = [f for exp in project.experiments for f in exp.fields]
    for column, label, value in zip(
        st.columns(4),
        [
            t("Studies", "研究"),
            t("Experiments", "实验条件"),
            t("Fields", "证据字段"),
            t("Reviewed", "人工确认"),
        ],
        [
            len(project.studies),
            len(project.experiments),
            len(fields),
            sum((f.review_status == "verified" for f in fields)),
        ],
    ):
        column.metric(label, value)
    if project.provider == "demo":
        st.caption(
            t(
                "Synthetic demo · Recorded results · No API usage",
                "合成演示 · 预录结果 · 不消耗 API 额度",
            )
        )
    if project.runs and project.runs[-1].status == "failed":
        st.error(tr(project.runs[-1].error))
    tabs = st.tabs([tr("资料与提取"), tr("证据核验"), tr("导出与记录")])
    with tabs[0]:
        extract_panel(project, store)
    with tabs[1]:
        review_panel(project, store)
    with tabs[2]:
        export_panel(project)


def new_project(store):
    st.subheader(tr("从一组论文开始"))
    st.write(tr("每篇主文献建立独立研究记录，补充材料显式关联。先在本地解析，再决定是否发送模型。"))
    left, right = st.columns([1.3, 1], gap="large")
    with left:
        name = st.text_input(tr("项目名称"), value=tr("我的文献证据表"))
        mains = st.file_uploader(
            tr("主文献 PDF（可多选）"), type=["pdf"], accept_multiple_files=True, key="mains"
        )
        supplements = st.file_uploader(
            tr("补充材料 PDF（可选）"), type=["pdf"], accept_multiple_files=True, key="supplements"
        )
        assignments = {}
        if mains:
            for i, supplement in enumerate(supplements):
                assignments[i] = st.selectbox(
                    tr(f"{supplement.name} 属于哪篇主文献？"),
                    range(len(mains)),
                    format_func=fixed_format(lambda n: mains[n].name),
                    key=f"assign_{i}",
                )
        st.caption(
            tr(
                "支持文本型 PDF，每份最多 30 MB / 250 页。扫描页、图片和复杂表格可能无法解析，会明确提示。"
            )
        )
    with right:
        provider = st.selectbox(
            tr("模型服务"),
            ["openai", "anthropic"],
            format_func=fixed_format(lambda x: "OpenAI" if x == "openai" else "Claude / Anthropic"),
        )
        model_env = "OPENAI_MODEL" if provider == "openai" else "ANTHROPIC_MODEL"
        model = st.text_input(
            tr("模型名称"),
            value=os.getenv(model_env, ""),
            help=tr("填写你账户中可用且支持结构化输出的模型 ID。"),
        )
        defaults = water_treatment_fields()
        chosen = st.multiselect(
            tr("水处理字段模板"),
            [f.key for f in defaults],
            default=[f.key for f in defaults],
            format_func=fixed_format(
                lambda key: next((field_label(f.key, f.label) for f in defaults if f.key == key))
            ),
        )
        custom = st.text_area(
            tr("自定义字段（可选）"),
            placeholder=tr(
                "temperature | 温度 | 本实验的反应温度 | unit\ncatalyst | 催化剂 | 催化剂名称和组成"
            ),
            help=tr("每行：英文键名 | 中文名称 | 提取说明 | unit（需要单位时填写）"),
        )
    if st.button(tr("解析并建立项目"), type="primary", disabled=not mains):
        try:
            specs = [f for f in defaults if f.key in chosen]
            for line in custom.splitlines():
                if not line.strip():
                    continue
                parts = [p.strip() for p in line.split("|")]
                if len(parts) not in (3, 4) or (len(parts) == 4 and parts[3] != "unit"):
                    raise ValueError(
                        tr("自定义字段格式：key | 名称 | 说明 | unit（第四项可省略）。")
                    )
                specs.append(
                    FieldSpec(
                        key=parts[0],
                        label=parts[1],
                        description=parts[2],
                        requires_unit=len(parts) == 4,
                    )
                )
            if not specs or len({f.key for f in specs}) != len(specs):
                raise ValueError(tr("请选择字段，并确保英文键名不重复。"))
            if not name.strip() or not model.strip():
                raise ValueError(tr("请填写项目名称和模型名称；创建项目时不调用 API。"))
            studies, seen = ([], set())
            with st.spinner(tr("正在本地解析 PDF…")):
                for i, main in enumerate(mains):
                    documents = [parse_pdf(main.getvalue(), main.name)]
                    documents.extend(
                        (
                            parse_pdf(s.getvalue(), s.name, "supplement")
                            for j, s in enumerate(supplements)
                            if assignments[j] == i
                        )
                    )
                    for doc in documents:
                        if doc.sha256 in seen:
                            raise ValueError(tr("检测到重复 PDF，请移除重复文件后重试。"))
                        seen.add(doc.sha256)
                    studies.append(Study(name=Path(main.name).stem, documents=documents))
            project = Project(
                name=name.strip(),
                provider=provider,
                model=model.strip(),
                fields=specs,
                studies=studies,
            )
            store.save(project)
            st.session_state.project = project
            st.rerun()
        except ValidationError:
            st.error(
                t(
                    "Invalid project or custom field. Use a unique lowercase key (letters, digits "
                    "and underscores), and provide a name and extraction instructions.",
                    "项目或自定义字段不符合格式。请使用不重复的小写英文键名（字母、数字和下划线），"
                    "并填写名称和提取说明。",
                )
            )
        except (ValueError, ParseError) as exc:
            st.error(tr(str(exc)))


def extract_panel(project, store):
    st.subheader(tr("资料与提取"))
    documents = [d for s in project.studies for d in s.documents]
    st.dataframe(
        [
            {
                tr("研究"): s.name,
                tr("文件"): d.filename,
                tr("类型"): tr("主文献") if d.role == "main" else tr("补充材料"),
                tr("PDF 页数"): d.page_count,
                tr("已解析页"): len(d.blocks),
                tr("提示"): "; ".join((tr(w) for w in d.warnings)),
            }
            for s in project.studies
            for d in s.documents
        ],
        hide_index=True,
        width="stretch",
    )
    for d in documents:
        for warning in d.warnings:
            st.warning(f"{d.filename}：{tr(warning)}")
    with st.expander(tr("查看本地解析文本与页码")):
        doc = st.selectbox(
            tr("来源文件"),
            documents,
            format_func=fixed_format(lambda d: d.filename),
            key=f"doc_{project.id}",
        )
        block = st.selectbox(
            tr("PDF 页码"),
            doc.blocks,
            format_func=fixed_format(lambda b: str(b.page)),
            key=f"page_{doc.id}",
        )
        st.text(block.text)
    if project.provider == "demo":
        st.info(tr("这是预录的合成案例，用于演示与回归测试，未调用模型，也不是实际研究结果。"))
        c1, c2 = st.columns(2)
        c1.download_button(
            tr("下载示例主文献"),
            assets().joinpath("synthetic_main.pdf").read_bytes(),
            "synthetic_main.pdf",
        )
        c2.download_button(
            tr("下载示例补充材料"),
            assets().joinpath("synthetic_supplement.pdf").read_bytes(),
            "synthetic_supplement.pdf",
        )
        return
    completed = {r.study_id for r in project.runs if r.status == "completed"}
    pending = [s for s in project.studies if s.id not in completed]
    st.caption(
        tr(
            f"服务：{project.provider} · 模型：{project.model} · 待提取：{len(pending)} 篇。已完成的论文不会重复发送。"
        )
    )
    if not pending:
        st.success(tr("本项目提取已完成，请到证据核验中检查结果。"))
        return
    for study in pending:
        try:
            text = input_text(study, project.fields)
            st.caption(
                tr(
                    f"{study.name}：待发送约 {len(text):,} 字符（非 token 数；费用以服务商账单为准）。"
                )
            )
        except ProviderError as exc:
            st.error(tr(str(exc)))
            return
    env_key = "OPENAI_API_KEY" if project.provider == "openai" else "ANTHROPIC_API_KEY"
    key = st.text_input(
        tr("API 密钥（仅本次会话）"),
        type="password",
        key=f"api_{project.provider}",
        help=tr(f"也可配置本机环境变量 {env_key}。不会写入项目或日志。"),
    ) or os.getenv(env_key, "")
    consent = st.checkbox(
        tr(f"我同意将这些已解析文本发送至 {project.provider}，并使用自己的 API 额度。"),
        key=f"consent_{project.id}",
    )
    allow_partial = True
    if any((d.warnings for d in documents)):
        allow_partial = st.checkbox(
            tr("我已检查缺失页面，接受仅提取成功解析的页面。"), key=f"partial_{project.id}"
        )
    if st.button(
        tr("开始 / 继续提取"), type="primary", disabled=not (key and consent and allow_partial)
    ):
        progress = st.progress(0, text=tr("准备提取…"))
        provider = APIProvider(project.provider, project.model, key)
        run_project(
            project,
            store,
            provider,
            lambda n, total, label: progress.progress(n / total, text=f"{n}/{total} · {label}"),
        )
        st.session_state.project = project
        st.rerun()


def review_panel(project, store):
    st.subheader(tr("证据核验"))
    st.caption(tr("自动检查原句是否存在。人工核验还需确认数值、单位、处理条件与指标对应。"))
    if not project.experiments:
        st.info(tr("尚无实验记录。先完成提取；已完成但没有记录的论文可在运行记录中查看。"))
        return
    rows = evidence_rows(project)
    st.dataframe(
        [
            {
                tr("实验"): r["experiment"],
                tr("字段"): field_label(r["field"], r["label"]),
                tr("当前值"): r["value"],
                tr("单位"): r["unit"],
                tr("出处"): tr("已定位") if r["source_located"] else tr("未定位 / 未找到"),
                tr("人工核验"): state_label(r["human_review"]),
            }
            for r in rows
        ],
        hide_index=True,
        width="stretch",
        height=260,
    )
    study_names = {s.id: s.name for s in project.studies}
    experiments_by_id = {e.id: e for e in project.experiments}
    experiment_id = st.selectbox(
        tr("选择实验条件"),
        list(experiments_by_id),
        format_func=fixed_format(
            lambda eid: (
                f"{study_names[experiments_by_id[eid].study_id]} / {experiments_by_id[eid].label}"
            )
        ),
        key=f"exp_{project.id}",
    )
    experiment = experiments_by_id[experiment_id]
    fields_by_id = {f.id: f for f in experiment.fields}
    field_id = st.selectbox(
        tr("选择字段"),
        list(fields_by_id),
        format_func=fixed_format(
            lambda fid: field_label(fields_by_id[fid].key, fields_by_id[fid].label)
        ),
        key=f"field_{experiment.id}",
    )
    field = fields_by_id[field_id]
    study = next((s for s in project.studies if s.id == experiment.study_id))
    left, right = st.columns([1.1, 1], gap="large")
    with left:
        st.markdown(tr("**原文证据**"))
        if not field.current_sources:
            st.info(tr("在已导入且成功解析的资料中未找到对应出处。"))
        for source in field.current_sources:
            label = tr(f"{source.filename or tr('未知来源')} · PDF 第 {source.page or '?'} 页")
            if source.matched:
                st.success(tr(f"原句已定位 · {label}"))
            else:
                st.warning(tr(f"原句未通过定位 · {label}"))
            st.text(source.quote)
            match = next(
                (b for d in study.documents for b in d.blocks if b.id == source.block_id), None
            )
            if match:
                with st.expander(tr(f"查看整页上下文 · {source.block_id}")):
                    st.text(match.text)
        with st.expander(tr("模型原始记录与检查提示"), expanded=bool(field.issues)):
            st.write(
                {
                    tr("模型原值"): field.original.value,
                    tr("模型单位"): field.original.unit,
                    tr("提取状态"): state_label(field.original.status),
                }
            )
            for issue in field.issues:
                st.warning(tr(issue))
    with right:
        st.markdown(tr("**人工核验与修订**"))
        with st.form(f"revise_{field.id}_{len(field.revisions)}"):
            value = st.text_input(tr("当前值"), value=field.value or "")
            unit = st.text_input(tr("单位"), value=field.unit or "")
            status = st.selectbox(
                tr("核验状态"),
                ["pending", "verified", "rejected"],
                index=["pending", "verified", "rejected"].index(field.review_status),
                format_func=fixed_format(
                    lambda x: {
                        "pending": tr("待核验"),
                        "verified": tr("人工确认"),
                        "rejected": tr("不采纳"),
                    }[x]
                ),
            )
            reviewer = st.text_input(tr("核验人"), value="Researcher")
            note = st.text_area(
                tr("核验说明 / 修改理由"),
                placeholder=tr(
                    "例如：对照 Trial A 的条件核验，85% 为污染物去除率，20% 为 TOC 去除率。"
                ),
            )
            replace_source = st.checkbox(tr("替换出处（不勾选则保留现有全部出处）"))
            blocks = [(d, b) for d in study.documents for b in d.blocks]
            source_index = st.selectbox(
                tr("替换为哪一页？"),
                range(len(blocks)),
                format_func=fixed_format(
                    lambda i: tr(f"{blocks[i][0].filename} · 第 {blocks[i][1].page} 页")
                ),
            )
            quote = st.text_area(tr("替换用的原文片段"), help=tr("从原文完整复制，不要改写。"))
            submitted = st.form_submit_button(tr("保存核验记录"), type="primary")
        if submitted:
            sources = (
                [SourceRef(block_id=blocks[source_index][1].id, quote=quote)]
                if replace_source
                else [SourceRef(block_id=s.block_id, quote=s.quote) for s in field.current_sources]
            )
            try:
                revise_field(
                    field,
                    study,
                    value=value.strip() or None,
                    unit=unit.strip() or None,
                    status=status,
                    note=note,
                    reviewer=reviewer,
                    sources=sources,
                )
                store.save(project)
                st.session_state.project = project
                st.rerun()
            except ValueError as exc:
                st.error(tr(str(exc)))
        if field.revisions:
            with st.expander(tr(f"修订历史（{len(field.revisions)} 条）")):
                st.json([r.model_dump() for r in field.revisions])


def export_panel(project):
    st.subheader(tr("导出与记录"))
    st.write(tr("导出保留模型原值、当前值、核验状态、出处与修订历史。未核验字段不会被标成已确认。"))
    cols = st.columns(3)
    cols[0].download_button(
        tr("下载 Excel 工作簿"),
        xlsx_bytes(project),
        "envevidence.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        width="stretch",
    )
    cols[1].download_button(
        tr("下载 CSV 证据表"), csv_bytes(project), "envevidence.csv", "text/csv", width="stretch"
    )
    cols[2].download_button(
        tr("下载完整 JSON"),
        project.model_dump_json(indent=2).encode("utf-8"),
        "envevidence_project.json",
        "application/json",
        width="stretch",
    )
    st.caption(tr("完整 JSON 包含已解析原文。对外分享前请确认资料的分发权限。"))
    st.markdown(tr("**运行记录**"))
    if project.runs:
        names = {s.id: s.name for s in project.studies}
        st.dataframe(
            [
                {
                    tr("论文"): names[r.study_id],
                    tr("状态"): state_label(r.status),
                    tr("输入 tokens"): r.usage.get("input_tokens", 0),
                    tr("输出 tokens"): r.usage.get("output_tokens", 0),
                    tr("错误"): tr(r.error) if r.error else "",
                    tr("开始时间"): r.started_at,
                }
                for r in project.runs
            ],
            hide_index=True,
            width="stretch",
        )
