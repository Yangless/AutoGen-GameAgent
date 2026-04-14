"""Tab-level renderers extracted from the Streamlit dashboard entrypoint."""

from __future__ import annotations

import json
from datetime import datetime
from threading import Thread
from typing import Any

import streamlit as st

from .dashboard_orders import run_batch_generation
from .dashboard_render_context import DashboardRenderContext
from .dashboard_runtime import (
    get_commander_order,
    get_player_names,
    set_commander_order,
)


def _get_team_analysis_logs(ctx: DashboardRenderContext) -> list[str]:
    capture = ctx.get("team_analysis_capture")
    if capture and hasattr(capture, "get_all_logs"):
        return list(capture.get_all_logs())
    return []


def _set_order_generation_state(ctx: DashboardRenderContext, **values: Any) -> None:
    for key, value in values.items():
        ctx.set(key, value)


def _safe_commander_order(ctx: DashboardRenderContext) -> str:
    try:
        return get_commander_order(ctx.runtime)
    except Exception:
        return ""


def _safe_player_names(ctx: DashboardRenderContext) -> list[str]:
    try:
        return list(get_player_names(ctx.runtime))
    except Exception:
        return []


def _attach_script_ctx(ctx: DashboardRenderContext, thread: Thread) -> None:
    if ctx.add_script_run_ctx is None:
        return
    try:
        ctx.add_script_run_ctx(thread)
    except Exception:
        return


def render_basic_logs_tab(ctx: DashboardRenderContext) -> None:
    """Render the basic dashboard logs tab."""
    logs = list(ctx.get("agent_logs", []))
    if logs:
        for log in reversed(logs):
            st.markdown(f"<div class='agent-log'>{log}</div>", unsafe_allow_html=True)
        return
    st.info("等待系统活动...")


def render_team_analysis_tab(ctx: DashboardRenderContext) -> None:
    """Render team analysis logs and structured intervention results."""
    st.markdown("**🧠 团队分析实时日志**")

    col_clear, col_count = st.columns([1, 3])
    with col_clear:
        if st.button("🗑️ 清空日志", key="clear_team_logs"):
            capture = ctx.get("team_analysis_capture")
            if capture and hasattr(capture, "clear_logs"):
                capture.clear_logs()
            ctx.set("team_analysis_results", [])
            st.rerun()

    with col_count:
        result_count = len(ctx.get("team_analysis_results", []))
        st.write(f"📊 当前日志条数: {len(_get_team_analysis_logs(ctx))} | 结果数: {result_count}")

    results = list(ctx.get("team_analysis_results", []))
    if results:
        st.markdown("**🎯 最新结构化决策结果**")
        for index, result in enumerate(reversed(results[-3:]), start=1):
            title = (
                f"{result['player_id']} | {result['captured_at']} | "
                f"{len(result['action_labels'])} actions"
            )
            with st.expander(title, expanded=(index == 1)):
                st.markdown(f"**会话ID:** `{result['session_id']}`")
                st.markdown(f"**Worker 数量:** {result['worker_count']}")
                st.markdown(f"**综合置信度:** {result['overall_confidence']:.2f}")
                if result["action_labels"]:
                    st.markdown(f"**动作类型:** {', '.join(result['action_labels'])}")
                if result["final_actions"]:
                    st.json(result["final_actions"])
                else:
                    st.info("无最终动作。")

    team_logs = _get_team_analysis_logs(ctx)
    if team_logs:
        log_entries_html = "".join(
            f"<div class='agent-log'>{log}</div>" for log in team_logs
        )
        log_container_html = (
            "<div class='log-container' style='height: 400px; overflow-y: auto; "
            "border: 1px solid #ddd; border-radius: 5px; padding: 10px; "
            "background-color: #f9f9f9; margin-bottom: 1rem;'>"
            f"{log_entries_html}</div>"
        )
        st.markdown(log_container_html, unsafe_allow_html=True)
        st.markdown(
            """
            <script>
            setTimeout(function() {
                var container = document.querySelector('.log-container');
                if (container) {
                    container.scrollTop = container.scrollHeight;
                }
            }, 100);
            </script>
            """,
            unsafe_allow_html=True,
        )
        return

    st.info(
        "💭 等待Agent团队分析...\n\n当检测到玩家负面行为达到阈值时，"
        "系统将自动触发多智能体团队分析，所有分析过程将在此处实时显示。"
    )


