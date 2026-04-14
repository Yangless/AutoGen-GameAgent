"""Section-level dashboard renderers extracted from the main entrypoint."""

from __future__ import annotations

import asyncio as _asyncio
from datetime import datetime
from threading import Thread
from typing import Any

import streamlit as st

from .dashboard_actions import process_atomic_action
from .dashboard_render_context import DashboardRenderContext
from .dashboard_state import clear_action_sequence
from .dashboard_tabs import (
    render_basic_logs_tab,
    render_orders_tab,
    render_stamina_tab,
    render_team_analysis_tab,
)

_ACTION_NAME_MAPPING = {
    "login": "登录游戏",
    "logout": "退出登录",
    "enter_dungeon": "进入副本",
    "complete_dungeon": "完成副本",
    "move_city": "迁移城市",
    "attack_city": "攻击城市",
    "be_attacked": "被攻击",
    "win_pvp": "PVP获胜",
    "lose_pvp": "PVP失败",
    "occupy_land": "占领土地",
    "attack_npc_tribe": "攻击蛮族",
    "recruit_hero": "招募英雄",
    "upgrade_building": "升级建筑",
    "upgrade_skill": "升级技能",
    "enhance_equipment": "强化装备",
    "dismantle_equipment": "分解装备",
    "unlock_achievement": "解锁成就",
    "unlock_map": "解锁地图",
    "stamina_exhausted": "体力耗尽",
    "attempt_enter_dungeon_no_stamina": "无体力进副本",
    "join_family": "加入家族",
    "leave_family": "离开家族",
    "join_nation": "加入国家",
    "send_chat_message": "发送聊天",
    "receive_chat_message": "接收聊天",
    "add_friend": "添加好友",
    "remove_friend": "删除好友",
    "receive_praise": "收到赞美",
    "be_invited_to_family": "被邀请入族",
    "navigate_to_payment_page": "跳转充值页",
    "make_payment": "进行充值",
    "buy_monthly_card": "购买月卡",
    "cancel_auto_renew": "取消自动续费",
    "receive_daily_reward": "领取日常奖励",
    "receive_event_reward": "领取活动奖励",
    "sell_item": "出售物品",
    "clear_backpack": "清理背包",
    "post_account_for_sale": "发布账号出售",
    "submit_review": "提交评价",
    "contact_support": "联系客服",
    "change_nickname": "修改昵称",
    "click_exit_game_button": "点击退出按钮",
    "uninstall_game": "卸载游戏",
}

_STAMINA_ACTIONS = {"stamina_exhausted", "attempt_enter_dungeon_no_stamina"}


def _get_chinese_name(action: str) -> str:
    action_name = action.split("(")[0]
    return _ACTION_NAME_MAPPING.get(action_name, action_name)


def _attach_script_ctx(ctx: DashboardRenderContext, thread: Thread) -> None:
    if ctx.add_script_run_ctx is None:
        return
    try:
        ctx.add_script_run_ctx(thread)
    except Exception:
        return


def _increment_stamina_count(ctx: DashboardRenderContext, action_name: str, chinese_name: str) -> None:
    ctx.set("stamina_exhaustion_count", int(ctx.get("stamina_exhaustion_count", 0)) + 1)
    ctx.add_stamina_guide_log(f"执行动作: {chinese_name}")
    _maybe_start_stamina_guidance(ctx, action_name)


