"""Dashboard action and intervention orchestration helpers."""

from __future__ import annotations

import sys
from datetime import datetime
from typing import Any, Callable, Mapping, MutableMapping

from .dashboard_session import append_action_sequence_entry


def _normalize_triggered_scenarios(triggered_rules: list[Any]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for rule in triggered_rules:
        if isinstance(rule, dict):
            normalized.append(
                {
                    "scenario": str(rule.get("scenario", "")),
                    "description": str(rule.get("description", "")),
                }
            )
            continue

        normalized.append(
            {
                "scenario": str(getattr(rule, "scenario", "")),
                "description": str(getattr(rule, "description", "")),
            }
        )
    return normalized


async def trigger_intervention(
    session_state: MutableMapping[str, Any],
    runtime: Mapping[str, Any],
    player_id: str,
    *,
    add_agent_log: Callable[[str], None],
    store_team_analysis_result: Callable[[dict[str, Any]], None],
) -> Any:
    """Trigger the async intervention flow and persist any structured result."""
    team_capture = session_state.get("team_analysis_capture")
    monitor = runtime["monitor"]
    agent_service = runtime["agent_service"]
    original_stdout = sys.stdout

    try:
        if hasattr(team_capture, "start_capture"):
            team_capture.start_capture()
        if hasattr(team_capture, "write"):
            sys.stdout = team_capture

        intervention = await agent_service.trigger_intervention(player_id)
        payload = getattr(intervention, "payload", None)
        if isinstance(payload, dict):
            store_team_analysis_result(payload)

        if hasattr(monitor, "reset_negative_count"):
            monitor.reset_negative_count(player_id)

        add_agent_log(f"🎯 已触发玩家 {player_id} 的智能体分析和干预")
        return intervention
    except Exception as exc:
        add_agent_log(f"❌ 触发干预时出错: {exc}")
        return None
    finally:
        sys.stdout = original_stdout
        if hasattr(team_capture, "stop_capture"):
            team_capture.stop_capture()


async def process_atomic_action(
    session_state: MutableMapping[str, Any],
    runtime: Mapping[str, Any],
    player_id: str,
    action_name: str,
    *,
    add_behavior_log: Callable[[str, str], None],
    add_agent_log: Callable[[str], None],
    store_team_analysis_result: Callable[[dict[str, Any]], None],
) -> Any:
    """Record an atomic action, log rule analysis, and trigger intervention if needed."""
    monitor = runtime["monitor"]
    action_service = runtime["action_service"]

    append_action_sequence_entry(
        session_state,
        player_id,
        action_name,
        timestamp=datetime.now(),
    )
    add_behavior_log(player_id, action_name)
    add_agent_log(f"🎯 执行动作: {action_name}")

    result = await action_service.process_action(player_id, action_name)
    triggered_scenarios = _normalize_triggered_scenarios(
        list(getattr(result, "triggered_rules", []))
    )

    full_sequence = (
        monitor.get_player_action_sequence(player_id)
        if hasattr(monitor, "get_player_action_sequence")
        else []
    )
    recent_actions = (
        monitor.get_recent_actions_for_analysis(player_id)
        if hasattr(monitor, "get_recent_actions_for_analysis")
        else full_sequence[-3:]
    )

    add_agent_log(
        f"📋 完整动作序列 ({len(full_sequence)} 个): {[a['action'] for a in full_sequence]}"
    )
    add_agent_log(
        f"🔍 分析窗口 ({len(recent_actions)} 个): {[a['action'] for a in recent_actions]}"
    )

    if triggered_scenarios:
        add_agent_log(f"🎭 触发场景数量: {len(triggered_scenarios)}")
        for index, scenario in enumerate(triggered_scenarios, start=1):
            add_agent_log(
                f"   {index}. {scenario.get('scenario', '未知场景')}: {scenario.get('description', '无描述')}"
            )
    else:
        add_agent_log("🎭 未触发任何场景")

    final_emotion_type = "neutral"
    if triggered_scenarios and hasattr(monitor, "rule_engine"):
        rule_engine = monitor.rule_engine
        if hasattr(rule_engine, "get_emotion_type_from_scenarios"):
            final_emotion_type = rule_engine.get_emotion_type_from_scenarios(
                triggered_scenarios
            )
            add_agent_log(f"📈 序列分析情绪: {final_emotion_type}")

    current_count = int(getattr(result, "current_negative_count", 0))
    session_state.setdefault("player_negative_counts", {})[player_id] = current_count

    if final_emotion_type == "negative":
        add_agent_log(f"⚠️ 检测到消极行为，计数更新: {current_count}")

    if getattr(result, "should_intervene", False):
        add_agent_log(
            f"🚨 玩家 {player_id} 达到负面行为阈值 ({current_count}/{monitor.threshold})"
        )
        await trigger_intervention(
            session_state,
            runtime,
            player_id,
            add_agent_log=add_agent_log,
            store_team_analysis_result=store_team_analysis_result,
        )
        session_state["player_negative_counts"][player_id] = (
            monitor.get_negative_count(player_id)
            if hasattr(monitor, "get_negative_count")
            else 0
        )
        add_agent_log(f"🔄 重置玩家 {player_id} 的负面行为计数为0")

    current_negative_count = (
        monitor.get_negative_count(player_id) if hasattr(monitor, "get_negative_count") else 0
    )
    sequence_length = len(full_sequence)
    add_agent_log(
        f"📊 状态更新完成 - 负面计数: {current_negative_count}/{monitor.threshold}, 序列长度: {sequence_length}"
    )
    return result
