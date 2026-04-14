"""Helpers for storing and formatting v2 intervention results."""

from __future__ import annotations

from datetime import datetime
from typing import Any


def format_intervention_result(
    result: dict[str, Any], captured_at: datetime | None = None
) -> dict[str, Any]:
    """Normalize a v2 intervention result for dashboard rendering."""
    captured_at = captured_at or datetime.now()
    actions = result.get("final_actions", []) or []

    return {
        "player_id": result.get("player_id", "unknown"),
        "session_id": result.get("session_id", "unknown"),
        "worker_count": result.get("worker_count", 0),
        "overall_confidence": round(float(result.get("overall_confidence", 0.0)), 3),
        "final_actions": actions,
        "action_labels": [action.get("action_type", "unknown") for action in actions],
        "captured_at": captured_at.strftime("%Y-%m-%d %H:%M:%S"),
    }


def store_intervention_result(
    history: list[dict[str, Any]],
    result: dict[str, Any],
    *,
    captured_at: datetime | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Append a formatted result and retain only the latest entries."""
    updated_history = list(history)
    updated_history.append(format_intervention_result(result, captured_at=captured_at))
    if limit > 0:
        updated_history = updated_history[-limit:]
    return updated_history