def _maybe_start_stamina_guidance(ctx: DashboardRenderContext, action_name: str) -> None:
    if action_name not in _STAMINA_ACTIONS:
        return

    rule_engine = ctx.get("rule_engine")
    if not rule_engine:
        return

    recent_actions = list(ctx.get("action_sequence", []))[-10:]
    action_names = [action["action"] for action in recent_actions]
    stamina_count = sum(1 for name in action_names if name in _STAMINA_ACTIONS)
    if stamina_count < 3:
        return

    ctx.add_stamina_guide_log("🚨 检测到体力耗尽模式，触发引导Agent")

    async def process_stamina_guide() -> None:
        from game_monitoring.agents.stamina_guide_agent import create_stamina_guide_agent

        stamina_agent = create_stamina_guide_agent()
        guide_message = f"玩家{ctx.current_player_id}体力耗尽次数达到阈值"
        ctx.add_stamina_guide_log(f"📤 发送引导消息: {guide_message}")

        response_stream = stamina_agent.run_stream(task=guide_message)
        final_response = None

        async for response in response_stream:
            if hasattr(response, "messages") and response.messages:
                final_response = response.messages[-1]
            elif hasattr(response, "chat_message"):
                final_response = response.chat_message

        results = list(ctx.get("stamina_guidance_results", []))
        if final_response and hasattr(final_response, "content"):
            response_text = final_response.content
            ctx.add_stamina_guide_log(f"💡 引导内容: {response_text}")
            results.append(
                {
                    "player_id": ctx.current_player_id,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "trigger_reason": f"体力耗尽次数达到{stamina_count}次",
                    "guidance_content": response_text,
                    "status": "success",
                }
            )
            ctx.add_stamina_guide_log("✅ 引导完成，结果已保存")
        else:
            ctx.add_stamina_guide_log(f"❌ 响应格式不正确: {type(final_response)}")
            results.append(
                {
                    "player_id": ctx.current_player_id,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "trigger_reason": f"体力耗尽次数达到{stamina_count}次",
                    "guidance_content": "引导失败: 响应格式错误",
                    "status": "error",
                }
            )

        ctx.set("stamina_guidance_results", results)

    def _run_stamina_guide_bg() -> None:
        loop = _asyncio.new_event_loop()
        try:
            _asyncio.set_event_loop(loop)
            loop.run_until_complete(process_stamina_guide())
        finally:
            try:
                loop.close()
            except Exception:
                pass

    thread = Thread(target=_run_stamina_guide_bg, name="stamina_guide_thread", daemon=True)
    _attach_script_ctx(ctx, thread)
    thread.start()


def render_dashboard_sections(ctx: DashboardRenderContext) -> None:
    """Render the three-column dashboard body."""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        render_left_panel(ctx)
    with col2:
        render_center_panel(ctx)
    with col3:
        render_right_panel(ctx)


