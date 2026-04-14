# 迭代2: 规则引擎插件化

## 概述
本迭代重构行为监控规则引擎，实现规则的定义-注册-执行的分离架构。

---

## 第1天: 规则引擎核心架构

### 目标目录结构

```
game_monitoring/
├── rules/
│   ├── __init__.py
│   ├── engine.py              # 规则引擎核心
│   ├── registry.py            # 规则注册中心
│   ├── context.py             # 规则执行上下文
│   ├── base.py                # 规则基类
│   ├── loader.py              # 规则自动发现
│   ├── definitions/           # 具体规则定义
│   │   ├── __init__.py
│   │   ├── emotion_rules.py   # 情绪相关
│   │   ├── churn_rules.py     # 流失风险
│   │   ├── bot_rules.py       # 机器人检测
│   │   ├── social_rules.py    # 社交行为
│   │   ├── economic_rules.py  # 经济行为
│   │   └── stamina_rules.py   # 体力规则
│   └── compositions/          # 规则组合逻辑
│       └── __init__.py
└── ...
```

### 规则引擎核心

**文件**: `rules/engine.py`

```python
"""
规则引擎核心

设计目标:
1. 规则独立定义，可动态注册/注销
2. 支持规则优先级和互斥
3. 可扩展的Hook机制
4. 规则组合逻辑支持
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
    CRITICAL = 1      # 关键规则，如体力耗尽
    HIGH = 2          # 高优先级，如流失风险
    MEDIUM = 3        # 中等优先级
    LOW = 4           # 低优先级，如社交活跃
    INFO = 5          # 信息性规则


class RuleCategory(Enum):
    """规则分类"""
    EMOTION = auto()      # 情绪相关
    CHURN_RISK = auto()   # 流失风险
    BOT_DETECTION = auto() # 机器人检测   
    SOCIAL = auto()       # 社交行为
    ECONOMIC = auto()     # 经济行为
    COMBAT = auto()       # 战斗行为
    META = auto()         # 元数据


@dataclass(frozen=True)
class RuleResult:
    """规则执行结果 - 不可变数据类"""
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
        """转换为字典"""
        return {
            'rule_id': self.rule_id,
            'triggered': self.triggered,
            'scenario_name': self.scenario_name,
            'description': self.description,
            'category': self.category.name,
            'confidence': self.confidence,
            'priority': self.priority.value,
            'triggered_actions': self.triggered_actions,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }
    
    @classmethod
    def not_triggered(
        cls,
        rule_id: str,
        scenario_name: str,
        reason: str = "未触发"
    ) -> 'RuleResult':
        """创建未触发的结果"""
        return cls(
            rule_id=rule_id,
            triggered=False,
            scenario_name=scenario_name,
            description=reason,
            category=RuleCategory.META,
            priority=RulePriority.INFO
        )


@dataclass
class RuleExecutionContext:
    """规则执行上下文"""
    player_id: str
    actions: List[Dict[str, Any]]  # 完整动作历史
    recent_actions: List[Dict[str, Any]]  # 最近窗口（默认3个）
    player_state: Optional[Dict] = None     # 当前玩家状态
    session_data: Dict[str, Any] = field(default_factory=dict)  # 会话数据
    
    def get_action_names(self, count: int = None) -> List[str]:
        """获取动作名称列表"""
        actions = self.recent_actions if count is None else self.recent_actions[-count:]
        return [a.get('action', '') for a in actions]
    
    def has_action(self, action_name: str) -> bool:
        """检查是否包含某动作"""
        return any(a.get('action') == action_name for a in self.recent_actions)
    
    def count_consecutive(self, action_name: str) -> int:
        """从最新开始计算连续某动作次数"""
        count = 0
        for action in reversed(self.recent_actions):
            if action.get('action') == action_name:
                count += 1
            else:
                break
        return count


class Rule(ABC):
    """
    规则基类
    
    使用示例:
    ```python
    class MyRule(Rule):
        @property
        def rule_id(self) -> str:
            return "my_rule"
        
        @property
        def scenario_name(self) -> str:
            return "我的场景"
        
        @property
        def category(self) -> RuleCategory:
            return RuleCategory.EMOTION
        
        def evaluate(self, context: RuleExecutionContext) -> RuleResult:
            # 规则逻辑
            if context.has_action("click_exit"):
                return RuleResult(...)
            return RuleResult.not_triggered(...)
    ```
    """
    
    @property
    @abstractmethod
    def rule_id(self) -> str:
        """规则唯一标识"""
        pass
    
    @property
    @abstractmethod
    def scenario_name(self) -> str:
        """场景名称"""
        pass
    
    @property
    def category(self) -> RuleCategory:
        """规则分类（默认META）"""
        return RuleCategory.META
    
    @property
    def priority(self) -> RulePriority:
        """优先级（默认MEDIUM）"""
        return RulePriority.MEDIUM
    
    @property
    def description(self) -> str:
        """规则描述"""
        return f"检测场景: {self.scenario_name}"
    
    @property
    def tags(self) -> Set[str]:
        """规则标签，用于分组和过滤"""
        return set()
    
    @abstractmethod
    def evaluate(self, context: RuleExecutionContext) -> RuleResult:
        """
        评估规则
        
        Args:
            context: 执行上下文
            
        Returns:
            规则执行结果
        """
        pass
    
    def should_skip(self, context: RuleExecutionContext) -> bool:
        """
        前置跳过检查
        
        返回True则跳过该规则
        """
        return False
    
    def get_dependencies(self) -> List[str]:
        """
        获取依赖的其他规则ID
        
        返回的规则会先执行，如果依赖规则未触发，当前规则可能跳过
        """
        return []
    
    def __repr__(self):
        return f"<{self.__class__.__name__}({self.rule_id})>"


class RulePrecondition:
    """
    规则前置条件
    
    用于构建可复用的前置检查器
    """
    
    @staticmethod
    def minimum_actions(count: int) -> Callable:
        """至少N个动作的预条件"""
        def check(context: RuleExecutionContext) -> bool:
            return len(context.recent_actions) >= count
        return check
    
    @staticmethod
    def requires_action(action_name: str) -> Callable:
        """需要特定动作"""
        def check(context: RuleExecutionContext) -> bool:
            return context.has_action(action_name)
        return check
    
    @staticmethod
    def within_timerange(seconds: int) -> Callable:
        """动作在指定时间范围内"""
        def check(context: RuleExecutionContext) -> bool:
            if not context.recent_actions:
                return False
            first_time = context.recent_actions[0].get('timestamp')
            last_time = context.recent_actions[-1].get('timestamp')
            if first_time and last_time:
                return (last_time - first_time).total_seconds() <= seconds
            return False
        return check


class RuleRegistry:
    """
    规则注册中心
    
    管理所有规则的注册、查询和执行
    """
    
    def __init__(self):
        self._rules: Dict[str, Rule] = {}
        self._by_category: Dict[RuleCategory, Set[str]] = {c: set() for c in RuleCategory}
        self._by_tag: Dict[str, Set[str]] = {}
        self._hooks: Dict[str, List[Callable]] = {
            'before_evaluate': [],
            'after_evaluate': [],
            'on_trigger': [],
        }
        self._disabled: Set[str] = set()
    
    # ============ 注册管理 ============
    
    def register(self, rule: Rule) -> 'RuleRegistry':
        """注册规则"""
        self._rules[rule.rule_id] = rule
        self._by_category[rule.category].add(rule.rule_id)
        
        for tag in rule.tags:
            if tag not in self._by_tag:
                self._by_tag[tag] = set()
            self._by_tag[tag].add(rule.rule_id)
        
        logger.debug(f"规则已注册: {rule.rule_id}")
        return self
    
    def unregister(self, rule_id: str) -> None:
        """注销规则"""
        if rule_id in self._rules:
            rule = self._rules[rule_id]
            self._by_category[rule.category].discard(rule_id)
            
            for tag in rule.tags:
                self._by_tag[tag].discard(rule_id)
            
            del self._rules[rule_id]
            self._disabled.discard(rule_id)
    
    def disable(self, rule_id: str) -> None:
        """禁用规则"""
        self._disabled.add(rule_id)
    
    def enable(self, rule_id: str) -> None:
        """启用规则"""
        self._disabled.discard(rule_id)
    
    # ============ 查询功能 ============
    
    def get(self, rule_id: str) -> Optional[Rule]:
        """获取规则"""
        return self._rules.get(rule_id)
    
    def get_all(self) -> List[Rule]:
        """获取所有规则"""
        return list(self._rules.values())
    
    def get_by_category(self, category: RuleCategory) -> List[Rule]:
        """按分类获取"""
        return [self._rules[rid] for rid in self._by_category[category] 
                if rid not in self._disabled]
    
    def get_by_tag(self, tag: str) -> List[Rule]:
        """按标签获取"""
        return [self._rules[rid] for rid in self._by_tag.get(tag, [])
                if rid not in self._disabled]
    
    def get_applicable(self, context: RuleExecutionContext) -> List[Rule]:
        """
        获取适用的规则列表
        
        考虑:
        - 禁用状态
        - should_skip
        - 前置条件
        """
        applicable = []
        for rule in self._rules.values():
            if rule.rule_id in self._disabled:
                continue
            if rule.should_skip(context):
                continue
            applicable.append(rule)
        
        # 按优先级排序
        return sorted(applicable, key=lambda r: r.priority.value)
    
    # ============ 执行功能 ============
    
    def execute_single(self, rule_id: str, context: RuleExecutionContext) -> Optional[RuleResult]:
        """执行单个规则"""
        rule = self._rules.get(rule_id)
        if not rule or rule_id in self._disabled:
            return None
            
        try:
            return rule.evaluate(context)
        except Exception as e:
            logger.error(f"规则 {rule_id} 执行失败: {e}")
            return RuleResult(
                rule_id=rule_id,
                triggered=False,
                scenario_name=rule.scenario_name,
                description=f"执行错误: {str(e)}",
                category=RuleCategory.META,
                priority=RulePriority.LOW
            )
    
    def execute_all(self, context: RuleExecutionContext, 
                    categories: List[RuleCategory] = None) -> List[RuleResult]:
        """
        执行所有适用规则
        
        Args:
            context: 执行上下文
            categories: 可选分类过滤
            
        Returns:
            触发的规则结果列表
        """
        results = []
        
        if categories:
            rules = []
            for cat in categories:
                rules.extend(self.get_by_category(cat))
        else:
            rules = self.get_applicable(context)
        
        # 执行前置hook
        for hook in self._hooks['before_evaluate']:
            try:
                hook(context, rules)
            except Exception as e:
                logger.warning(f"前置hook错误: {e}")
        
        for rule in rules:
            result = self.execute_single(rule.rule_id, context)
            if result and result.triggered:
                results.append(result)
                
                # 执行触发hook
                for hook in self._hooks['on_trigger']:
                    try:
                        hook(context, result)
                    except Exception as e:
                        logger.warning(f"触发hook错误: {e}")
        
        # 执行后置hook
        for hook in self._hooks['after_evaluate']:
            try:
                hook(context, results)
            except Exception as e:
                logger.warning(f"后置hook错误: {e}")
        
        return results
    
    # ============ Hook管理 ============
    
    def add_hook(self, event: str, callback: Callable) -> None:
        """添加Hook"""
        if event in self._hooks:
            self._hooks[event].append(callback)
    
    def remove_hook(self, event: str, callback: Callable) -> None:
        """移除Hook"""
        if event in self._hooks:
            self._hooks[event] = [cb for cb in self._hooks[event] if cb != callback]
    
    # ============ 工具方法 ============
    
    def get_summary(self) -> Dict[str, Any]:
        """获取注册摘要"""
        return {
            'total': len(self._rules),
            'active': len(self._rules) - len(self._disabled),
            'disabled': len(self._disabled),
            'by_category': {
                cat.name: len(self._by_category[cat])
                for cat in RuleCategory
            }
        }
    
    def __repr__(self):
        return f"<RuleRegistry rules={len(self._rules)}>"


class RuleEngine:
    """
    规则引擎
    
    对外统一接口，封装Registry和上下文准备
    """
    
    def __init__(self, registry: RuleRegistry = None):
        self._registry = registry or RuleRegistry()
        self._window_size = 3
    
    @property
    def registry(self) -> RuleRegistry:
        """获取注册中心"""
        return self._registry
    
    def set_window_size(self, size: int) -> 'RuleEngine':
        """设置分析窗口大小"""
        self._window_size = size
        return self
    
    def analyze(
        self,
        player_id: str,
        actions: List[Dict[str, Any]],
        player_state: Dict = None,
        categories: List[RuleCategory] = None
    ) -> List[RuleResult]:
        """
        分析玩家动作序列
        
        Args:
            player_id: 玩家ID
            actions: 完整动作序列
            player_state: 可选的玩家状态
            categories: 可选的分类过滤
            
        Returns:
            触发的规则列表
        """
        # 准备最近窗口
        recent = actions[-self._window_size:] if len(actions) >= self._window_size else actions
        
        context = RuleExecutionContext(
            player_id=player_id,
            actions=actions,
            recent_actions=recent,
            player_state=player_state
        )
        
        return self._registry.execute_all(context, categories)
    
    def get_emotion_from_results(self, results: List[RuleResult]) -> str:
        """
        根据规则结果判断情绪类型
        
        情绪优先级: negative > abnormal > positive > neutral
        """
        priority_map = {
            RuleCategory.EMOTION: 2,  # EMOTION类别中通常是negative
            RuleCategory.CHURN_RISK: 2,
            RuleCategory.BOT_DETECTION: 1,
            RuleCategory.SOCIAL: 0,
            RuleCategory.ECONOMIC: 0,
        }
        
        max_priority = -1
        emotion = "neutral"
        
        for result in results:
            if not result.triggered:
                continue
            
            # 根据category和scenario_name推断情绪
            category = result.category
            
            if category in (RuleCategory.EMOTION, RuleCategory.CHURN_RISK):
                if any(word in result.scenario_name for word in ["失败", "风险", "退出", "消极"]):
                    if priority_map.get(category, 0) > max_priority:
                        max_priority = priority_map[category]
                        emotion = "negative"
                elif any(word in result.scenario_name for word in ["充值", "成就", "活跃"]):
                    emotion = "positive"
                    
            elif category == RuleCategory.BOT_DETECTION:
                emotion = "abnormal"
        
        return emotion
    
    def quick_check(
        self,
        player_id: str,
        action_name: str,
        **action_params
    ) -> List[RuleResult]:
        """
        快速检查单个动作
        
        用于轻量级场景检测
        """
        action = {
            'action': action_name,
            'params': action_params,
            'timestamp': datetime.now(),
            'player_id': player_id
        }
        
        # 使用预定义的简单规则列表
        context = RuleExecutionContext(
            player_id=player_id,
            actions=[action],
            recent_actions=[action]
        )
        
        return self._registry.execute_all(context)
    
    def __enter__(self):
        """上下文管理器支持"""
        return self
    
    def __exit__(self, *args):
        pass
```

