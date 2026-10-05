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
        st.markdown(
            '<div class="ee-brand"><svg viewBox="0 0 32 32" aria-hidden="true" fill="none">'
            '<rect x="1" y="1" width="30" height="30" rx="10" fill="#176BDA"/>'
            '<path d="M11 8h10M14 8v8l-5 7a2 2 0 0 0 2 3h10a2 2 0 0 0 2-3l-5-7V8M12 21h8" '
            'stroke="white" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>'
            '</svg><span>EnvEvidence</span></div>', unsafe_allow_html=True,
        )
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
        with st.container(key="glass_navigation"):
            icons = {"analysis": ":material/experiment:", "evidence": ":material/menu_book:",
                     "settings": ":material/palette:"}
            for page in NAMES:
                if st.button(
                    name(page), key=f"nav_{page}", icon=icons[page], width="stretch",
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


def reset_appearance(workspace, store):
    # A button callback updates widget state before the next script run. Popping
    # a rendered widget's key can leave its old browser selection on the screen.
    prefs = workspace.preferences
    prefs.palette, prefs.accent, prefs.background = ("glacier", *PALETTES["glacier"][:2])
    prefs.visual_style, prefs.reduce_transparency, prefs.appearance_version = "glass", False, 2
    st.session_state.palette_draft = "glacier"
    st.session_state.visual_style_draft = "glass"
    st.session_state.reduce_transparency_draft = False
    for key in ("accent_draft", "background_draft"):
        st.session_state.pop(key, None)
    try:
        store.save(workspace)
    except OSError:
        st.error(t("Could not save. Check folder permissions and free disk space.",
                   "无法保存，请检查目录权限与磁盘空间。"))
        st.stop()


def settings(workspace, store):
    st.header(name("settings"))
    st.caption(t("Shape your research workspace.", "让科研工作台更合你的习惯。"))
    prefs = workspace.preferences
    with st.container(key="split_appearance"):
        left, right = st.columns([1, 1.1], gap="large")
    with left, st.container(key="surface_appearance_controls"):
        st.subheader(t("Color and material", "配色与材质"))
        names = {
            "glacier": ("Glacier · blue & cyan", "冰川 · 蓝青"),
            "mineral": ("Mineral · teal", "矿物青 · 浅灰"),
            "clay": ("Clay", "陶土色"), "forest": ("Forest", "森林绿"),
            "ocean": ("Ocean", "海洋蓝"), "sand": ("Sand", "暖灰橙"),
            "graphite": ("Graphite", "石墨紫"), "custom": ("Custom", "自定义"),
        }
        palette = st.selectbox(
            t("Palette", "配色方案"), list(names), index=list(names).index(prefs.palette),
            format_func=fixed_format(lambda x: t(*names[x])), key="palette_draft",
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
        draft.visual_style = st.radio(
            t("Navigation material", "导航材质"), ["glass", "solid"],
            index=["glass", "solid"].index(prefs.visual_style), horizontal=True,
            format_func=fixed_format(lambda x: t("Frosted glass", "磨砂玻璃") if x == "glass" else t("Solid", "实色")),
            key="visual_style_draft",
        )
        draft.reduce_transparency = st.checkbox(
            t("Reduce transparency", "减少透明效果"), value=prefs.reduce_transparency,
            help=t("Use opaque navigation and panels while keeping your colors.", "保留配色，让导航与面板使用不透明背景。"),
            key="reduce_transparency_draft",
        )
        draft.appearance_version = 2
        apply_theme(draft)
        if st.button(t("Save appearance", "保存外观"), type="primary", key="save_appearance", width="stretch"):
            workspace.preferences = Preferences.model_validate(draft.model_dump())
            persist(workspace, store)
        st.button(t("Restore default appearance", "恢复默认外观"), key="reset_colors", width="stretch",
                  on_click=reset_appearance, args=(workspace, store))
    with right:
        c = colors(draft)
        st.markdown(
            f'<div class="ee-hero"><h3>{t("A clearer view of your experiments.", "让每次实验，清晰呈现。")}</h3>'
            f'<p>{t("Live preview · Save to keep this appearance", "即时预览 · 保存后下次启动仍生效")}</p></div>',
            unsafe_allow_html=True,
        )
        with st.container(key="glass_appearance_preview"):
            st.markdown("**" + t("Your workspace", "你的工作台") + "**")
            st.caption(t("Navigation floats above a quiet background. Measurements and figures stay on solid surfaces.",
                         "导航悬浮于浅色背景之上，测量数据与图表呈现在清晰的实色面板中。"))
        with st.container(key="surface_appearance_preview"):
            st.markdown("**" + t("Measurements · Treatment A", "测量数据 · 处理 A") + "**")
            st.progress(0.7, text=t("7 of 10 samples recorded", "已记录 7 / 10 个样品"))
            st.caption(f"{c['accent']} · {c['background']}")