def render_stamina_tab(ctx: DashboardRenderContext) -> None:
    """Render stamina-guide logs and generated guidance."""
    st.markdown("**⚡ 体力引导Agent监控**")

    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.markdown("**📋 体力引导日志**")
        btn_col1, btn_col2, btn_col3 = st.columns(3)
        with btn_col1:
            if st.button("🔄 刷新", key="refresh_stamina_tab_logs"):
                st.rerun()
        with btn_col2:
            if st.button("🗑️ 清空", key="clear_stamina_tab_logs"):
                ctx.set("stamina_guide_logs", [])
                st.rerun()
        with btn_col3:
            if ctx.get("batch_generation_in_progress", False):
                st.write("批量军令生成中")

        logs = list(ctx.get("stamina_guide_logs", []))
        if logs:
            log_container_html = (
                "<div class='log-container' style='height: 200px; overflow-y: auto; "
                "border: 1px solid #ddd; border-radius: 5px; padding: 10px; "
                "background-color: #f9f9f9;'>"
                + "".join(f"<div class='agent-log'>{log}</div>" for log in logs)
                + "</div>"
            )
            st.markdown(log_container_html, unsafe_allow_html=True)
        else:
            st.info("💡 暂无体力引导日志，请执行体力相关动作。")

        st.markdown("**🎯 个性化引导结果**")
        results = list(ctx.get("stamina_guidance_results", []))
        if results:
            for index, result in enumerate(reversed(results[-5:]), start=1):
                status_icon = "✅" if result["status"] == "success" else "❌"
                with st.expander(
                    f"{status_icon} {result['player_id']} - {result['timestamp']}",
                    expanded=(index == 1),
                ):
                    st.markdown(f"**触发原因:** {result['trigger_reason']}")
                    st.markdown("**引导内容:**")
                    if result["status"] == "success":
                        st.success(result["guidance_content"])
                    else:
                        st.error(result["guidance_content"])
                    st.markdown(f"**状态:** {result['status']}")
        else:
            st.info("💡 暂无个性化引导结果，当体力耗尽次数达到阈值时将自动生成。")

    with col_right:
        st.markdown("**📊 体力统计**")
        st.metric("体力耗尽次数", ctx.get("stamina_exhaustion_count", 0))
        st.metric("日志条数", len(ctx.get("stamina_guide_logs", [])))


