"""Main dashboard page routed through runtime services."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import streamlit as st

from ...ui.adapters.streamlit_adapter import LogAdapter, SessionStateAdapter, st_async
from ...ui.components import ActionGridComponent, LogPanel, PlayerStatusPanelCompact
from ...ui.components.player_status_panel import SimplePlayerStateView
from ...ui.dashboard_runtime import build_runtime_bundle, get_player_names
from ...ui.intervention_result_view import store_intervention_result

DEFAULT_PLAYER_ID = "孤独的凤凰战士"


@dataclass
class DashboardActionOutcome:
    """Result envelope for a dashboard action execution."""

    result: Any
    rule_labels: list[str]
    intervention: Any | None = None


def _cache_resource(func):
    cache_resource = getattr(st, "cache_resource", None)
    if callable(cache_resource):
        return cache_resource(func)
    return func


@_cache_resource
def get_runtime() -> dict[str, Any]:
    """Resolve the dashboard runtime bundle from the application container."""
    return build_runtime_bundle()


def init_session(default_player: str = DEFAULT_PLAYER_ID) -> None:
    """Initialize the dashboard session state once."""
    session_state = st.session_state
    session_state.setdefault("initialized", True)
    session_state.setdefault("current_player_id", default_player)
    session_state.setdefault("behavior_logs", [])
    session_state.setdefault("agent_logs", [])
    session_state.setdefault("team_analysis_results", [])


def get_rule_label(rule: Any) -> str:
    """Extract a readable rule label from v2 or legacy-shaped rule objects."""
    return (
        getattr(rule, "scenario", None)
        or getattr(rule, "scenario_name", None)
        or getattr(rule, "name", None)
        or "unknown_rule"
    )


async def process_dashboard_action(
    action_service: Any,
    agent_service: Any,
    player_id: str,
    action_name: str,
) -> DashboardActionOutcome:
    """Process an action and trigger intervention when the service asks for it."""
    result = await action_service.process_action(player_id, action_name)
    intervention = None
    if getattr(result, "should_intervene", False):
        intervention = await agent_service.trigger_intervention(player_id)

    return DashboardActionOutcome(
        result=result,
        rule_labels=[get_rule_label(rule) for rule in getattr(result, "triggered_rules", [])],
        intervention=intervention,
    )


def _build_player_state_view(runtime: dict[str, Any], player_id: str) -> SimplePlayerStateView:
    player_state = runtime["player_state_manager"].get_player_state(player_id)
    return SimplePlayerStateView(
        player_id=player_id,
        player_name=player_state.player_name or player_id,
        team_stamina=player_state.team_stamina or [100, 100, 100, 100],
        emotion=player_state.emotion or "未知",
        emotion_confidence=player_state.emotion_confidence or 0.0,
        churn_risk_level=player_state.churn_risk_level or "未知",
        churn_risk_score=player_state.churn_risk_score or 0.0,
        bot_status=(player_state.is_bot, player_state.bot_confidence or 0.0),
    )


def _store_intervention_payload(payload: Any) -> None:
    if not isinstance(payload, dict):
        return

    st.session_state.team_analysis_results = store_intervention_result(
        st.session_state.team_analysis_results,
        payload,
        captured_at=datetime.now(),
        limit=10,
    )


def create_dashboard() -> None:
    """Render the Streamlit dashboard page."""
    st.set_page_config(page_title="🎮 Agent助手监控系统", page_icon="🎮", layout="wide")

    init_session()
    runtime = get_runtime()
    monitor = runtime["monitor"]
    action_service = runtime["action_service"]
    agent_service = runtime["agent_service"]
    session_adapter = SessionStateAdapter()
    behavior_log_adapter = LogAdapter(session_adapter, "behavior_logs")
    agent_log_adapter = LogAdapter(session_adapter, "agent_logs")

    player_names = get_player_names(runtime) or [DEFAULT_PLAYER_ID]
    current_player_id = st.session_state.current_player_id
    if current_player_id not in player_names:
        current_player_id = player_names[0]
        st.session_state.current_player_id = current_player_id

    st.markdown(
        "<h1 style='text-align: center; margin-top: 0;'>🎮 Agent助手监控系统 Dashboard</h1>",
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        st.markdown("<h2 class='section-header'>👤 玩家状态</h2>", unsafe_allow_html=True)
        selected_player = st.selectbox(
            "选择玩家",
            options=player_names,
            index=player_names.index(current_player_id),
        )
        if selected_player != current_player_id:
            st.session_state.current_player_id = selected_player
            st.rerun()

        current_player_id = st.session_state.current_player_id
        PlayerStatusPanelCompact(_build_player_state_view(runtime, current_player_id)).render()

        st.subheader("📊 负面行为统计")
        negative_count = (
            monitor.get_negative_count(current_player_id)
            if hasattr(monitor, "get_negative_count")
            else 0
        )
        metric_col1, metric_col2 = st.columns(2)
        with metric_col1:
            st.metric("当前计数", negative_count)
        with metric_col2:
            st.metric("触发阈值", getattr(monitor, "threshold", 0))

        if negative_count >= getattr(monitor, "threshold", 0):
            st.error("⚠️ 已达触发阈值！")

    with col2:
        tab1, tab2, tab3 = st.tabs(["📋 基础日志", "🧠 Agent分析", "📦 干预结果"])

        with tab1:
            LogPanel("📋 基础日志", "behavior_logs", height=350).render(
                behavior_log_adapter.get_logs()
            )

        with tab2:
            LogPanel("🧠 Agent分析", "agent_logs", height=350).render(
                agent_log_adapter.get_logs()
            )

        with tab3:
            results = st.session_state.team_analysis_results
            if not results:
                st.info("暂无干预结果")
            else:
                latest = results[-1]
                st.metric("最近动作数", len(latest.get("final_actions", [])))
                st.metric("综合置信度", latest.get("overall_confidence", 0.0))
                st.json(latest)

    with col3:
        st.markdown("<h2 class='section-header'>🎯 原子动作</h2>", unsafe_allow_html=True)

        @st_async
        async def handle_action(action_name: str) -> None:
            player_id = st.session_state.current_player_id
            behavior_log_adapter.log(f"🎯 执行动作: {action_name}")

            outcome = await process_dashboard_action(
                action_service,
                agent_service,
                player_id,
                action_name,
            )

            if outcome.rule_labels:
                for rule_label in outcome.rule_labels:
                    agent_log_adapter.log(f"🎭 触发规则: {rule_label}")

            if outcome.intervention is not None:
                if getattr(outcome.intervention, "success", False):
                    agent_log_adapter.log("🚨 达到阈值，已触发Agent干预")
                    _store_intervention_payload(getattr(outcome.intervention, "payload", None))
                    if hasattr(monitor, "reset_negative_count"):
                        monitor.reset_negative_count(player_id)
                else:
                    agent_log_adapter.log(
                        f"❌ Agent干预失败: {getattr(outcome.intervention, 'message', 'unknown error')}"
                    )

            st.rerun()

        ActionGridComponent(on_action_click=handle_action, columns=3).render()

    st.markdown("---")
    st.write(f"系统状态: 🟢 运行中 | 当前玩家: {st.session_state.current_player_id}")


if __name__ == "__main__":
    create_dashboard()
