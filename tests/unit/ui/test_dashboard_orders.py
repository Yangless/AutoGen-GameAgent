import json
from datetime import datetime

from game_monitoring.domain.repositories.player_repository import PlayerEntity
from game_monitoring.ui.dashboard_orders import run_batch_generation


def test_run_batch_generation_tracks_progress_and_success_results():
    runtime = {
        "player_repository": type(
            "Repo",
            (),
            {
                "get_by_name": staticmethod(
                    lambda name: PlayerEntity(
                        player_name=name,
                        player_id=f"{name}_id",
                        team_stamina=[10, 20, 30, 40],
                        backpack_items=["bread"],
                        team_levels=[10, 20, 30, 40],
                        skill_levels=[1, 2, 3, 4],
                        reserve_troops=123,
                    )
                )
            },
        )()
    }
    session_state = {
        "batch_generated_orders": [],
        "batch_generation_processed": 0,
        "batch_generation_in_progress": True,
        "batch_generation_error": None,
    }

    def generate_order(**kwargs):
        return json.dumps(
            {
                "player_name": kwargs["player_name"],
                "player_id": kwargs["player_id"],
                "military_order": "attack",
                "team_analysis": [{"team_number": 1}],
            },
            ensure_ascii=False,
        )

    run_batch_generation(
        session_state,
        runtime,
        ["玩家A"],
        "总军令",
        generate_order,
        now_factory=lambda: datetime(2026, 4, 14, 16, 30, 0),
    )

    assert session_state["batch_generation_processed"] == 1
    assert session_state["batch_generation_in_progress"] is False
    assert session_state["batch_generated_orders"][0]["player_name"] == "玩家A"
    assert session_state["batch_generated_orders"][0]["military_order"] == "attack"
    assert session_state["batch_generated_orders"][0]["teams_info"] == [{"team_number": 1}]


def test_run_batch_generation_records_missing_player_and_generator_errors():
    class Repo:
        @staticmethod
        def get_by_name(name):
            if name == "缺失玩家":
                return None
            return PlayerEntity(player_name=name, player_id=f"{name}_id")

    runtime = {"player_repository": Repo()}
    session_state = {
        "batch_generated_orders": [],
        "batch_generation_processed": 0,
        "batch_generation_in_progress": True,
        "batch_generation_error": None,
    }

    def failing_generator(**kwargs):
        raise RuntimeError("generator failed")

    run_batch_generation(
        session_state,
        runtime,
        ["缺失玩家", "失败玩家"],
        "总军令",
        failing_generator,
        now_factory=lambda: datetime(2026, 4, 14, 16, 31, 0),
    )

    assert session_state["batch_generation_processed"] == 2
    assert session_state["batch_generation_in_progress"] is False
    assert len(session_state["batch_generated_orders"]) == 2
    assert "未找到玩家信息" in session_state["batch_generated_orders"][0]["error"]
    assert session_state["batch_generated_orders"][1]["error"] == "generator failed"
    assert session_state["batch_generation_error"] == "generator failed"
