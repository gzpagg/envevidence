from __future__ import annotations

import os

import streamlit as st

from envevidence import __version__
from envevidence.evidence_ui import evidence_page
from envevidence.i18n import LANGUAGE, t
from envevidence.storage import ProjectStore
from envevidence.themes import apply_theme
from envevidence.workbench_ui import home, learning, notes, settings, sidebar, tasks
from envevidence.workspace import WorkspaceStore


def main():
    st.set_page_config(page_title="EnvEvidence · Research Workspace", page_icon="🌿", layout="wide")
    root = os.getenv("ENVEVIDENCE_DATA_DIR") or "data"
    workspace_store = WorkspaceStore(root)
    try:
        workspace = workspace_store.load()
    except (OSError, ValueError):
        st.error(
            "Cannot read workspace data. Original file preserved. / 无法读取工作台数据，原文件已保留。"
        )
        st.stop()
    LANGUAGE.set(workspace.preferences.language)
    st.set_page_config(page_title=t("EnvEvidence · Research Workspace", "EnvEvidence · 科研工作台"))
    apply_theme(workspace.preferences)
    evidence_store = ProjectStore(root)
    if st.session_state.get("page") in workspace.preferences.hidden:
        st.session_state.page = "home"
    sidebar(workspace, workspace_store, evidence_store, __version__)
    page = st.session_state.get("page", "home")
    try:
        if page == "home":
            home(workspace, evidence_store)
        elif page == "evidence":
            evidence_page(evidence_store)
        else:
            {"learning": learning, "tasks": tasks, "notes": notes, "settings": settings}[page](
                workspace, workspace_store
            )
    except OSError:
        st.error(
            t(
                "Could not access local data. Check folder permissions and disk space.",
                "无法访问本地数据，请检查目录权限和磁盘空间。",
            )
        )


if __name__ == "__main__":
    main()
