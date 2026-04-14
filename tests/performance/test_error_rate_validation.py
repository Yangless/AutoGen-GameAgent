from game_monitoring.infrastructure.monitoring.output_metrics import OutputMetrics


def test_error_rate_validation():
    """测试错误率：目标≤11%"""
    metrics = OutputMetrics()

    for _ in range(450):
        metrics.record_validation(success=True, retries=0)

    for _ in range(50):
        metrics.record_validation(success=False, retries=3)

    error_rate = metrics.get_error_rate()

    print(f"错误率: {error_rate * 100:.2f}%")

    assert error_rate <= 0.11
