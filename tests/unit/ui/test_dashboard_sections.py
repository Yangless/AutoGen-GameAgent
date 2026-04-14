import importlib
from types import SimpleNamespace

from tests.unit.ui.streamlit_test_double import install_streamlit_test_double


def _build_ctx():
    from game_monitoring.ui.dashboard_render_context import DashboardRenderContext

    return DashboardRenderContext(
        session_state=SimpleNamespace(
            current_player_id="player_1",
            system_initialized=True,
        ),
        runtime={},
        monitor=SimpleNamespace(),
        player_state_manager=SimpleNamespace(),
        run_async=lambda coro: coro,
        add_agent_log=lambda message: None,
        add_behavior_log=lambda player_id, action: None,
        add_stamina_guide_log=lambda message: None,
        store_team_analysis_result=lambda result: None,
        add_script_run_ctx=None,
    )


def test_render_dashboard_sections_dispatches_left_center_right(monkeypatch):
    install_streamlit_test_double()
    section_module = importlib.import_module("game_monitoring.ui.dashboard_sections")
    calls = []

    monkeypatch.setattr(section_module, "render_left_panel", lambda ctx: calls.append("left"))
    monkeypatch.setattr(section_module, "render_center_panel", lambda ctx: calls.append("center"))
    monkeypatch.setattr(section_module, "render_right_panel", lambda ctx: calls.append("right"))

    section_module.render_dashboard_sections(_build_ctx())

    assert calls == ["left", "center", "right"]


def test_render_center_panel_calls_all_tab_renderers(monkeypatch):
    install_streamlit_test_double()
    section_module = importlib.import_module("game_monitoring.ui.dashboard_sections")
    calls = []

    monkeypatch.setattr(section_module, "render_basic_logs_tab", lambda ctx: calls.append("logs"))
    monkeypatch.setattr(section_module, "render_team_analysis_tab", lambda ctx: calls.append("analysis"))
    monkeypatch.setattr(section_module, "render_stamina_tab", lambda ctx: calls.append("stamina"))
    monkeypatch.setattr(section_module, "render_orders_tab", lambda ctx: calls.append("orders"))

    section_module.render_center_panel(_build_ctx())

    assert calls == ["logs", "analysis", "stamina", "orders"]


def test_render_status_bar_uses_current_player_and_system_state():
    fake_streamlit = install_streamlit_test_double()
    section_module = importlib.import_module("game_monitoring.ui.dashboard_sections")

    section_module.render_status_bar(_build_ctx())

    assert any("👤 当前玩家: player_1" == value for value in fake_streamlit.writes)
    assert any("⚙️ 系统状态: 🟢 运行中" == value for value in fake_streamlit.writes)