---

## 第2天: 具体规则实现

### 情绪规则定义

**文件**: `rules/definitions/emotion_rules.py`

```python
"""
情绪相关规则
"""

from ..engine import Rule, RuleResult, RuleExecutionContext, RuleCategory, RulePriority


class ConsecutiveFailuresRule(Rule):
    """
    连续失败触发消极情绪
    
    检测副本失败、PVP失败、抽卡失败等连续负面事件
    """
    
    FAILURE_ACTIONS = {
        'complete_dungeon': {'status': 'fail'},
        'upgrade_skill': {'status': 'fail'},
        'upgrade_building': {'status': 'fail'},
        'recruit_hero': {'rarity': 'common'},
        'lose_pvp': {}
    }
    
    THRESHOLD = 2  # 至少2次失败触发
    
    @property
    def rule_id(self) -> str:
        return "consecutive_failures"
    
    @property
    def scenario_name(self) -> str:
        return "连续失败触发消极情绪"
    
    @property
    def category(self) -> RuleCategory:
        return RuleCategory.EMOTION
    
    @property
    def priority(self) -> RulePriority:
        return RulePriority.HIGH
    
    @property
    def tags(self) -> set:
        return {'emotion', 'negative', 'failure'}
    
    def evaluate(self, context: RuleExecutionContext) -> RuleResult:
        failures = []
        consecutive_count = 0
        
        # 从最新开始反向检查连续失败
        for action in reversed(context.recent_actions):
            action_name = action.get('action', '')
            params = action.get('params', {})
            
            if self._is_failure_action(action_name, params):
                consecutive_count += 1
                failures.insert(0, action_name)
            elif action_name:  # 其他动作打断失败链
                break
        
        triggered = consecutive_count >= self.THRESHOLD
        
        return RuleResult(
            rule_id=self.rule_id,
            triggered=triggered,
            scenario_name=self.scenario_name,
            description=f"连续失败{consecutive_count}次: {', '.join(failures)}" if triggered else "未检测到连续失败",
            category=self.category,
            confidence=min(consecutive_count / 3.0, 1.0),
            priority=self.priority,
            triggered_actions=failures,
            metadata={'failure_count': consecutive_count}
        )
    
    def _is_failure_action(self, action_name: str, params: dict) -> bool:
        """判断是否失败"""
        if action_name not in self.FAILURE_ACTIONS:
            return False
        
        expected = self.FAILURE_ACTIONS[action_name]
        
        # PVP失败直接判断
        if action_name == 'lose_pvp':
            return True
        
        # 抽卡抽到白卡
        if action_name == 'recruit_hero':
            return params.get('rarity') == 'common'
        
        # 其他动作检查状态
        if 'status' in expected:
            return params.get('status') == expected['status']
        
        return False


class SocialWithdrawalRule(Rule):
    """社交退出行为风险"""
    
    WITHDRAWAL_ACTIONS = {'leave_family', 'remove_friend', 'clear_backpack'}
    THRESHOLD = 2
    
    @property
    def rule_id(self) -> str:
        return "social_withdrawal"
    
    @property
    def scenario_name(self) -> str:
        return "社交退出行为风险"
    
    @property
    def category(self) -> RuleCategory:
        return RuleCategory.EMOTION
    
    @property
    def priority(self) -> RulePriority:
        return RulePriority.HIGH
    
    @property
    def tags(self) -> set:
        return {'emotion', 'negative', 'social'}
    
    def evaluate(self, context: RuleExecutionContext) -> RuleResult:
        triggered_set = set()
        
        for action in context.recent_actions:
            action_name = action.get('action', '')
            if action_name in self.WITHDRAWAL_ACTIONS:
                triggered_set.add(action_name)
        
        # 需要至少两种不同的退出行为
        unique_actions = len(triggered_set)
        triggered = unique_actions >= self.THRESHOLD
        
        return RuleResult(
            rule_id=self.rule_id,
            triggered=triggered,
            scenario_name=self.scenario_name,
            description=f"社交退出行为: {', '.join(triggered_set)}" if triggered else "未检测到社交风险",
            category=self.category,
            confidence=min(unique_actions / 3.0, 1.0),
            priority=self.priority,
            triggered_actions=list(triggered_set),
            metadata={'unique_count': unique_actions}
        )


class ConsecutiveAttacksRule(Rule):
    """连续被攻击消极行为"""
    
    THRESHOLD = 3
    
    @property
    def rule_id(self) -> str:
        return "consecutive_attacks"
    
    @property
    def scenario_name(self) -> str:
        return "连续被攻击消极行为"
    
    @property
    def category(self) -> RuleCategory:
        return RuleCategory.EMOTION
    
    @property
    def priority(self) -> RulePriority:
        return RulePriority.HIGH
    
    def evaluate(self, context: RuleExecutionContext) -> RuleResult:
        consecutive = context.count_consecutive('be_attacked')
        triggered = consecutive >= self.THRESHOLD
        
        return RuleResult(
            rule_id=self.rule_id,
            triggered=triggered,
            scenario_name=self.scenario_name,
            description=f"连续被攻击{consecutive}次" if triggered else "未连续被攻击",
            category=self.category,
            confidence=min(consecutive / 3.0, 1.0),
            priority=self.priority,
            metadata={'attack_count': consecutive}
        )


class PaymentPositiveRule(Rule):
    """充值行为积极表现"""
    
    PAYMENT_ACTIONS = {'make_payment', 'buy_monthly_card', 'navigate_to_payment_page'}
    
    @property
    def rule_id(self) -> str:
        return "payment_positive"
    
    @property
    def scenario_name(self) -> str:
        return "充值行为积极表现"
    
    @property
    def category(self) -> RuleCategory:
        return RuleCategory.ECONOMIC
    
    @property
    def priority(self) -> RulePriority:
        return RulePriority.LOW
    
    @property
    def tags(self) -> set:
        return {'positive', 'payment'}
    
    def evaluate(self, context: RuleExecutionContext) -> RuleResult:
        actions_found = []
        
        for action in context.recent_actions:
            action_name = action.get('action', '')
            if action_name in self.PAYMENT_ACTIONS:
                actions_found.append(action_name)
        
        triggered = len(actions_found) > 0
        
        return RuleResult(
            rule_id=self.rule_id,
            triggered=triggered,
            scenario_name=self.scenario_name,
            description=f"充值行为: {', '.join(actions_found)}" if triggered else "无支付行为",
            category=self.category,
            confidence=0.7 if triggered else 0.0,
            priority=self.priority
        )
```

