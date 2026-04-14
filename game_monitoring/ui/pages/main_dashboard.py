"""
重构后的主Dashboard页面

职责：纯协调层，调用服务完成业务逻辑
"""

import streamlit as st
from typing import Optional, List

from ...core import bootstrap_application, GameContext, SystemConfig
from ...ui.adapters.streamlit_adapter import SessionStateAdapter, LogAdapter, st_async
from ...ui.components import ActionGridComponent, PlayerStatusPanel, LogPanel, SimplePlayerStateView
from ...application.services import ActionProcessingService


def init_session(default_player: str = "孤独的凤凰战士"):
    """初始化session state"""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.current_player_id = default_player
        st.session_state.behavior_logs = []
        st.session_state.agent_logs = []
        st.session_state.negative_counts = {}


def create_dashboard():
    """创建Dashboard"""
    st.set_page_config(
        page_title="🎮 Agent助手监控系统",
        page_icon="🎮",
        layout="wide"
    )

    # 初始化
    init_session()

    # 引导系统
    @st.cache_resource
    def get_system():
        return bootstrap_application()

    container = get_system()
    context = container.resolve(GameContext)
    action_service = container.resolve(ActionProcessingService)

    st.markdown("<h1 style='text-align: center; margin-top: 0;'>🎮 Agent助手监控系统 Dashboard</h1>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    # ===== 左侧面板 =====
    with col1:
        st.markdown("<h2 class='section-header'>👤 玩家状态</h2>", unsafe_allow_html=True)

        player_id = st.session_state.current_player_id

        # 玩家选择
        player_names = ["龙傲天", "叶良辰", "孤独的凤凰战士"]
        selected = st.selectbox(
            "选择玩家",
            options=player_names,
            index=player_names.index(player_id) if player_id in player_names else 0
        )
        if selected != player_id:
            st.session_state.current_player_id = selected
            st.rerun()

        # 简单状态展示
        player_state = context.player_state_manager.get_player_state(player_id)
        state_view = SimplePlayerStateView(
            player_id=player_id,
            player_name=player_id,
            emotion=player_state.emotion or "未知",
            emotion_confidence=player_state.emotion_confidence or 0.0,
            churn_risk_level=player_state.churn_risk_level or "未知",
            churn_risk_score=player_state.churn_risk_score or 0.0,
            bot_status=(player_state.is_bot, player_state.bot_confidence)
        )
        PlayerStatusPanelCompact(state_view).render()

        # 负面行为计数
        st.subheader("📊 负面行为统计")
        monitor = context.monitor
        negative_count = getattr(monitor, '_negative_counts', {}).get(player_id, 0)

        col_stat1, col_stat2 = st.columns(2)
        with col_stat1:
            st.metric("当前计数", negative_count)
        with col_stat2:
            st.metric("触发阈值", monitor.threshold)

        if negative_count >= monitor.threshold:
            st.error("⚠️ 已达触发阈值！")

    # ===== 中央面板 =====
    with col2:
        tab1, tab2, tab3 = st.tabs(["📋 基础日志", "🧠 Agent分析", "⚡ 体力引导"])

        with tab1:
            log_adapter = LogAdapter(SessionStateAdapter(), "behavior_logs")
            LogPanel("📋 基础日志", "behavior_logs", height=350).render(
                log_adapter.get_logs()
            )

        with tab2:
            st.markdown("**🧠 团队分析**")
            st.info("这里将显示Agent团队分析结果...")

        with tab3:
            st.markdown("**⚡ 体力引导Agent**")
            st.info("体力相关引导将显示在这里...")

    # ===== 右侧面板 =====
    with col3:
        st.markdown("<h2 class='section-header'>🎯 原子动作</h2>", unsafe_allow_html=True)

        @st_async
        async def handle_action(action_name: str):
            """处理动作点击"""
            log_adapter = LogAdapter(SessionStateAdapter())
            log_adapter.log(f"🎯 执行动作: {action_name}")

            result = await action_service.process_action(player_id, action_name)

            if result.triggered_rules:
                for rule in result.triggered_rules:
                    log_adapter.log(f"🎭 触发规则: {rule.scenario_name}")

            if result.should_intervene:
                log_adapter.log("🚨 达到阈值，触发Agent干预！")
                # 这里可以调用Agent服务

            st.rerun()

        ActionGridComponent(
            on_action_click=handle_action,
            columns=3
        ).render()

    # 底部状态
    st.markdown("---")
    st.write(f"系统状态: 🟢 运行中 | 当前玩家: {player_id}")


if __name__ == "__main__":
    create_dashboard()
