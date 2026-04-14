import asyncio
from datetime import datetime

import streamlit as st
from streamlit_autorefresh import st_autorefresh

try:
    from streamlit.runtime.scriptrunner import add_script_run_ctx
except Exception:
    add_script_run_ctx = None

from game_monitoring.ui.dashboard_render_context import DashboardRenderContext
from game_monitoring.ui.dashboard_runtime import build_runtime_bundle
from game_monitoring.ui.dashboard_sections import (
    render_dashboard_sections,
    render_status_bar,
)
from game_monitoring.ui.dashboard_session import (
    append_dashboard_log,
    ensure_dashboard_state,
)
from game_monitoring.ui.intervention_result_view import store_intervention_result


st.set_page_config(
    page_title="🎮 游戏Agent助手监控系统 Dashboard",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    .stApp {
        padding: 0 !important;
    }

    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }

    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-top: 0 !important;
        margin-bottom: 1rem;
    }

    .section-header {
        font-size: 1.5rem;
        color: #ff7f0e;
        margin-bottom: 1rem;
        border-bottom: 2px solid #ff7f0e;
        padding-bottom: 0.5rem;
    }

    .player-info {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }

    .behavior-log {
        background-color: #e8f4fd;
        padding: 0.5rem;
        border-radius: 0.3rem;
        margin-bottom: 0.5rem;
        border-left: 4px solid #1f77b4;
    }

    .agent-log {
        background-color: #fff2cc;
        padding: 0.5rem;
        border-radius: 0.3rem;
        margin-bottom: 0.5rem;
        border-left: 4px solid #ff7f0e;
    }

    .log-container {
        height: 400px;
        overflow-y: auto;
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 10px;
        background-color: #f9f9f9;
        margin-bottom: 1rem;
    }

    .stButton > button {
        width: 100%;
        height: 2.5rem;
        font-size: 0.9rem;
        border-radius: 0.5rem;
        border: 1px solid #ddd;
        background-color: #ffffff;
        color: #333333;
        transition: all 0.2s ease;
        margin-bottom: 0.5rem;
    }

    .stButton > button:hover {
        background-color: #f0f2f6;
        border-color: #1f77b4;
        color: #1f77b4;
        transform: translateY(-1px);
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    .stButton > button:active {
        transform: translateY(0);
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
    }

    .action-category {
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e0e0e0;
    }
</style>
""",
    unsafe_allow_html=True,
)


def run_async(coro):
    """Run an async coroutine inside Streamlit."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(coro)


def add_stamina_guide_log(message):
    """Append a stamina-guide log entry."""
    append_dashboard_log(
        st.session_state,
        "stamina_guide_logs",
        message,
        limit=50,
        timestamp_factory=lambda: datetime.now().strftime("%H:%M:%S"),
    )


@st.cache_resource
def initialize_system():
    """Initialize dashboard runtime dependencies."""
    return build_runtime_bundle()


def add_behavior_log(player_id: str, action: str):
    """Append a behavior log entry."""
    append_dashboard_log(
        st.session_state,
        "behavior_logs",
        f"玩家 {player_id}: {action}",
        limit=100,
        timestamp_factory=lambda: datetime.now().strftime("%H:%M:%S"),
    )


def add_agent_log(message: str):
    """Append an agent log entry."""
    append_dashboard_log(
        st.session_state,
        "agent_logs",
        message,
        limit=50,
        timestamp_factory=lambda: datetime.now().strftime("%H:%M:%S"),
    )


def store_team_analysis_result(result):
    """Persist a formatted v2 intervention result for dashboard rendering."""
    if not isinstance(result, dict):
        return

    st.session_state.team_analysis_results = store_intervention_result(
        st.session_state.team_analysis_results,
        result,
        captured_at=datetime.now(),
        limit=10,
    )

    player_id = result.get("player_id", "unknown")
    action_count = len(result.get("final_actions", []) or [])
    confidence = float(result.get("overall_confidence", 0.0))
    add_agent_log(
        f"🧠 v2 干预完成: 玩家 {player_id}, 动作数 {action_count}, 综合置信度 {confidence:.2f}"
    )


def main():
    ensure_dashboard_state(st.session_state)
    st_autorefresh(interval=2000, limit=None, key="auto_refresh_dashboard")

    st.markdown(
        '<h1 class="main-header">🎮 Agent助手监控系统 Dashboard</h1>',
        unsafe_allow_html=True,
    )

    if not st.session_state.system_initialized:
        with st.spinner("正在初始化监控系统..."):
            st.session_state.system = initialize_system()
            runtime = st.session_state.system
            st.session_state.monitor = runtime["monitor"]
            st.session_state.player_state_manager = runtime["player_state_manager"]
            st.session_state.system_initialized = True
            add_agent_log("🚀 监控系统初始化完成")

    ctx = DashboardRenderContext(
        session_state=st.session_state,
        runtime=st.session_state.system,
        monitor=st.session_state.monitor,
        player_state_manager=st.session_state.player_state_manager,
        run_async=run_async,
        add_agent_log=add_agent_log,
        add_behavior_log=add_behavior_log,
        add_stamina_guide_log=add_stamina_guide_log,
        store_team_analysis_result=store_team_analysis_result,
        add_script_run_ctx=add_script_run_ctx,
    )

    render_dashboard_sections(ctx)
    render_status_bar(ctx)


if __name__ == "__main__":
    main()