### 体力规则

**文件**: `rules/definitions/stamina_rules.py`

```python
"""
体力相关规则
"""

from ..engine import Rule, RuleResult, RuleExecutionContext, RuleCategory, RulePriority


class StaminaExhaustionRule(Rule):
    """
    体力耗尽引导触发
    
    检测玩家多次体力耗尽，触发恢复引导
    """
    
    STAMINA_KEYWORDS = ['stamina_exhausted', 'attempt_enter_dungeon_no_stamina']
    DEFAULT_THRESHOLD = 3
    
    @property
    def rule_id(self) -> str:
        return "stamina_exhaustion"
    
    @property
    def scenario_name(self) -> str:
        return "体力耗尽引导触发"
    
    @property
    def category(self) -> RuleCategory:
        return RuleCategory.COMBAT
    
    @property
    def priority(self) -> RulePriority:
        return RulePriority.CRITICAL
    
    @property
    def tags(self) -> set:
        return {'stamina', 'critical', 'guidance'}
    
    def evaluate(self, context: RuleExecutionContext) -> RuleResult:
        # 从完整历史统计
        threshold = context.session_data.get('stamina_threshold', self.DEFAULT_THRESHOLD)
        
        stamina_count = sum(
            1 for action in context.actions
            if any(kw in action.get('action', '').lower() for kw in self.STAMINA_KEYWORDS)
        )
        
        triggered = stamina_count >= threshold
        
        return RuleResult(
            rule_id=self.rule_id,
            triggered=triggered,
            scenario_name=self.scenario_name,
            description=f"体力耗尽{stamina_count}次，已达引导阈值" if triggered else "未达体力耗尽阈值",
            category=self.category,
            confidence=min(stamina_count / threshold, 1.0),
            priority=self.priority,
            triggered_actions=[a.get('action') for a in context.actions 
                              if any(kw in a.get('action', '').lower() for kw in self.STAMINA_KEYWORDS)][-5:],
            metadata={
                'stamina_count': stamina_count,
                'threshold': threshold
            }
        )


class LowStaminaPreRule(Rule):
    """低体力预警（使用最近动作窗口）"""
    
    LOW_ACTIONS = {'stamina_exhausted', 'attempt_enter_dungeon_no_stamina'}
    
    @property
    def rule_id(self) -> str:
        return "low_stamina_warning"
    
    @property
    def scenario_name(self) -> str:
        return "低体力行为预警"
    
    @property
    def category(self) -> RuleCategory:
        return RuleCategory.COMBAT
    
    @property
    def priority(self) -> RulePriority:
        return RulePriority.MEDIUM
    
    def evaluate(self, context: RuleExecutionContext) -> RuleResult:
        low_actions = [
            a.get('action') for a in context.recent_actions
            if a.get('action') in self.LOW_ACTIONS
        ]
        
        triggered = len(low_actions) > 0
        
        return RuleResult(
            rule_id=self.rule_id,
            triggered=triggered,
            scenario_name=self.scenario_name,
            description=f"低体力行为次数: {len(low_actions)}" if triggered else "无低体力行为",
            category=self.category,
            confidence=0.5 if triggered else 0.0
        )
```

