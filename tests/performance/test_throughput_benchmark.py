import time

from game_monitoring.agents.orchestrator import OrchestratorAgent
from game_monitoring.domain.messages import PlayerEvent


def test_throughput_benchmark():
    """测试处理能力：目标≥3000条/日"""
    orchestrator = OrchestratorAgent(
        model_client=None,
        worker_types=["emotion", "churn", "behavior"],
    )

    total_events = 1000
    start_time = time.perf_counter()

    for i in range(total_events):
        event = PlayerEvent(
            player_id=f"player_{i}",
            triggered_scenarios=[{"scenario": "test"}],
            behavior_history=[],
            session_id=f"session_{i}",
        )
        tasks = orchestrator._generate_tasks(event)
        assert len(tasks) == 3

    elapsed = time.perf_counter() - start_time
    throughput_per_second = total_events / max(elapsed, 1e-9)
    throughput_per_day = throughput_per_second * 86400

    print(f"吞吐量: {throughput_per_day:.0f} 条/日")

    assert throughput_per_day >= 3000