def render_orders_tab(ctx: DashboardRenderContext) -> None:
    """Render military-order generation, preview, and send actions."""
    st.markdown("**⚔️ 军令操作中心**")

    st.subheader("⚔️ 多玩家个性化军令生成")
    with st.expander("批量生成军令", expanded=False):
        st.markdown("### 📋 指挥官总军令")
        commander_order = st.text_area(
            "输入指挥官总军令：",
            value=_safe_commander_order(ctx),
            height=200,
            key="commander_order_input_tab4",
        )

        st.markdown("### 👥 选择玩家")
        available_players = _safe_player_names(ctx)

        if available_players:
            selected_players = st.multiselect(
                "选择要生成军令的玩家：",
                options=available_players,
                default=available_players,
                key="selected_players_tab4",
            )

            if st.button("🎯 批量生成个性化军令", key="generate_batch_military_orders_tab4"):
                if selected_players and commander_order.strip():
                    if ctx.get("batch_generation_in_progress", False):
                        st.warning("⚠️ 另一项批量生成任务正在进行中，请稍候...")
                    else:
                        set_commander_order(ctx.runtime, commander_order.strip())

                        from game_monitoring.tools.military_order_tool import (
                            generate_military_order_with_llm,
                        )

                        _set_order_generation_state(
                            ctx,
                            batch_generated_orders=[],
                            batch_generation_in_progress=True,
                            batch_generation_total=len(selected_players),
                            batch_generation_processed=0,
                            batch_generation_error=None,
                        )

                        thread = Thread(
                            target=run_batch_generation,
                            args=(
                                ctx.session_state,
                                ctx.runtime,
                                list(selected_players),
                                commander_order.strip(),
                                generate_military_order_with_llm,
                            ),
                            daemon=True,
                        )
                        _attach_script_ctx(ctx, thread)
                        thread.start()
                        st.info(
                            f"⏳ 已开始批量生成 {len(selected_players)} 名玩家的个性化军令，"
                            "结果将实时显示在下方。"
                        )
                        st.rerun()
                else:
                    if not selected_players:
                        st.warning("⚠️ 请选择至少一个玩家")
                    if not commander_order.strip():
                        st.warning("⚠️ 请输入指挥官总军令")
        else:
            st.info("ℹ️ 暂无可用玩家，请先在上下文中添加玩家信息")

    st.subheader("⚔️ 个性化军令预览")

    batch_generated_orders = ctx.get("batch_generated_orders")
    single_generated_order = ctx.get("single_generated_order")

    if batch_generated_orders:
        st.markdown("### 📋 批量生成的军令预览")
        for order in batch_generated_orders:
            player_name = order.get("player_name", "未知玩家")
            player_id = order.get("player_id", "unknown")
            with st.expander(f"👤 {player_name} ({player_id})", expanded=False):
                st.markdown("### 📜 军令内容")
                military_order_content = order.get("military_order", "军令内容未找到")
                st.markdown(f"```\n{military_order_content}\n```")

                teams_info = order.get("teams_info", [])
                if teams_info:
                    st.markdown("### 👥 队伍信息")
                    for team in teams_info:
                        st.write(
                            f"• **队伍{team.get('team_number', 'N/A')}**: "
                            f"{team.get('level', 'N/A')}级, "
                            f"体力{team.get('stamina', 'N/A')}%, "
                            f"能力: {team.get('capability', 'N/A')}"
                        )
                        st.write(f"  任务安排: {team.get('assignment', 'N/A')}")

        if st.button("🗑️ 清除批量结果", key="clear_batch_results_tab4"):
            _set_order_generation_state(
                ctx,
                batch_generated_orders=None,
                batch_generation_in_progress=False,
                batch_generation_total=0,
                batch_generation_processed=0,
                batch_generation_error=None,
            )
            st.rerun()
    elif single_generated_order:
        st.markdown("### 👤 单个玩家军令预览")

        player_name = single_generated_order.get("player_name", "未知玩家")
        player_id = single_generated_order.get("player_id", "unknown")
        st.markdown(f"**玩家**: {player_name} ({player_id})")
        st.markdown("### 📜 军令内容")
        military_order_content = single_generated_order.get(
            "military_order",
            "军令内容未找到",
        )
        st.markdown(f"```\n{military_order_content}\n```")

        if st.button("🗑️ 清除单个军令", key="clear_single_result_tab4"):
            ctx.set("single_generated_order", None)
            st.rerun()
    else:
        st.info("💡 暂无生成的军令，请先生成批量军令或单个玩家军令。")

    with st.expander("单个玩家军令生成", expanded=False):
        if st.button("🎯 生成当前玩家军令预览", key="generate_single_military_order_preview_tab4"):
            if ctx.player_state_manager:
                from game_monitoring.tools.military_order_tool import (
                    generate_personalized_military_order,
                )

                player_state = ctx.player_state_manager.get_player_state(ctx.current_player_id)
                military_order = generate_personalized_military_order(
                    player_id=ctx.current_player_id,
                    player_name=player_state.player_name or "勇士",
                    team_stamina=player_state.team_stamina or 50,
                    backpack_items=player_state.backpack_items or [],
                    team_levels=player_state.team_levels or {},
                    skill_levels=player_state.skill_levels or {},
                    reserve_troops=player_state.reserve_troops or 0,
                )

                ctx.set(
                    "single_generated_order",
                    {
                        "player_id": ctx.current_player_id,
                        "player_name": player_state.player_name or "勇士",
                        "military_order": military_order,
                        "timestamp": datetime.now(),
                    },
                )
                ctx.set("batch_generated_orders", None)

                st.success(
                    f"✅ 已生成玩家 {player_state.player_name or '勇士'} 的个性化军令！"
                    "军令预览将自动显示在下方"
                )
                ctx.add_agent_log(f"🎯 已生成玩家 {ctx.current_player_id} 的个性化军令预览")
                st.rerun()
            else:
                st.error("玩家状态管理器未初始化")

    st.subheader("📤 发送军令")
    with st.expander("发送军令给玩家", expanded=False):
        st.markdown("### 选择发送方式")

        batch_generated_orders = ctx.get("batch_generated_orders")
        if batch_generated_orders:
            st.markdown("#### 📋 批量发送军令")
            if st.button("📤 发送所有批量生成的军令", key="send_batch_military_orders_tab4"):
                from game_monitoring.tools.military_order_tool import send_military_order

                success_count = 0
                total_count = len(batch_generated_orders)
                for order in batch_generated_orders:
                    player_name = order.get("player_name", "未知玩家")
                    military_order = order.get("military_order", "")

                    if military_order:
                        try:
                            result_string = send_military_order(
                                order.get("player_id", "unknown"),
                                military_order,
                            )
                            result_dict = json.loads(result_string)
                            if result_dict.get("status") == "success":
                                success_count += 1
                                ctx.add_agent_log(f"✔️ 成功发送军令给 {player_name}")
                            else:
                                ctx.add_agent_log(
                                    "❌ 发送军令给 "
                                    f"{player_name} 失败: {result_dict.get('message', '未知错误')}"
                                )
                        except Exception as exc:
                            ctx.add_agent_log(f"❌ 发送军令给 {player_name} 异常: {exc}")

                if success_count == total_count:
                    st.success(f"✅ 成功发送所有 {total_count} 份军令！")
                elif success_count > 0:
                    st.warning(f"⚠️ 成功发送 {success_count}/{total_count} 份军令")
                else:
                    st.error("❌ 所有军令发送失败")

            st.markdown("---")

        st.markdown("#### 👤 单个玩家发送军令")
        if st.button("📤 发送当前玩家军令", key="send_single_military_order_tab4"):
            if ctx.player_state_manager:
                from game_monitoring.tools.military_order_tool import (
                    generate_personalized_military_order,
                    send_military_order,
                )

                player_state = ctx.player_state_manager.get_player_state(ctx.current_player_id)
                military_order = generate_personalized_military_order(
                    player_id=ctx.current_player_id,
                    player_name=player_state.player_name or "勇士",
                    team_stamina=player_state.team_stamina or 50,
                    backpack_items=player_state.backpack_items or [],
                    team_levels=player_state.team_levels or {},
                    skill_levels=player_state.skill_levels or {},
                    reserve_troops=player_state.reserve_troops or 0,
                )

                try:
                    result_string = send_military_order(ctx.current_player_id, military_order)
                    result_dict = json.loads(result_string)
                    if result_dict.get("status") == "success":
                        st.success(f"✅ 成功发送军令给 {player_state.player_name or '勇士'}！")
                        ctx.add_agent_log(f"✔️ 成功发送军令给玩家 {ctx.current_player_id}")
                    else:
                        st.error(f"❌ 发送失败: {result_dict.get('message', '未知错误')}")
                        ctx.add_agent_log(
                            f"❌ 发送军令失败: {result_dict.get('message', '未知错误')}"
                        )
                except Exception as exc:
                    st.error(f"❌ 发送异常: {exc}")
                    ctx.add_agent_log(f"❌ 发送军令异常: {exc}")
            else:
                st.error("玩家状态管理器未初始化")