def render_left_panel(ctx: DashboardRenderContext) -> None:
    """Render the player state panel."""
    st.markdown("<h2 class='section-header'>👤 玩家状态</h2>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='player-info'><strong>玩家ID:</strong> {ctx.current_player_id}</div>",
        unsafe_allow_html=True,
    )

    st.subheader("⚙️ 玩家属性设置")
    with st.expander("设置玩家属性", expanded=False):
        if ctx.player_state_manager:
            player_state = ctx.player_state_manager.get_player_state(ctx.current_player_id)
            player_name = st.text_input(
                "玩家姓名",
                value=player_state.player_name or "",
                key="player_name_input",
            )

            st.markdown("**队伍体力**")
            current_stamina = player_state.team_stamina or [100, 100, 100, 100]
            if not isinstance(current_stamina, list) or len(current_stamina) != 4:
                current_stamina = [100, 100, 100, 100]

            team_stamina_list = []
            for index, col in enumerate(st.columns(4)):
                with col:
                    team_stamina_list.append(
                        st.slider(
                            f"队伍 {index + 1}",
                            min_value=0,
                            max_value=150,
                            value=current_stamina[index],
                            key=f"team_stamina_{index}",
                        )
                    )

            backpack_items = st.text_area(
                "背包道具 (每行一个)",
                value="\n".join(player_state.backpack_items or []),
                key="backpack_items_input",
            )
            team_levels_input = st.text_input(
                "阵容等级 (用逗号分隔)",
                value=", ".join(map(str, player_state.team_levels or [])),
                key="team_levels_input",
            )
            skill_levels_input = st.text_input(
                "技能等级 (用逗号分隔)",
                value=", ".join(map(str, player_state.skill_levels or [])),
                key="skill_levels_input",
            )
            reserve_troops = st.number_input(
                "预备兵数量",
                min_value=0,
                value=player_state.reserve_troops or 0,
                key="reserve_troops_input",
            )

            if st.button("💾 更新玩家属性", key="update_player_attributes"):
                backpack_list = [item.strip() for item in backpack_items.split("\n") if item.strip()]
                team_levels_list = player_state.team_levels
                skill_levels_list = player_state.skill_levels

                try:
                    team_levels_list = [
                        int(level.strip()) for level in team_levels_input.split(",") if level.strip()
                    ]
                except ValueError:
                    st.error("阵容等级格式错误，请输入用逗号分隔的数字！")

                try:
                    skill_levels_list = [
                        int(level.strip()) for level in skill_levels_input.split(",") if level.strip()
                    ]
                except ValueError:
                    st.error("技能等级格式错误，请输入用逗号分隔的数字！")

                from .dashboard_runtime import sync_player_profile

                sync_player_profile(
                    ctx.runtime,
                    ctx.current_player_id,
                    display_name=player_name,
                    team_stamina=team_stamina_list,
                    backpack_items=backpack_list,
                    team_levels=team_levels_list,
                    skill_levels=skill_levels_list,
                    reserve_troops=reserve_troops,
                )
                ctx.add_agent_log(f"✅ 已更新玩家 {ctx.current_player_id} 的属性")
                st.success("玩家属性已更新！")
                st.rerun()

    if ctx.player_state_manager:
        player_state = ctx.player_state_manager.get_player_state(ctx.current_player_id)

        st.subheader("🎮 个性化属性")
        if player_state.player_name:
            st.write(f"**玩家姓名:** {player_state.player_name}")
        if player_state.team_stamina is not None:
            st.write(f"**队伍体力:** {player_state.team_stamina}/100")
        if player_state.backpack_items:
            preview = ", ".join(player_state.backpack_items[:3])
            suffix = "..." if len(player_state.backpack_items) > 3 else ""
            st.write(f"**背包道具:** {preview}{suffix}")
        if player_state.team_levels:
            st.write(f"**阵容等级:** {len(player_state.team_levels)} 个武将")
        if player_state.skill_levels:
            st.write(f"**技能等级:** {len(player_state.skill_levels)} 个技能")
        if player_state.reserve_troops is not None:
            st.write(f"**预备兵数量:** {player_state.reserve_troops}")

        st.subheader("😊 情绪状态")
        st.metric(
            "当前情绪",
            player_state.emotion or "未知",
            f"置信度: {float(player_state.emotion_confidence or 0.0):.2f}",
        )
        if player_state.emotion_keywords:
            st.write("关键词:", ", ".join(player_state.emotion_keywords))

        st.subheader("⚠️ 流失风险")
        st.metric(
            "风险等级",
            player_state.churn_risk_level or "未知",
            f"风险分数: {float(player_state.churn_risk_score or 0.0):.2f}",
        )
        if player_state.churn_risk_factors:
            st.write("风险因素:", ", ".join(player_state.churn_risk_factors))

        st.subheader("🤖 机器人检测")
        st.metric(
            "是否机器人",
            "是" if player_state.is_bot else "否",
            f"置信度: {float(player_state.bot_confidence or 0.0):.2f}",
        )
        if player_state.bot_patterns:
            st.write("检测模式:", ", ".join(player_state.bot_patterns))

        last_updated = getattr(player_state, "last_updated", None)
        if last_updated is not None and hasattr(last_updated, "strftime"):
            st.write(f"**最后更新:** {last_updated.strftime('%Y-%m-%d %H:%M:%S')}")

    st.subheader("📊 最近行为历史")
    if ctx.monitor and hasattr(ctx.monitor, "get_player_history"):
        recent_behaviors = ctx.monitor.get_player_history(ctx.current_player_id)[-5:]
        if recent_behaviors:
            for behavior in recent_behaviors:
                st.markdown(
                    "<div class='behavior-log'>"
                    f"{behavior.timestamp.strftime('%H:%M:%S')}: {behavior.action}"
                    "</div>",
                    unsafe_allow_html=True,
                )
        else:
            st.write("暂无行为记录")


def render_center_panel(ctx: DashboardRenderContext) -> None:
    """Render the dashboard center tabs."""
    st.markdown("<h2 class='section-header'>🤖 Agent 决策流程</h2>", unsafe_allow_html=True)
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📋 基础日志", "🧠 Agent团队分析", "⚡ 体力引导Agent", "⚔️ 军令操作"]
    )
    with tab1:
        render_basic_logs_tab(ctx)
    with tab2:
        render_team_analysis_tab(ctx)
    with tab3:
        render_stamina_tab(ctx)
    with tab4:
        render_orders_tab(ctx)

    st.subheader("📈 系统状态")
    if ctx.monitor and hasattr(ctx.monitor, "behavior_history"):
        total_behaviors = len(ctx.monitor.behavior_history)
        negative_counts = {
            player_id: ctx.monitor.get_negative_count(player_id)
            for player_id in ctx.get("player_negative_counts", {}).keys()
        } if hasattr(ctx.monitor, "get_negative_count") else {}
        current_player_count = (
            ctx.monitor.get_negative_count(ctx.current_player_id)
            if hasattr(ctx.monitor, "get_negative_count")
            else 0
        )
        action_sequence_length = len(ctx.get("action_sequence", []))

        col2_1, col2_2, col2_3, col2_4 = st.columns(4)
        with col2_1:
            st.metric("总行为记录", total_behaviors)
        with col2_2:
            st.metric("监控阈值", getattr(ctx.monitor, "threshold", 0))
        with col2_3:
            st.metric(
                "当前玩家负面行为",
                current_player_count,
                delta=1
                if current_player_count >= getattr(ctx.monitor, "threshold", 0)
                else None,
            )
        with col2_4:
            st.metric("动作序列长度", action_sequence_length)

        threshold = getattr(ctx.monitor, "threshold", 0)
        if current_player_count >= threshold:
            st.error(f"🚨 玩家 {ctx.current_player_id} 已达到分析阈值！")
        else:
            st.success(f"✅ 距离触发分析还需 {threshold - current_player_count} 次负面行为")

        if action_sequence_length > 0:
            st.info(f"📊 当前动作序列包含 {action_sequence_length} 个动作")
            recent_actions = [action["action"] for action in ctx.get("action_sequence", [])[-3:]]
            if recent_actions:
                st.write(f"**最近动作:** {' → '.join(recent_actions)}")

        if negative_counts:
            st.write("**所有玩家负面行为计数:**")
            for player_id, count in negative_counts.items():
                st.write(f"- {player_id}: {count}")


