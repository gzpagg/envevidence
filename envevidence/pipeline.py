from collections.abc import Callable

from .models import Project, Run, now
from .providers import ProviderError
from .storage import ProjectStore
from .verification import validate_extraction


def run_project(
    project: Project,
    store: ProjectStore,
    provider,
    progress: Callable[[int, int, str], None] | None = None,
) -> Project:
    keys = [f.key for f in project.fields]
    if not keys or len(keys) != len(set(keys)):
        raise ValueError("至少选择一个字段，且字段名不能重复。")
    completed = {r.study_id for r in project.runs if r.status == "completed"}
    for run in project.runs:
        if run.status == "running":
            run.status, run.error, run.finished_at = "failed", "上次运行中断，可重试。", now()
    store.save(project)
    for i, study in enumerate(project.studies, 1):
        if study.id in completed:
            continue
        if progress:
            progress(i - 1, len(project.studies), study.name)
        run = Run(study_id=study.id, status="running")
        project.runs.append(run)
        store.save(project)
        try:
            result = provider.extract(study, project.fields)
            experiments = validate_extraction(result.extraction, study, project.fields)
        except Exception as exc:
            run.status = "failed"
            # Never store raw SDK errors, response bodies, credentials, or document text in errors.
            run.error = (
                str(exc)
                if isinstance(exc, ProviderError)
                else "提取或结构校验失败；未保存此篇部分结果。"
            )
            run.finished_at = now()
            store.save(project)
            break  # Avoid repeatedly charging subsequent studies after a provider failure.
        project.experiments.extend(experiments)
        run.status, run.usage, run.finished_at = "completed", result.usage, now()
        store.save(project)
        if progress:
            progress(i, len(project.studies), study.name)
    return project
