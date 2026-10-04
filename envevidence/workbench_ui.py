import streamlit as st

from .i18n import fixed_format, t
from .themes import PALETTES, apply_theme, colors
from .workspace import Preferences

NAMES = {
    "analysis": ("Experiment analysis", "实验分析"),
    "evidence": ("Literature evidence", "文献证据"),
    "settings": ("Appearance", "外观"),
}


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


def sidebar(workspace, store, version):
    prefs = workspace.preferences
    with st.sidebar:
        st.markdown("## EnvEvidence")
        st.caption(
            t(
                "Experiments, curves and evidence.",
                "实验数据、动力学曲线与文献证据。",
            )
        )
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
        for page in NAMES:
            if st.button(
                name(page),
                key=f"nav_{page}",
                width="stretch",
                type="primary" if st.session_state.get("page", "analysis") == page else "secondary",
            ):
                go(page)
        st.divider()
        kept = len(workspace.goals) + len(workspace.tasks) + len(workspace.notes)
        if kept:
            st.caption(
                t(
                    f"{kept} learning goals, tasks and notes from version 0.2 are kept unchanged in data/workspace/state.json.",
                    f"0.2 版的 {kept} 条学习目标、任务和便签原样保存在 data/workspace/state.json。",
                )
            )
        st.caption(
            t(
                "Experiment analysis stays local. Only explicit literature extraction sends text to your chosen API.",
                "实验分析完全在本地完成。只有主动启动文献提取才向所选 API 发送文本。",
            )
        )
        st.caption(f"v{version} · " + t("Local · Single user", "本地 · 单用户"))


def settings(workspace, store):
    st.header(name("settings"))
    prefs = workspace.preferences
    left, _ = st.columns([1, 1.15], gap="large")
    with left:
        st.subheader(t("Color palette", "界面配色"))
        names = {
            "mineral": ("Mineral · teal", "矿物青 · 浅灰"),
            "clay": ("Clay", "陶土色"),
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
            f"""<div class="ee-hero"><h3 style="color:inherit">{t("Every value, traced to its source.", "每个数值，都能追溯到原文。")}</h3><p>{t("Live preview · Save to keep this palette", "即时预览 · 保存后下次启动仍生效")}</p></div>""",
            unsafe_allow_html=True,
        )
        st.caption(f"{c['accent']} · {c['background']}")
        if st.button(t("Save appearance", "保存外观"), type="primary", key="save_appearance"):
            workspace.preferences = Preferences.model_validate(draft.model_dump())
            persist(workspace, store)
        if st.button(t("Restore default colors", "恢复默认配色"), key="reset_colors"):
            prefs.palette, prefs.accent, prefs.background = ("mineral", *PALETTES["mineral"][:2])
            for key in ("palette_draft", "accent_draft", "background_draft"):
                st.session_state.pop(key, None)
            persist(workspace, store)