---

## 第3天: 规则自动加载

### 自动规则发现

**文件**: `rules/loader.py`

```python
"""
规则自动加载模块

支持动态发现和注册规则
"""

import importlib
import pkgutil
import inspect
from pathlib import Path
from typing import List, Type
import logging

from .engine import Rule, RuleRegistry

logger = logging.getLogger(__name__)


class RuleLoader:
    """规则加载器"""
    
    def __init__(self, registry: RuleRegistry = None):
        self._registry = registry or RuleRegistry()
    
    def discover_rules(
        self,
        package_name: str = "game_monitoring.rules.definitions",
        package_path: str = None
    ) -> List[Rule]:
        """
        从包中自动发现所有规则类
        
        Args:
            package_name: 要扫描的包名
            package_path: 包路径（可选，用于从不同位置加载）
            
        Returns:
            发现并实例化的规则列表
        """
        discovered_instances = []
        
        try:
            package = importlib.import_module(package_name)
        except ImportError as e:
            logger.error(f"无法导入包 {package_name}: {e}")
            return []
        
        # 确定扫描路径
        if package_path:
            search_path = [package_path]
        else:
            search_path = [str(Path(package.__file__).parent)]
        
        for _, module_name, _ in pkgutil.iter_modules(search_path):
            full_module_name = f"{package_name}.{module_name}"
            
            try:
                module = importlib.import_module(full_module_name)
                instances = self._extract_rules_from_module(module)
                discovered_instances.extend(instances)
                
            except Exception as e:
                logger.warning(f"加载模块 {full_module_name} 失败: {e}")
        
        logger.info(f"从 {package_name} 发现了 {len(discovered_instances)} 个规则")
        return discovered_instances
    
    def _extract_rules_from_module(self, module) -> List[Rule]:
        """从模块中提取规则类"""
        instances = []
        
        for name in dir(module):
            obj = getattr(module, name)
            
            # 检查是否是Rule的子类
            if (isinstance(obj, type) and 
                issubclass(obj, Rule) and 
                obj is not Rule and
                not inspect.isabstract(obj)):
                
                try:
                    instance = obj()
                    instances.append(instance)
                    logger.debug(f"发现规则: {instance.rule_id}")
                except Exception as e:
                    logger.error(f"实例化 {name} 失败: {e}")
        
        return instances
    
    def load_from_yaml(self, yaml_path: str) -> List[Rule]:
        """
        从YAML配置加载规则（预留扩展）
        
        TODO: 实现基于配置文件的规则加载
        """
        raise NotImplementedError("YAML加载尚未实现")
    
    def auto_register(
        self,
        registry: RuleRegistry = None,
        package_name: str = "game_monitoring.rules.definitions"
    ) -> RuleRegistry:
        """
        自动发现并注册到新注册中心
        
        Args:
            registry: 目标注册中心（None则创建新）
            package_name: 扫描包名
            
        Returns:
            注册好的规则注册中心
        """
        target = registry or self._registry
        rules = self.discover_rules(package_name)
        
        for rule in rules:
            if not target.get(rule.rule_id):
                target.register(rule)
            else:
                logger.warning(f"规则 {rule.rule_id} 已存在，跳过")
        
        return target


# 便捷函数
def load_default_rules(registry: RuleRegistry = None) -> RuleRegistry:
    """加载默认规则集"""
    loader = RuleLoader(registry)
    return loader.auto_register(registry)


def create_engine_with_defaults() -> 'RuleEngine':
    """创建预加载规则的Engine"""
    from .engine import RuleEngine, RuleRegistry
    
    registry = RuleRegistry()
    load_default_rules(registry)
    
    return RuleEngine(registry)
```

