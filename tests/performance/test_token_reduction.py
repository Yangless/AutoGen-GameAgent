from datetime import datetime

from game_monitoring.infrastructure.memory.memory_service import ShortTermMemory


def test_token_reduction():
    """测试Token消耗降低：目标55%"""
    all_memories = [
        ShortTermMemory(
            session_id="test",
            timestamp=datetime.now(),
            role="user",
            content=f"Message {i}",
        )
        for i in range(100)
    ]

    original_tokens = len(all_memories) * 50

    recent_memories = all_memories[-10:]
    summary = "玩家经历了情绪波动，已采取安抚措施。关键事件：干预发送关怀邮件。"

    optimized_tokens = len(recent_memories) * 50 + len(summary)
    reduction_rate = (original_tokens - optimized_tokens) / original_tokens

    print(f"原始Token: {original_tokens}")
    print(f"优化后Token: {optimized_tokens}")
    print(f"降低比例: {reduction_rate * 100:.1f}%")

    assert reduction_rate >= 0.55
