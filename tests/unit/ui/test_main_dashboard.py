import asyncio
import importlib
import sys
import types
from types import SimpleNamespace
from unittest.mock import AsyncMock

from tests.unit.ui.streamlit_test_double import install_streamlit_test_double

streamlit_stub = install_streamlit_test_double()

main_dashboard = importlib.import_module("game_monitoring.ui.pages.main_dashboard")
get_rule_label = main_dashboard.get_rule_label
process_dashboard_action = main_dashboard.process_dashboard_action


def test_get_rule_label_prefers_v2_scenario_field():
    rule = SimpleNamespace(scenario="negative_behavior", scenario_name="legacy_name")

    assert get_rule_label(rule) == "negative_behavior"


def test_process_dashboard_action_triggers_agent_service_when_needed():
    action_result = SimpleNamespace(
        player_id="player_1",
        action_name="sell_item",
        triggered_rules=[SimpleNamespace(scenario="negative_behavior")],
        should_intervene=True,
    )
    action_service = AsyncMock()
    action_service.process_action = AsyncMock(return_value=action_result)
    intervention = SimpleNamespace(success=True, payload={"player_id": "player_1"})
    agent_service = AsyncMock()
    agent_service.trigger_intervention = AsyncMock(return_value=intervention)

    outcome = asyncio.run(
        process_dashboard_action(
            action_service,
            agent_service,
            "player_1",
            "sell_item",
        )
    )

    assert outcome.result is action_result
    assert outcome.rule_labels == ["negative_behavior"]
    assert outcome.intervention is intervention
    agent_service.trigger_intervention.assert_awaited_once_with("player_1")


def test_streamlit_dashboard_main_delegates_rendering(monkeypatch):
    streamlit_stub.session_state.clear()
    streamlit_stub.session_state.system_initialized = True
    streamlit_stub.session_state.system = {"runtime": True}
    streamlit_stub.session_state.monitor = object()
    streamlit_stub.session_state.player_state_manager = object()
    calls = []

    dashboard_module = importlib.import_module("streamlit_dashboard")
    dashboard_module = importlib.reload(dashboard_module)

    monkeypatch.setattr(
        dashboard_module,
        "render_dashboard_sections",
        lambda ctx: calls.append("sections"),
    )
    monkeypatch.setattr(
        dashboard_module,
        "render_status_bar",
        lambda ctx: calls.append("status"),
    )

    dashboard_module.main()

    assert calls == ["sections", "status"]
