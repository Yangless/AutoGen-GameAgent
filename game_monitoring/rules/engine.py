"""
规则引擎核心

包含:
- Rule: 规则基类
- RuleExecutionContext: 执行上下文
- RuleResult: 执行结果
- RuleRegistry: 规则注册中心
- RuleEngine: 主引擎
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable, Set
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class RulePriority(Enum):
    """规则优先级"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    INFO = 5


class RuleCategory(Enum):
    """规则分类"""
    EMOTION = "emotion"
    CHURN_RISK = "churn_risk"
    BOT_DETECTION = "bot_detection"
    SOCIAL = "social"
    ECONOMIC = "economic"
    COMBAT = "combat"
    META = "meta"


@dataclass(frozen=True)
class RuleResult:
    """规则执行结果"""
    rule_id: str
    triggered: bool
    scenario_name: str
    description: str
    category: RuleCategory
    confidence: float = 1.0
    priority: RulePriority = RulePriority.MEDIUM
    triggered_actions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'rule_id': self.rule_id,
            'triggered': self.triggered,
            'scenario_name': self.scenario_name,
            'description': self.description,
            'category': self.category.value,
            'confidence': self.confidence,
            'priority': self.priority.value,
            'triggered_actions': self.triggered_actions,
            'metadata': self.metadata
        }

    @classmethod
    def not_triggered(cls, rule_id: str, scenario_name: str, reason: str = "未触发") -> 'RuleResult':
        return cls(
            rule_id=rule_id,
            triggered=False,
            scenario_name=scenario_name,
            description=reason,
            category=RuleCategory.META
        )


@dataclass
class RuleExecutionContext:
    """规则执行上下文"""
    player_id: str
    actions: List[Dict[str, Any]]
    recent_actions: List[Dict[str, Any]]
    player_state: Optional[Dict] = None
    session_data: Dict[str, Any] = field(default_factory=dict)

    def get_action_names(self, count: int = None) -> List[str]:
        actions = self.recent_actions if count is None else self.recent_actions[-count:]
        return [a.get('action', '') for a in actions]

    def has_action(self, action_name: str) -> bool:
        return any(a.get('action') == action_name for a in self.recent_actions)

    def count_consecutive(self, action_name: str) -> int:
        count = 0
        for action in reversed(self.recent_actions):
            if action.get('action') == action_name:
                count += 1
            else:
                break
        return count


class Rule(ABC):
    """规则基类"""

    @property
    @abstractmethod
    def rule_id(self) -> str:
        pass

    @property
    @abstractmethod
    def scenario_name(self) -> str:
        pass

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.META

    @property
    def priority(self) -> RulePriority:
        return RulePriority.MEDIUM

    @property
    def description(self) -> str:
        return f"检测场景: {self.scenario_name}"

    @abstractmethod
    def evaluate(self, context: RuleExecutionContext) -> RuleResult:
        pass

    def should_skip(self, context: RuleExecutionContext) -> bool:
        return False


class RuleRegistry:
    """规则注册中心"""

    def __init__(self):
        self._rules: Dict[str, Rule] = {}
        self._disabled: Set[str] = set()

    def register(self, rule: Rule) -> 'RuleRegistry':
        self._rules[rule.rule_id] = rule
        return self

    def get(self, rule_id: str) -> Optional[Rule]:
        return self._rules.get(rule_id)

    def get_all(self) -> List[Rule]:
        return list(self._rules.values())

    def get_applicable(self, context: RuleExecutionContext) -> List[Rule]:
        applicable = []
        for rule in self._rules.values():
            if rule.rule_id in self._disabled:
                continue
            if not rule.should_skip(context):
                applicable.append(rule)
        return sorted(applicable, key=lambda r: r.priority.value)

    def execute_all(self, context: RuleExecutionContext) -> List[RuleResult]:
        results = []
        for rule in self.get_applicable(context):
            try:
                result = rule.evaluate(context)
                if result.triggered:
                    results.append(result)
            except Exception as e:
                logger.error(f"规则 {rule.rule_id} 执行失败: {e}")
        return results


class RuleEngine:
    """规则引擎"""

    def __init__(self, registry: RuleRegistry = None, window_size: int = 3):
        self._registry = registry or RuleRegistry()
        self._window_size = window_size

    @property
    def registry(self) -> RuleRegistry:
        return self._registry

    def analyze(
        self,
        player_id: str,
        actions: List[Dict[str, Any]],
        player_state: Dict = None
    ) -> List[RuleResult]:
        recent = actions[-self._window_size:] if len(actions) >= self._window_size else actions

        context = RuleExecutionContext(
            player_id=player_id,
            actions=actions,
            recent_actions=recent,
            player_state=player_state
        )

        return self._registry.execute_all(context)

    def get_emotion_from_results(self, results: List[RuleResult]) -> str:
        """从规则结果判断情绪"""
        for result in results:
            if result.category in (RuleCategory.EMOTION, RuleCategory.CHURN_RISK):
                if any(word in result.scenario_name for word in ['失败', '风险', '退出', '攻击']):
                    return "negative"
        return "neutral"
