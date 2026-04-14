"""
规则引擎模块

设计目标:
1. 规则独立定义，可动态注册/注销
2. 支持规则优先级和互斥
3. 可扩展的Hook机制
4. 规则组合逻辑支持

使用示例:
```python
from rules import RuleEngine, Rule, RuleResult

engine = RuleEngine()
result = engine.analyze("player_1", actions)
```
"""

from .engine import (
    Rule,
    RuleEngine,
    RuleExecutionContext,
    RuleResult,
    RuleCategory,
    RulePriority,
    RuleRegistry
)

__all__ = [
    'Rule',
    'RuleEngine',
    'RuleExecutionContext',
    'RuleResult',
    'RuleCategory',
    'RulePriority',
    'RuleRegistry'
]