### __init__ 更新

**文件**: `rules/__init__.py`

```python
"""
规则引擎模块

导出核心类和便捷函数
"""

from .engine import (
    Rule,
    RuleEngine,
    RuleRegistry,
    RuleResult,
    RuleExecutionContext,
    RuleCategory,
    RulePriority,
    RulePrecondition
)

from .loader import RuleLoader, load_default_rules, create_engine_with_defaults

# 便捷导出
__all__ = [
    'Rule',
    'RuleEngine',
    'RuleRegistry',
    'RuleResult',
    'RuleExecutionContext',
    'RuleCategory',
    'RulePriority',
    'RulePrecondition',
    'RuleLoader',
    'load_default_rules',
    'create_engine_with_defaults'
]


def create_default_rules() -> RuleRegistry:
    """
    创建并填充默认规则的注册中心
    
    使用示例:
    ```python
    from game_monitoring.rules import create_default_rules
    
    registry = create_default_rules()
    print(f"已加载 {len(registry.get_all())} 个规则")
    ```
    """
    return load_default_rules()
```

---

## 第4天: BehaviorMonitor迁移

### 新的 BehaviorMonitor

**文件**: `monitoring/behavior_monitor_v2.py` (重写的版本)

```python
"""
行为监控器 V2 - 集成规则引擎
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from ..rules import RuleEngine, RuleRegistry, RuleCategory
from ..domain.repositories.player_repository import PlayerRepository
from ..monitoring.player_state import PlayerStateManager


class BehaviorMonitorV2:
    """
    行为监控器（插件化规则引擎版）
    
    新特性:
    - 基于规则的动态场景检测
    - 支持规则分类过滤
    - 更好的情绪判断
    - 更丰富的元数据
    """
    
    def __init__(
        self,
        engine: RuleEngine = None,
        threshold: int = 3,
        max_sequence_length: int = 50,
        recent_actions_window: int = 3
    ):
        self._engine = engine or RuleEngine()
        self._threshold = threshold
        self._max_sequence_length = max_sequence_length
        self._recent_window = recent_actions_window
        
        # 数据存储
        self._player_sequences: Dict[str, List[Dict]] = {}
        self._behavior_history: List[Any] = []  # PlayerBehavior对象
        
        # 负面行为计数
        self._negative_counts: Dict[str, int] = {}
    
    @property
    def threshold(self) -> int:
        return self._threshold
    
    @property
    def engine(self) -> RuleEngine:
        return self._engine
    
    def add_atomic_action(
        self,
        player_id: str,
        action_name: str,
        params: Dict[str, Any] = None
    ) -> List[Dict]:
        """
        添加原子动作并分析
        
        Args:
            player_id: 玩家ID
            action_name: 动作名称
            params: 可选参数
            
        Returns:
            触发的规则结果列表
        """
        # 初始化玩家序列
        if player_id not in self._player_sequences:
            self._player_sequences[player_id] = []
        
        # 创建动作数据
        action_data = {
            'action': action_name,
            'params': params or {},
            'timestamp': datetime.now(),
            'player_id': player_id
        }
        
        # 添加到序列
        self._player_sequences[player_id].append(action_data)
        
        # 限制序列长度
        if len(self._player_sequences[player_id]) > self._max_sequence_length:
            self._player_sequences[player_id] = self._player_sequences[player_id][-self._max_sequence_length:]
        
        # 获取分析窗口
        actions = self._player_sequences[player_id]
        recent = actions[-self._recent_window:] if len(actions) >= self._recent_window else actions
        
        # 执行规则分析
        results = self._engine.analyze(player_id, actions, categories=[
            RuleCategory.EMOTION,
            RuleCategory.CHURN_RISK,
            RuleCategory.BOT_DETECTION,
            RuleCategory.COMBAT
        ])
        
        # 返回触发的规则（转换为字典）
        return [r.to_dict() for r in results if r.triggered]
    
    def should_trigger_intervention(
        self,
        player_id: str,
        triggered_rules: List[Dict]
    ) -> bool:
        """
        判断是否应该触发干预
        
        基于:
        1. 消极规则触发计数
        2. CRITICAL优先级规则立即触发
        """
        # 检查CRITICAL规则
        has_critical = any(
            r.get('priority') == 1 for r in triggered_rules
        )
        if has_critical:
            return True
        
        # 检查消极情绪计数
        emotion_type = self._engine.get_emotion_from_results([
            type('obj', (), r) for r in triggered_rules
        ])
        
        if emotion_type == "negative":
            current = self._negative_counts.get(player_id, 0) + 1
            self._negative_counts[player_id] = current
            return current >= self._threshold
        
        return False
    
    def reset_negative_count(self, player_id: str) -> None:
        """重置负面计数"""
        self._negative_counts[player_id] = 0
    
    def get_negative_count(self, player_id: str) -> int:
        """获取当前负面计数"""
        return self._negative_counts.get(player_id, 0)
    
    def get_player_action_sequence(self, player_id: str) -> List[Dict]:
        """获取玩家动作序列"""
        return self._player_sequences.get(player_id, [])
    
    def clear_player_sequence(self, player_id: str) -> None:
        """清空玩家序列"""
        if player_id in self._player_sequences:
            self._player_sequences[player_id] = []
```

