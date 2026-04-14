"""Dashboard session-state and logging helpers."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, MutableMapping

from ..simulator.behavior_simulator import PlayerBehaviorRuleEngine
from ..simulator.player_behavior import PlayerActionDefinitions

DEFAULT_PLAYER_ID = "孤独的凤凰战士"


class TeamAnalysisLogCapture:
    """Capture team-analysis stdout while keeping session state synchronized."""

    def __init__(
        self,
        session_state: MutableMapping[str, Any],
        *,
        session_key: str = "team_analysis_logs",
        max_logs: int = 10000,
        timestamp_factory: Callable[[], str] | None = None,
    ):
        self._session_state = session_state
        self._session_key = session_key
        self._max_logs = max_logs
        self._timestamp_factory = timestamp_factory or (lambda: "")
        self._logs: list[str] = []
        self._is_capturing = False

    def start_capture(self) -> None:
        self._is_capturing = True
        self._logs.clear()
        self._session_state[self._session_key] = []

    def stop_capture(self) -> None:
        self._is_capturing = False

    def write(self, text: str) -> None:
        if not self._is_capturing or not text.strip():
            return

        timestamp = self._timestamp_factory()
        entry = f"[{timestamp}] {text.strip()}" if timestamp else text.strip()
        self._logs.append(entry)
        if len(self._logs) > self._max_logs:
            self._logs = self._logs[-self._max_logs :]
        self._session_state[self._session_key] = self._logs.copy()

    def flush(self) -> None:
        """Compatibility no-op for stdout-like usage."""

    def get_all_logs(self) -> list[str]:
        return self._logs.copy()

    def clear_logs(self) -> None:
        self._logs.clear()
        self._session_state[self._session_key] = []


def append_dashboard_log(
    session_state: MutableMapping[str, Any],
    key: str,
    message: str,
    *,
    limit: int,
    timestamp_factory: Callable[[], str],
) -> str:
    """Append a timestamped dashboard log entry and retain only the latest entries."""
    entry = f"[{timestamp_factory()}] {message}"
    logs = list(session_state.get(key, []))
    logs.append(entry)
    if limit > 0 and len(logs) > limit:
        logs = logs[-limit:]
    session_state[key] = logs
    return entry


def append_action_sequence_entry(
    session_state: MutableMapping[str, Any],
    player_id: str,
    action_name: str,
    *,
    timestamp: Any,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Record a UI action entry for later display."""
    entry = {
        "action": action_name,
        "params": params or {},
        "timestamp": timestamp,
        "player_id": player_id,
    }
    sequence = list(session_state.get("action_sequence", []))
    sequence.append(entry)
    session_state["action_sequence"] = sequence
    return entry


def ensure_dashboard_state(
    session_state: MutableMapping[str, Any],
    *,
    action_definitions_factory: Callable[[], Any] | None = None,
    rule_engine_factory: Callable[[], Any] | None = None,
    team_capture_factory: Callable[[MutableMapping[str, Any]], Any] | None = None,
) -> None:
    """Ensure all dashboard session keys exist."""
    defaults = {
        "system": None,
        "monitor": None,
        "player_state_manager": None,
        "current_player_id": DEFAULT_PLAYER_ID,
        "behavior_logs": [],
        "agent_logs": [],
        "system_initialized": False,
        "team_analysis_logs": [],
        "team_analysis_results": [],
        "player_negative_counts": {},
        "stamina_guidance_results": [],
        "action_sequence": [],
        "batch_generated_orders": None,
        "single_generated_order": None,
        "batch_generation_in_progress": False,
        "batch_generation_total": 0,
        "batch_generation_processed": 0,
        "batch_generation_error": None,
        "stamina_exhaustion_count": 0,
        "stamina_guide_logs": [],
    }

    for key, value in defaults.items():
        if key not in session_state:
            session_state[key] = value

    if "action_definitions" not in session_state:
        factory = action_definitions_factory or PlayerActionDefinitions
        session_state["action_definitions"] = factory()

    if "rule_engine" not in session_state:
        factory = rule_engine_factory or PlayerBehaviorRuleEngine
        session_state["rule_engine"] = factory()

    if "team_analysis_capture" not in session_state:
        factory = team_capture_factory or (
            lambda mapping: TeamAnalysisLogCapture(
                mapping,
                timestamp_factory=lambda: datetime.now().strftime("%H:%M:%S.%f")[:-3],
            )
        )
        session_state["team_analysis_capture"] = factory(session_state)
