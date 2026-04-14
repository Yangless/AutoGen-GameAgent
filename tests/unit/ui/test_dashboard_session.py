from game_monitoring.ui.dashboard_session import (
    TeamAnalysisLogCapture,
    append_dashboard_log,
    ensure_dashboard_state,
)


def test_ensure_dashboard_state_sets_defaults_without_overwriting_existing_values():
    session_state = {"current_player_id": "existing"}

    ensure_dashboard_state(
        session_state,
        action_definitions_factory=lambda: "actions",
        rule_engine_factory=lambda: "rules",
        team_capture_factory=lambda mapping: ("capture", mapping),
    )

    assert session_state["current_player_id"] == "existing"
    assert session_state["action_definitions"] == "actions"
    assert session_state["rule_engine"] == "rules"
    assert session_state["team_analysis_capture"][0] == "capture"
    assert session_state["action_sequence"] == []
    assert session_state["team_analysis_results"] == []
    assert session_state["batch_generation_in_progress"] is False


def test_append_dashboard_log_keeps_only_latest_entries():
    session_state = {"agent_logs": []}

    append_dashboard_log(
        session_state,
        "agent_logs",
        "one",
        limit=2,
        timestamp_factory=lambda: "10:00:00",
    )
    append_dashboard_log(
        session_state,
        "agent_logs",
        "two",
        limit=2,
        timestamp_factory=lambda: "10:00:01",
    )
    append_dashboard_log(
        session_state,
        "agent_logs",
        "three",
        limit=2,
        timestamp_factory=lambda: "10:00:02",
    )

    assert session_state["agent_logs"] == [
        "[10:00:01] two",
        "[10:00:02] three",
    ]


def test_team_analysis_log_capture_syncs_session_state_only_while_capturing():
    session_state = {"team_analysis_logs": []}
    timestamps = iter(["10:00:00.000", "10:00:01.000"])
    capture = TeamAnalysisLogCapture(
        session_state,
        timestamp_factory=lambda: next(timestamps),
    )

    capture.write("ignored")
    capture.start_capture()
    capture.write("hello")
    capture.stop_capture()
    capture.write("ignored again")

    assert capture.get_all_logs() == ["[10:00:00.000] hello"]
    assert session_state["team_analysis_logs"] == ["[10:00:00.000] hello"]
