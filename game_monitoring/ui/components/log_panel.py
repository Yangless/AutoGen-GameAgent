"""
日志面板组件

显示各种日志
"""

import streamlit as st
from typing import List, Callable


class LogPanel:
    """日志面板"""

    def __init__(
        self,
        title: str,
        log_key: str,
        max_logs: int = 100,
        height: int = 300
    ):
        self._title = title
        self._log_key = log_key
        self._max_logs = max_logs
        self._height = height

    def render(self, logs: List[str]):
        """渲染日志面板"""
        st.markdown(f"**{self._title}**")

        if logs:
            log_html = "\n".join([
                f"<div class='agent-log'>{log}</div>"
                for log in reversed(logs)
            ])
            st.markdown(
                f"<div style='height: {self._height}px; overflow-y: auto; "
                f"border: 1px solid #ddd; padding: 10px;'>{log_html}</div>",
                unsafe_allow_html=True
            )
        else:
            st.info(f"暂无{self._title}")

    def render_controls(self, refresh_callback: Callable = None):
        """渲染控制按钮"""
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 刷新"):
                if refresh_callback:
                    refresh_callback()
        with col2:
            if st.button("🗑️ 清空"):
                return True
        return False
