from datetime import date
from html import escape

import streamlit as st
from pydantic import ValidationError

from .demo import DemoProvider, demo_project
from .i18n import fixed_format, t
from .pipeline import run_project
from .themes import NOTE_COLORS, PALETTES, apply_theme, colors
from .workspace import (
    MODULES,
    DailyTask,
    LearningGoal,
    Note,
    Preferences,
    Step,
    add_demo,
    overdue_tasks,
    task_progress,
    tasks_for_day,
)

NAMES = {
    "home": ("Workspace", "工作台"),
    "evidence": ("Literature evidence", "文献证据"),
    "learning": ("Learning goals", "学习进度"),
    "tasks": ("Daily tasks", "日常进度"),
    "notes": ("Sticky notes", "便利贴"),
    "settings": ("Appearance & modules", "外观与模块"),
}
ICONS = {"home": "◈", "evidence": "▤", "learning": "◉", "tasks": "☑", "notes": "▧", "settings": "⚙"}


def name(key):
    return t(*NAMES[key])


def go(page):
    st.session_state.page = page
    st.rerun()


def persist(workspace, store):
    try:
        store.save(workspace)
    except OSError:
        st.error(
            t(
                "Could not save. Check folder permissions and free disk space.",
                "无法保存，请检查目录权限与磁盘空间。",
            )
        )
        st.stop()
    st.rerun()


def invalid():
    st.error(
        t(
            "Check the form: a nonempty title (up to 300 characters) and valid http(s) resource links are required.",
            "请检查表单：标题不能为空且最多 300 字符；资源链接需为有效的 http(s) 地址。",
        )
    )


def sidebar(workspace, store, evidence_store, version):
    prefs = workspace.preferences
    with st.sidebar:
        st.markdown("## 🌿 EnvEvidence")
        st.caption(t("Your research, one day at a time.", "有条理地推进每一天的科研。"))
        locale = st.selectbox(
            "Language / 语言",
            ["en", "zh"],
            index=["en", "zh"].index(prefs.language),
            format_func=fixed_format(lambda v: "English" if v == "en" else "简体中文"),
            key="locale",
        )
        if locale != prefs.language:
            prefs.language = locale
            persist(workspace, store)
        st.divider()
        for module in ["home"] + [m for m in prefs.order if m not in prefs.hidden] + ["settings"]:
            if st.button(
                f"{ICONS[module]}  {name(module)}",
                key=f"nav_{module}",
                width="stretch",
                type="primary" if st.session_state.get("page", "home") == module else "secondary",
            ):
                go(module)
        st.divider()
        if st.button(
            t("Load workspace demo", "载入工作台演示"),
            key="workspace_demo",
            disabled=workspace.demo_loaded,
            width="stretch",
        ):
            project = demo_project()
            project.name = t("Demo · Water-treatment evidence", "示例 · 水处理实验的证据核验")
            run_project(project, evidence_store, DemoProvider())
            add_demo(workspace, prefs.language)
            st.session_state.project = project
            persist(workspace, store)
        st.caption(
            t(
                "Invented examples. Appended once, without replacing your work.",
                "自制演示，只追加一次，不覆盖已有内容。",
            )
        )
        st.divider()
        st.caption(
            t(
                "Plans and notes stay on this computer. Only explicit evidence extraction sends text to your chosen API.",
                "计划和便签保存在本机。只有主动启动文献提取才向所选 API 发送文本。",
            )
        )
        st.caption(f"v{version} · " + t("Local · Single user", "本地 · 单用户"))


def hero():
    st.markdown(
        f"""<div class="ee-hero"><div class="ee-eyebrow">ENVEVIDENCE / RESEARCH WORKSPACE</div>\n    <h1>{t("Make room for focused research.", "让科研进展，看得见。")}</h1>\n    <p>{t("Learn with intention. Plan your day. Keep every claim connected to evidence.", "拆解学习目标，安排每日任务，让每条证据都有出处。")}</p></div>""",
        unsafe_allow_html=True,
    )


