"""Dashboard military-order batch helpers."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Callable, Mapping, MutableMapping


def _build_missing_player_result(player_name: str, captured_at: datetime) -> dict[str, Any]:
    return {
        "player_name": player_name,
        "player_id": "unknown",
        "military_order": "",
        "teams_info": [],
        "error": f"未找到玩家信息: {player_name}",
        "timestamp": captured_at,
    }


def _build_error_result(
    player_name: str,
    player_id: str,
    error: str,
    captured_at: datetime,
) -> dict[str, Any]:
    return {
        "player_name": player_name,
        "player_id": player_id,
        "military_order": "",
        "teams_info": [],
        "error": error,
        "timestamp": captured_at,
    }


def _build_success_result(result: dict[str, Any], player_name: str, captured_at: datetime) -> dict[str, Any]:
    return {
        "player_name": result.get("player_name", player_name),
        "player_id": result.get("player_id", player_name.lower().replace(" ", "_")),
        "military_order": result.get("military_order", ""),
        "teams_info": result.get("team_analysis", []),
        "timestamp": captured_at,
    }


def run_batch_generation(
    session_state: MutableMapping[str, Any],
    runtime: Mapping[str, Any],
    selected_players: list[str],
    commander_order: str,
    generate_military_order_with_llm: Callable[..., str],
    *,
    now_factory: Callable[[], datetime] = datetime.now,
) -> None:
    """Generate personalized military orders for a set of players and track progress."""
    repo = runtime["player_repository"]
    session_state.setdefault("batch_generated_orders", [])
    session_state.setdefault("batch_generation_processed", 0)
    session_state.setdefault("batch_generation_error", None)

    try:
        for player_name in selected_players:
            entity = repo.get_by_name(player_name)
            captured_at = now_factory()

            if entity is None:
                session_state["batch_generated_orders"].append(
                    _build_missing_player_result(player_name, captured_at)
                )
                session_state["batch_generation_processed"] += 1
                continue

            try:
                result_str = generate_military_order_with_llm(
                    player_name=entity.player_name or player_name,
                    player_id=entity.player_id or player_name.lower().replace(" ", "_"),
                    team_stamina=entity.team_stamina,
                    backpack_items=entity.backpack_items,
                    team_levels=entity.team_levels,
                    skill_levels=entity.skill_levels,
                    reserve_troops=entity.reserve_troops,
                    commander_order=commander_order,
                )
                result = json.loads(result_str)
                session_state["batch_generated_orders"].append(
                    _build_success_result(result, player_name, captured_at)
                )
            except Exception as exc:
                session_state["batch_generated_orders"].append(
                    _build_error_result(
                        player_name,
                        entity.player_id or player_name.lower().replace(" ", "_"),
                        str(exc),
                        captured_at,
                    )
                )
                session_state["batch_generation_error"] = str(exc)
            finally:
                session_state["batch_generation_processed"] += 1
    except Exception as exc:
        session_state["batch_generation_error"] = f"批量生成线程异常: {exc}"
    finally:
        session_state["batch_generation_in_progress"] = False
