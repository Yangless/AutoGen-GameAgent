"""Shared render context for the Streamlit dashboard UI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping, MutableMapping


@dataclass
class DashboardRenderContext:
    """Carry shared dashboard render dependencies across section modules."""

    session_state: Any
    runtime: Mapping[str, Any]
    monitor: Any
    player_state_manager: Any
    run_async: Callable[[Any], Any]
    add_agent_log: Callable[[str], None]
    add_behavior_log: Callable[[str, str], None]
    add_stamina_guide_log: Callable[[str], None]
    store_team_analysis_result: Callable[[dict[str, Any]], None]
    add_script_run_ctx: Callable[[Any], None] | None = None

    def get(self, key: str, default: Any = None) -> Any:
        """Read a session value from either a mapping or an attribute object."""
        state = self.session_state
        if isinstance(state, Mapping):
            return state.get(key, default)
        return getattr(state, key, default)

    def set(self, key: str, value: Any) -> Any:
        """Write a session value to either a mapping or an attribute object."""
        state = self.session_state
        if isinstance(state, MutableMapping):
            state[key] = value
        else:
            setattr(state, key, value)
        return value

    def append(self, key: str, value: Any) -> list[Any]:
        """Append a value onto a list-like session field."""
        items = list(self.get(key, []))
        items.append(value)
        self.set(key, items)
        return items

    @property
    def current_player_id(self) -> str:
        return str(self.get("current_player_id", ""))

    @property
    def system_initialized(self) -> bool:
        return bool(self.get("system_initialized", False))