def home(workspace, evidence_store):
    hero()
    st.caption(t("TODAY", "今天") + " · " + date.today().isoformat())
    modules = [m for m in workspace.preferences.order if m not in workspace.preferences.hidden]
    if not modules:
        st.info(
            t(
                "All modules are hidden. Enable them in Appearance & modules.",
                "所有模块已隐藏，可在外观与模块中重新开启。",
            )
        )
    for start in range(0, len(modules), 2):
        columns = st.columns(2, gap="large")
        for col, module in zip(columns, modules[start : start + 2]):
            with col, st.container(border=True, key=f"surface_home_{module}"):
                st.subheader(f"{ICONS[module]}  {name(module)}")
                if module == "evidence":
                    projects = evidence_store.list_projects()
                    pending, unreadable = (0, 0)
                    for record in projects:
                        try:
                            project = evidence_store.load(record["id"])
                            pending += sum(
                                (
                                    f.review_status == "pending"
                                    for e in project.experiments
                                    for f in e.fields
                                )
                            )
                        except (OSError, ValueError):
                            unreadable += 1
                    st.write(
                        t(
                            f"Projects: {len(projects)} · Fields awaiting review: {pending}",
                            f"{len(projects)} 个项目 · {pending} 个字段待核验",
                        )
                    )
                    st.caption(
                        t(
                            "Source location is the start of scientific review.",
                            "原文定位是科学核验的起点。",
                        )
                    )
                    if unreadable:
                        st.warning(
                            t(
                                f"{unreadable} unreadable projects excluded from review counts.",
                                f"{unreadable} 个无法读取的项目未计入核验统计。",
                            )
                        )
                    if projects and st.button(
                        t("Open latest: ", "打开最近项目：") + projects[0]["name"],
                        key="latest_evidence",
                    ):
                        try:
                            st.session_state.project = evidence_store.load(projects[0]["id"])
                            go("evidence")
                        except (OSError, ValueError):
                            st.error(t("Could not open this project.", "无法打开此项目。"))
                elif module == "learning":
                    goals = [g for g in workspace.goals if not g.archived]
                    st.write(t(f"Active learning goals: {len(goals)}", f"{len(goals)} 个学习目标"))
                    for goal in goals[:2]:
                        st.write(goal.title)
                        progress(goal.progress, t("No steps yet", "尚未添加步骤"))
                    if not goals:
                        st.caption(
                            t(
                                "Turn a topic into a small, actionable checklist.",
                                "将学习主题拆成可以逐步完成的清单。",
                            )
                        )
                elif module == "tasks":
                    tasks = tasks_for_day(workspace, date.today())
                    progress(task_progress(tasks), t("No tasks planned today", "今天尚未安排任务"))
                    st.write(
                        t(
                            f"{sum((x.status == 'done' for x in tasks))} / {len(tasks)} tasks completed",
                            f"已完成 {sum((x.status == 'done' for x in tasks))} / {len(tasks)} 项任务",
                        )
                    )
                    count = len(overdue_tasks(workspace, date.today()))
                    st.caption(
                        t(
                            f"Overdue tasks: {count} · Original dates retained",
                            f"{count} 项逾期任务 · 保留原计划日期",
                        )
                    )
                else:
                    notes = sorted(
                        [n for n in workspace.notes if not n.archived], key=lambda n: not n.pinned
                    )
                    st.write(
                        t(
                            f"Notes: {len(notes)} · Keep small ideas close",
                            f"{len(notes)} 张便签 · 随时记录灵感",
                        )
                    )
                    if notes:
                        note_card(notes[0], compact=True)
                if st.button(
                    t("Open module →", "进入模块 →"), key=f"open_{module}", width="stretch"
                ):
                    go(module)


def progress(value, empty):
    if value is None:
        st.caption(empty)
    else:
        st.progress(value, text=f"{round(value * 100)}%")


def archived_view(key):
    return st.toggle(t("Show archived", "查看归档"), key=f"archived_{key}")


def archive_button(item, workspace, store):
    if st.button(
        t("Restore", "恢复") if item.archived else t("Archive", "归档"), key=f"archive_{item.id}"
    ):
        item.archived = not item.archived
        persist(workspace, store)


