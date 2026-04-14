import importlib
from types import SimpleNamespace

from tests.unit.ui.streamlit_test_double import install_streamlit_test_double


def _build_ctx(**session_overrides):
    from game_monitoring.ui.dashboard_render_context import DashboardRenderContext

    session_state = SimpleNamespace(
        agent_logs=[],
        team_analysis_results=[],
        team_analysis_capture=SimpleNamespace(get_all_logs=lambda: []),
        stamina_guidance_results=[],
        stamina_exhaustion_count=0,
        stamina_guide_logs=[],
        batch_generated_orders=None,
        single_generated_order=None,
        batch_generation_in_progress=False,
        batch_generation_total=0,
        batch_generation_processed=0,
        batch_generation_error=None,
        current_player_id="player_1",
    )
    for key, value in session_overrides.items():
        setattr(session_state, key, value)

    return DashboardRenderContext(
        session_state=session_state,
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


def test_render_basic_logs_tab_shows_info_when_logs_missing():
    fake_streamlit = install_streamlit_test_double()
    tab_module = importlib.import_module("game_monitoring.ui.dashboard_tabs")

    tab_module.render_basic_logs_tab(_build_ctx())

    assert fake_streamlit.infos == ["等待系统活动..."]


def test_render_team_analysis_tab_shows_waiting_info_without_results():
    fake_streamlit = install_streamlit_test_double()
    tab_module = importlib.import_module("game_monitoring.ui.dashboard_tabs")

    tab_module.render_team_analysis_tab(_build_ctx())

    assert any("等待Agent团队分析" in value for value in fake_streamlit.infos)


def test_render_orders_tab_shows_no_players_message(monkeypatch):
    fake_streamlit = install_streamlit_test_double()
    tab_module = importlib.import_module("game_monitoring.ui.dashboard_tabs")
    monkeypatch.setattr(tab_module, "get_player_names", lambda runtime: [])

    tab_module.render_orders_tab(_build_ctx(runtime={}))

    assert any("暂无可用玩家" in value for value in fake_streamlit.infos)
