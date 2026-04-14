"""
规则定义模块

包含所有具体规则实现
"""

from .emotion_rules import *
from .churn_rules import *
from .combat_rules import *

__all__ = [
    'ConsecutiveFailuresRule',
    'SocialWithdrawalRule',
    'ChurnRiskRule',
    'StaminaExhaustionRule',
]