---

## 第5天: 验收验证

### 测试框架

**文件**: `tests/rules/test_rules.py`

```python
import pytest
from datetime import datetime
from game_monitoring.rules import (
    RuleEngine, RuleRegistry, RuleExecutionContext,
    ConsecutiveFailuresRule, SocialWithdrawalRule,
    StaminaExhaustionRule, RuleCategory
)


class TestConsecutiveFailuresRule:
    """连续失败规则测试"""
    
    def test_triggers_on_two_failures(self):
        """两次失败应触发"""
        rule = ConsecutiveFailuresRule()
        
        context = RuleExecutionContext(
            player_id="test",
            recent_actions=[
                {'action': 'complete_dungeon', 'params': {'status': 'fail'}},
                {'action': 'complete_dungeon', 'params': {'status': 'fail'}},
            ],
            actions=[]
        )
        
        result = rule.evaluate(context)
        
        assert result.triggered is True
        assert "连续失败2次" in result.description
    
    def test_not_triggered_on_one_failure(self):
        """单次失败不应触发"""
        rule = ConsecutiveFailuresRule()
        
        context = RuleExecutionContext(
            player_id="test",
            recent_actions=[
                {'action': 'complete_dungeon', 'params': {'status': 'fail'}},
                {'action': 'enter_dungeon', 'params': {}}
            ],
            actions=[]
        )
        
        result = rule.evaluate(context)
        
        assert result.triggered is False


class TestRuleEngine:
    """规则引擎集成测试"""
    
    def test_analyze_returns_triggered_rules(self):
        """分析返回触发的规则"""
        engine = RuleEngine()
        
        # 注册测试规则
        engine.registry.register(ConsecutiveFailuresRule())
        
        actions = [
            {'action': 'complete_dungeon', 'params': {'status': 'fail'}},
            {'action': 'complete_dungeon', 'params': {'status': 'fail'}},
            {'action': 'complete_dungeon', 'params': {'status': 'fail'}},
        ]
        
        results = engine.analyze("player_1", actions)
        
        assert len(results) == 1
        assert results[0].rule_id == "consecutive_failures"
    
    def test_get_emotion_from_results(self):
        """从规则结果判断情绪"""
        engine = RuleEngine()
        
        # 模拟负面结果
        results = [type('obj', (), {
            'triggered': True,
            'category': RuleCategory.EMOTION,
            'scenario_name': '连续失败触发消极情绪',
            'priority': 2
        })()]
        
        emotion = engine.get_emotion_from_results(results)
        
        assert emotion == "negative"
```

---

## 迁移检查清单

### 阶段1: 新规则引擎
- [ ] 创建 `rules/` 包结构
- [ ] 实现 `Rule` 基类
- [ ] 实现 `RuleEngine` 和 `RuleRegistry`
- [ ] 迁移11条现有规则到新架构
- [ ] 实现自动规则发现

### 阶段2: 兼容性
- [ ] 新版本 `BehaviorMonitorV2` 实现
- [ ] 保持与旧API的兼容层
- [ ] Streamlit使用新监控器

### 阶段3: 验证
- [ ] 所有规则单元测试
- [ ] 规则引擎集成测试
- [ ] 完整流测试
- [ ] 性能对比（确保无退化）

---

## 验收标准

1. ✅ 11条规则全部迁移完成并工作正常
2. ✅ 新规则可以独立添加/删除
3. ✅ 规则优先级正确生效
4. ✅ 规则分类过滤工作
5. ✅ 引擎性能与旧版持平或更优
6. ✅ 100%规则单元测试覆盖

---

**文档结束**
