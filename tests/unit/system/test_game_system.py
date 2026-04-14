import importlib
import sys
import types
import asyncio
import inspect

from game_monitoring.team.team_manager import GameMonitoringTeamV2


def test_game_player_monitoring_system_uses_v2_team(monkeypatch):
    """系统主入口默认使用新版 TeamManager。"""
    config_module = types.ModuleType("config")
    config_module.custom_model_client = None
    monkeypatch.setitem(sys.modules, "config", config_module)

    game_system_module = importlib.import_module("game_monitoring.system.game_system")
    game_system_module = importlib.reload(game_system_module)

    system = game_system_module.GamePlayerMonitoringSystem(model_client=None)

    assert isinstance(system.team, GameMonitoringTeamV2)


def test_game_player_monitoring_system_no_longer_exposes_legacy_runtime_switch(monkeypatch):
    """系统主入口不再暴露 legacy runtime 开关。"""
    config_module = types.ModuleType("config")
    config_module.custom_model_client = None
    monkeypatch.setitem(sys.modules, "config", config_module)

    game_system_module = importlib.import_module("game_monitoring.system.game_system")
    game_system_module = importlib.reload(game_system_module)

    parameters = inspect.signature(
        game_system_module.GamePlayerMonitoringSystem.__init__
    ).parameters

    legacy_runtime_parameter = "use_v2" + "_runtime"

    assert legacy_runtime_parameter not in parameters


def test_game_player_monitoring_system_bootstraps_context_with_repositories(monkeypatch):
    """系统主入口创建的上下文应带上仓储依赖。"""
    config_module = types.ModuleType("config")
    config_module.custom_model_client = None
    monkeypatch.setitem(sys.modules, "config", config_module)

    game_system_module = importlib.import_module("game_monitoring.system.game_system")
    game_system_module = importlib.reload(game_system_module)

    system = game_system_module.GamePlayerMonitoringSystem(model_client=None)

    assert system.context.player_repository is not None
    assert system.context.commander_order_repository is not None


def test_game_player_monitoring_system_uses_bootstrap_application(monkeypatch):
    """系统主入口应复用 bootstrap_application，而不是手动写兼容全局上下文。"""
    config_module = types.ModuleType("config")
    config_module.custom_model_client = None
    monkeypatch.setitem(sys.modules, "config", config_module)

    game_system_module = importlib.import_module("game_monitoring.system.game_system")
    game_system_module = importlib.reload(game_system_module)

    source = inspect.getsource(game_system_module.GamePlayerMonitoringSystem.__init__)

    assert "bootstrap_application" in source
    assert "set_global_context" not in source


def test_game_player_monitoring_system_logs_v2_intervention_result(monkeypatch):
    """系统主入口会输出 v2 干预结果摘要，供控制台和 Streamlit 捕获。"""
    config_module = types.ModuleType("config")
    config_module.custom_model_client = None
    monkeypatch.setitem(sys.modules, "config", config_module)

    game_system_module = importlib.import_module("game_monitoring.system.game_system")
    game_system_module = importlib.reload(game_system_module)

    system = game_system_module.GamePlayerMonitoringSystem(model_client=None)

    class FakeUI:
        def __init__(self):
            self.activation_player_id = None
            self.intervention_result = None

        def print_team_activation(self, player_id):
            self.activation_player_id = player_id

        def print_intervention_result(self, result):
            self.intervention_result = result

    class FakeTeam:
        async def trigger_analysis_and_intervention(self, player_id, monitor):
            assert player_id == "player_1"
            assert monitor is system.monitor
            return {
                "player_id": "player_1",
                "session_id": "player_1-abcd1234",
                "worker_count": 3,
                "overall_confidence": 0.82,
                "final_actions": [
                    {"action_type": "grant_reward"},
                    {"action_type": "assign_support"},
                ],
            }

    fake_ui = FakeUI()
    system.ui = fake_ui
    system.team = FakeTeam()

    result = asyncio.run(system.trigger_analysis_and_intervention("player_1"))

    assert result["player_id"] == "player_1"
    assert fake_ui.activation_player_id == "player_1"
    assert fake_ui.intervention_result == result
