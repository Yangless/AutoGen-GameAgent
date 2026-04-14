from game_monitoring.infrastructure.monitoring.output_metrics import OutputMetrics


def test_output_metrics_record_success():
    """测试记录成功验证"""
    metrics = OutputMetrics()

    metrics.record_validation(success=True, retries=0)
    metrics.record_validation(success=True, retries=1)
    metrics.record_validation(success=False, retries=3)

    assert metrics.total_outputs == 3
    assert metrics.validation_errors == 1
    assert metrics.retry_counts == [0, 1, 3]


def test_output_metrics_error_rate():
    """测试错误率计算"""
    metrics = OutputMetrics()

    for _ in range(10):
        metrics.record_validation(success=True, retries=0)

    for _ in range(2):
        metrics.record_validation(success=False, retries=3)

    error_rate = metrics.get_error_rate()

    assert error_rate == 2 / 12
    assert abs(error_rate - 0.1667) < 0.01


def test_output_metrics_avg_retries():
    """测试平均重试次数"""
    metrics = OutputMetrics()

    metrics.record_validation(success=True, retries=0)
    metrics.record_validation(success=True, retries=1)
    metrics.record_validation(success=True, retries=2)

    assert metrics.get_avg_retries() == 1.0
