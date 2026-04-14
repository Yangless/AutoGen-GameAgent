import importlib
import sys
import types

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