def _render_action_grid(actions: list[str], category_key: str, ctx: DashboardRenderContext, cols: int = 3) -> None:
    if not actions:
        return

    rows = (len(actions) + cols - 1) // cols
    for row in range(rows):
        columns = st.columns(cols)
        for col_idx in range(cols):
            action_idx = row * cols + col_idx
            if action_idx >= len(actions):
                continue

            action = actions[action_idx]
            action_name = action.split("(")[0]
            chinese_name = _get_chinese_name(action)

            with columns[col_idx]:
                if st.button(
                    chinese_name,
                    key=f"{category_key}_{action_idx}",
                    help=f"点击执行: {action}",
                    use_container_width=True,
                ):
                    ctx.run_async(
                        process_atomic_action(
                            ctx.session_state,
                            ctx.runtime,
                            ctx.current_player_id,
                            action_name,
                            add_behavior_log=ctx.add_behavior_log,
                            add_agent_log=ctx.add_agent_log,
                            store_team_analysis_result=ctx.store_team_analysis_result,
                        )
                    )
                    if action_name in _STAMINA_ACTIONS:
                        _increment_stamina_count(ctx, action_name, chinese_name)
                    st.rerun()


def render_right_panel(ctx: DashboardRenderContext) -> None:
    """Render the atomic action panel."""
    st.markdown("<h2 class='section-header'>🎯 原子动作界面</h2>", unsafe_allow_html=True)
    st.info("⚔️ 军令操作功能已移至【军令操作】标签页")

    action_definitions = ctx.get("action_definitions")
    if not action_definitions:
        return

    st.markdown("### 🎮 核心游戏动作")
    _render_action_grid(action_definitions.core_game_actions, "core", ctx, cols=3)

    st.markdown("### 👥 社交动作")
    _render_action_grid(action_definitions.social_actions, "social", ctx, cols=3)

    st.markdown("### 💰 经济动作")
    _render_action_grid(action_definitions.economic_actions, "economic", ctx, cols=3)

    st.markdown("### 📋 元数据动作")
    _render_action_grid(action_definitions.meta_actions, "meta", ctx, cols=3)

    st.markdown("### 📊 动作序列管理")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📋 查看序列", help="查看当前动作序列"):
            action_sequence = list(ctx.get("action_sequence", []))
            if action_sequence:
                st.info(f"当前序列长度: {len(action_sequence)}")
                for index, action in enumerate(action_sequence[-5:], start=1):
                    st.write(
                        f"{index}. {action['action']} "
                        f"({action['timestamp'].strftime('%H:%M:%S')})"
                    )
            else:
                st.info("动作序列为空")
    with col2:
        if st.button("🗑️ 清空序列", help="清空当前动作序列"):
            clear_action_sequence(ctx.session_state, ctx.monitor, ctx.current_player_id)
            ctx.add_agent_log("🗑️ 动作序列已清空")
            st.rerun()


def render_status_bar(ctx: DashboardRenderContext) -> None:
    """Render the dashboard footer status row."""
    st.markdown("---")
    status_col1, status_col2, status_col3 = st.columns(3)
    with status_col1:
        st.write(f"🕒 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    with status_col2:
        st.write(f"👤 当前玩家: {ctx.current_player_id}")
    with status_col3:
        system_status = "🟢 运行中" if ctx.system_initialized else "🔴 未初始化"
        st.write(f"⚙️ 系统状态: {system_status}")