def learning(workspace, store):
    st.header(name("learning"))
    st.caption(
        t(
            "Progress = completed steps / all steps. Archived goals are excluded.",
            "进度＝已完成步骤／全部步骤；归档目标不计入当前进度。",
        )
    )
    with st.expander(t("Add a learning goal", "添加学习目标")):
        with st.form("new_goal", clear_on_submit=True):
            title = st.text_input(t("Goal title", "目标名称"), key="new_goal_title")
            if st.form_submit_button(t("Create goal", "创建目标")):
                try:
                    workspace.goals.append(LearningGoal(title=title))
                    persist(workspace, store)
                except ValidationError:
                    invalid()
    archived = archived_view("goals")
    goals = {g.id: g for g in workspace.goals if g.archived == archived}
    if not goals:
        st.info(t("No goals in this view.", "当前视图没有目标。"))
        return
    selected = st.selectbox(
        t("Goal", "学习目标"),
        list(goals),
        format_func=fixed_format(lambda x: goals[x].title),
        key=f"goal_{archived}",
    )
    goal = goals[selected]
    progress(goal.progress, t("No steps yet", "尚未添加步骤"))
    with st.form(f"goal_edit_{goal.id}"):
        title = st.text_input(t("Title", "标题"), goal.title)
        description = st.text_area(t("Description", "说明"), goal.description)
        resources = st.text_area(
            t("Resource links (one per line)", "资源链接（每行一个）"), "\n".join(goal.resources)
        )
        if st.form_submit_button(t("Save goal", "保存目标")):
            try:
                updated = LearningGoal(
                    **{
                        **goal.model_dump(),
                        "title": title,
                        "description": description,
                        "resources": [x.strip() for x in resources.splitlines() if x.strip()],
                    }
                )
                workspace.goals[workspace.goals.index(goal)] = updated
                persist(workspace, store)
            except ValidationError:
                invalid()
    for index, link in enumerate(goal.resources, 1):
        st.link_button(t(f"Resource {index}", f"资源 {index}"), link)
    st.subheader(t("Steps", "学习步骤"))
    for step in goal.steps:
        done = st.checkbox(step.title, value=step.done, key=f"step_{step.id}", disabled=archived)
        if done != step.done:
            step.done = done
            persist(workspace, store)
    if not archived:
        with st.form(f"add_step_{goal.id}", clear_on_submit=True):
            title = st.text_input(t("New step", "新步骤"), key="new_step_title")
            if st.form_submit_button(t("Add step", "添加步骤")):
                if not title.strip() or len(title.strip()) > 300:
                    invalid()
                else:
                    goal.steps.append(Step(title=title.strip()))
                    persist(workspace, store)
        if goal.steps:
            with st.expander(t("Edit or remove a step", "修改或移除步骤")):
                ids = {s.id: s for s in goal.steps}
                chosen = st.selectbox(
                    t("Step", "步骤"),
                    list(ids),
                    format_func=fixed_format(lambda x: ids[x].title),
                    key=f"edit_step_{goal.id}",
                )
                step = ids[chosen]
                with st.form(f"step_edit_{step.id}"):
                    title = st.text_input(t("Step title", "步骤名称"), step.title)
                    save = st.form_submit_button(t("Save step", "保存步骤"))
                    remove = st.form_submit_button(t("Remove step", "移除步骤"))
                if remove:
                    goal.steps.remove(step)
                    persist(workspace, store)
                if save:
                    if not title.strip() or len(title.strip()) > 300:
                        invalid()
                    else:
                        step.title = title.strip()
                        persist(workspace, store)
    archive_button(goal, workspace, store)


def task_label(value):
    return t(
        *{
            "todo": ("To do", "待办"),
            "doing": ("In progress", "进行中"),
            "done": ("Done", "已完成"),
            "high": ("High", "高"),
            "normal": ("Normal", "中"),
            "low": ("Low", "低"),
        }[value]
    )


