"""
输出质量监控

记录验证成功率、重试次数等指标。
"""


class OutputMetrics:
    """输出质量监控。"""

    def __init__(self) -> None:
        self.total_outputs = 0
        self.validation_errors = 0
        self.retry_counts: list[int] = []

    def record_validation(self, success: bool, retries: int) -> None:
        """记录一次验证结果。"""
        self.total_outputs += 1
        if not success:
            self.validation_errors += 1
        self.retry_counts.append(retries)

    def get_error_rate(self) -> float:
        """返回验证错误率。"""
        if self.total_outputs == 0:
            return 0.0
        return self.validation_errors / self.total_outputs

    def get_avg_retries(self) -> float:
        """返回平均重试次数。"""
        if not self.retry_counts:
            return 0.0
        return sum(self.retry_counts) / len(self.retry_counts)