def tasks(workspace, store):
    st.header(name("tasks"))
    with st.expander(t("Add a task", "添加任务")):
        with st.form("new_task", clear_on_submit=True):
            title = st.text_input(t("Task title", "任务名称"), key="new_task_title")
            planned = st.date_input(
                t("Planned date", "计划日期"), date.today(), key="new_task_date"
            )
            priority = st.selectbox(
                t("Priority", "优先级"),
                ["normal", "high", "low"],
                format_func=fixed_format(task_label),
            )
            if st.form_submit_button(t("Create task", "创建任务")):
                try:
                    workspace.tasks.append(
                        DailyTask(title=title, planned_date=planned, priority=priority)
                    )
                    persist(workspace, store)
                except ValidationError:
                    invalid()
    archived = archived_view("tasks")
    view = st.radio(
        t("Task view", "任务视图"),
        ["today", "date", "overdue"],
        horizontal=True,
        format_func=fixed_format(
            lambda x: {
                "today": t("Today", "今天"),
                "date": t("Choose date", "指定日期"),
                "overdue": t("Overdue", "逾期未完成"),
            }[x]
        ),
        key="task_view",
    )
    day = date.today()
    if view == "date":
        day = st.date_input(t("View date", "查看日期"), day, key="view_date")
    if archived:
        items = [x for x in workspace.tasks if x.archived]
        st.caption(
            t(
                "All archived tasks, independent of the date filter.",
                "显示全部归档任务，不受日期筛选影响。",
            )
        )
    elif view == "overdue":
        items = overdue_tasks(workspace, day)
        st.caption(
            t(
                "Unfinished tasks before today; dates are never changed automatically.",
                "今天以前尚未完成的任务；不会自动更改日期。",
            )
        )
    else:
        items = tasks_for_day(workspace, day)
        progress(task_progress(items), t("No tasks for this date", "该日期尚无任务"))
    items.sort(key=lambda x: (x.planned_date, ["high", "normal", "low"].index(x.priority)))
    if not items:
        st.info(t("No tasks in this view.", "当前视图没有任务。"))
    for task in items:
        with st.container(border=True, key=f"surface_task_{task.id}"):
            st.subheader(task.title)
            st.caption(
                f"{task.planned_date} · {task_label(task.priority)} · {task_label(task.status)}"
            )
            with st.form(f"task_{task.id}"):
                title = st.text_input(t("Title", "标题"), task.title)
                planned = st.date_input(t("Planned date", "计划日期"), task.planned_date)
                priority = st.selectbox(
                    t("Priority", "优先级"),
                    ["high", "normal", "low"],
                    index=["high", "normal", "low"].index(task.priority),
                    format_func=fixed_format(task_label),
                )
                status = st.selectbox(
                    t("Status", "状态"),
                    ["todo", "doing", "done"],
                    index=["todo", "doing", "done"].index(task.status),
                    format_func=fixed_format(task_label),
                )
                if st.form_submit_button(t("Save task", "保存任务")):
                    try:
                        updated = DailyTask(
                            **{
                                **task.model_dump(),
                                "title": title,
                                "planned_date": planned,
                                "priority": priority,
                                "status": status,
                            }
                        )
                        workspace.tasks[workspace.tasks.index(task)] = updated
                        persist(workspace, store)
                    except ValidationError:
                        invalid()
            archive_button(task, workspace, store)


def note_card(note, compact=False):
    text = note.body[:180] + ("…" if len(note.body) > 180 else "") if compact else note.body
    title = ("● " if note.pinned else "") + note.title
    st.markdown(
        f'<div class="ee-note" style="background:{NOTE_COLORS[note.color]}"><strong>{escape(title)}</strong><br>{escape(text)}</div>',
        unsafe_allow_html=True,
    )


def notes(workspace, store):
    st.header(name("notes"))
    with st.expander(t("Add a sticky note", "添加便利贴")):
        with st.form("new_note", clear_on_submit=True):
            title = st.text_input(t("Note title", "便签标题"), key="new_note_title")
            body = st.text_area(t("Note", "内容"), key="new_note_body")
            if st.form_submit_button(t("Create note", "创建便签")):
                try:
                    workspace.notes.append(Note(title=title, body=body))
                    persist(workspace, store)
                except ValidationError:
                    invalid()
    archived = archived_view("notes")
    items = sorted(
        [n for n in workspace.notes if n.archived == archived], key=lambda n: not n.pinned
    )
    if not items:
        st.info(t("No notes in this view.", "当前视图没有便签。"))
    for note in items:
        note_card(note)
        with st.expander(t("Edit: ", "编辑：") + note.title):
            with st.form(f"note_{note.id}"):
                title = st.text_input(t("Title", "标题"), note.title)
                body = st.text_area(t("Note", "内容"), note.body)
                pinned = st.checkbox(t("Pin to top", "置顶"), note.pinned)
                color = st.selectbox(
                    t("Note color", "便签颜色"),
                    list(NOTE_COLORS),
                    index=list(NOTE_COLORS).index(note.color),
                    format_func=fixed_format(
                        lambda x: t(
                            x.title(),
                            {
                                "sage": "鼠尾草绿",
                                "sky": "天空蓝",
                                "sand": "浅杏黄",
                                "lavender": "淡紫",
                            }[x],
                        )
                    ),
                )
                if st.form_submit_button(t("Save note", "保存便签")):
                    try:
                        updated = Note(
                            **{
                                **note.model_dump(),
                                "title": title,
                                "body": body,
                                "pinned": pinned,
                                "color": color,
                            }
                        )
                        workspace.notes[workspace.notes.index(note)] = updated
                        persist(workspace, store)
                    except ValidationError:
                        invalid()
            archive_button(note, workspace, store)


def settings(workspace, store):
    st.header(name("settings"))
    prefs = workspace.preferences
    left, right = st.columns([1, 1.15], gap="large")
    with left:
        st.subheader(t("Color palette", "界面配色"))
        names = {
            "forest": ("Forest", "森林绿"),
            "ocean": ("Ocean", "海洋蓝"),
            "sand": ("Sand", "暖灰橙"),
            "graphite": ("Graphite", "石墨紫"),
            "custom": ("Custom", "自定义"),
        }
        palette = st.selectbox(
            t("Palette", "配色方案"),
            list(names),
            index=list(names).index(prefs.palette),
            format_func=fixed_format(lambda x: t(*names[x])),
            key="palette_draft",
        )
        draft = prefs.model_copy(deep=True)
        draft.palette = palette
        if palette == "custom":
            cols = st.columns(2)
            draft.accent = cols[0].color_picker(
                t("Accent color", "主色"), prefs.accent, key="accent_draft"
            )
            draft.background = cols[1].color_picker(
                t("Page background", "页面背景"), prefs.background, key="background_draft"
            )
        else:
            draft.accent, draft.background, _ = PALETTES[palette]
        apply_theme(draft)
        c = colors(draft)
        st.markdown(
            f"""<div class="ee-hero"><h3 style="color:inherit">{t("A little space to think.", "留一点空间，专注思考。")}</h3><p>{t("Live preview · Save to keep this palette", "即时预览 · 保存后下次启动仍生效")}</p></div>""",
            unsafe_allow_html=True,
        )
        st.caption(f"{c['accent']} · {c['background']}")
        if st.button(t("Save appearance", "保存外观"), type="primary", key="save_appearance"):
            workspace.preferences = Preferences.model_validate(draft.model_dump())
            persist(workspace, store)
        if st.button(t("Restore default colors", "恢复默认配色"), key="reset_colors"):
            prefs.palette, prefs.accent, prefs.background = ("forest", *PALETTES["forest"][:2])
            for key in ("palette_draft", "accent_draft", "background_draft"):
                st.session_state.pop(key, None)
            persist(workspace, store)
    with right:
        st.subheader(t("Modules & order", "模块与顺序"))
        st.caption(
            t(
                "Hide a module without deleting its data. Workspace and settings remain available.",
                "隐藏模块不会删除数据，工作台与设置入口始终保留。",
            )
        )
        for i, module in enumerate(prefs.order):
            with st.container(border=True, key=f"surface_settings_{module}"):
                cols = st.columns([3, 1, 1])
                visible = cols[0].checkbox(
                    name(module), module not in prefs.hidden, key=f"visible_{module}"
                )
                if visible != (module not in prefs.hidden):
                    prefs.hidden = (
                        [m for m in prefs.hidden if m != module]
                        if visible
                        else prefs.hidden + [module]
                    )
                    persist(workspace, store)
                if cols[1].button(t("↑ Up", "↑ 上移"), key=f"up_{module}", disabled=i == 0):
                    prefs.order[i - 1], prefs.order[i] = (prefs.order[i], prefs.order[i - 1])
                    persist(workspace, store)
                if cols[2].button(
                    t("↓ Down", "↓ 下移"), key=f"down_{module}", disabled=i == len(prefs.order) - 1
                ):
                    prefs.order[i + 1], prefs.order[i] = (prefs.order[i], prefs.order[i + 1])
                    persist(workspace, store)
        if st.button(t("Restore default layout", "恢复默认布局"), key="reset_layout"):
            prefs.order, prefs.hidden = (MODULES.copy(), [])
            for module in MODULES:
                st.session_state.pop(f"visible_{module}", None)
            persist(workspace, store)
