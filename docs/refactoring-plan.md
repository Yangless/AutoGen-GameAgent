# 游戏Agent监控系统重构计划

## 文档信息
- **版本**: 1.0.0
- **创建日期**: 2026-04-13
- **作者**: Claude Code
- **状态**: 设计阶段

---

## 一、重构目标

本次重构旨在解决当前系统的架构债务，建立更清晰、可扩展、可测试的系统架构。

### 1.1 核心目标

| 目标 | 优先级 | 说明 |
|------|--------|------|
| 解耦全局依赖 | P0 | 消除全局状态，提高模块独立性和可测试性 |
| 引入依赖注入 | P0 | 建立标准化的依赖管理机制 |
| 规则引擎插件化 | P1 | 支持动态规则注册和扩展 |
| UI/业务分离 | P1 | 实现清晰的关注点分离 |

### 1.2 重构原则

- **向后兼容**: 重构期间保持现有API兼容
- **渐进式演进**: 分阶段实施，避免一次性大规模改动
- **测试优先**: 每一步重构必须有充分的测试覆盖
- **文档同步**: 架构变更同步更新设计文档

---

## 二、解耦全局依赖

### 2.1 当前问题分析

**问题1: 模块级全局变量**
```python
# context.py (当前实现)
_monitor: Optional[BehaviorMonitor] = None
_player_state_manager: Optional[PlayerStateManager] = None
```

**问题2: 全局状态访问点分散**
```python
# 多处直接访问全局上下文
from ..context import get_global_monitor, get_global_player_state_manager
monitor = get_global_monitor()  # 隐式依赖
```

**问题3: 硬编码数据**
- `_players_info` 字典硬编码3个玩家
- `_commander_order` 字符串常量

### 2.2 重构方案

#### 2.2.1 引入领域上下文对象

```python
# core/context.py (新架构)
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

@dataclass(frozen=True)
class GameContext:
    """不可变的游戏上下文对象，作为系统核心依赖"""
    monitor: 'BehaviorMonitor'
    player_state_manager: 'PlayerStateManager'
    player_repository: 'PlayerRepository'
    order_repository: 'OrderRepository'
    config: 'SystemConfig'
    
    def with_player(self, player_id: str) -> 'PlayerContext':
        """创建针对特定玩家的上下文"""
        return PlayerContext(
            game_context=self,
            player_id=player_id
        )

@dataclass(frozen=True)
class PlayerContext:
    """玩家级上下文"""
    game_context: GameContext
    player_id: str
    
    @property
    def monitor(self) -> 'BehaviorMonitor':
        return self.game_context.monitor
    
    @property
    def player_state(self) -> 'PlayerState':
        return self.game_context.player_state_manager.get_player_state(self.player_id)
```

#### 2.2.2 播放器数据重构为 Repository 模式

```python
# repositories/player_repository.py
from abc import ABC, abstractmethod
from typing import Dict, Optional, List

class PlayerRepository(ABC):
    """玩家数据仓储抽象"""
    
    @abstractmethod
    def get_by_name(self, player_name: str) -> Optional[Dict[str, Any]]: ...
    
    @abstractmethod
    def get_all_names(self) -> List[str]: ...
    
    @abstractmethod
    def save(self, player_name: str, data: Dict[str, Any]) -> None: ...

class InMemoryPlayerRepository(PlayerRepository):
    """内存实现（用于开发和测试）"""
    def __init__(self, initial_data: Optional[Dict] = None):
        self._storage = initial_data or {}
    
    def get_by_name(self, player_name: str) -> Optional[Dict[str, Any]]:
        return self._storage.get(player_name)
    
    def get_all_names(self) -> List[str]:
        return list(self._storage.keys())
    
    def save(self, player_name: str, data: Dict[str, Any]) -> None:
        self._storage[player_name] = data

class YamlPlayerRepository(PlayerRepository):
    """YAML配置实现（用于生产）"""
    def __init__(self, config_path: str):
        self._config_path = config_path
        self._data = self._load_from_yaml()
    
    def _load_from_yaml(self) -> Dict:
        # 从YAML文件加载玩家配置
        pass
```

#### 2.2.3 迁移路径

**阶段1: 双轨运行（向后兼容）**
```python
# context.py (迁移兼容层)
_context_instance: Optional[GameContext] = None

def set_global_context(context: GameContext) -> None:
    """新的全局上下文设置方式"""
    global _context_instance
    _context_instance = context
    
    # 为旧代码保留兼容性
    _monitor = context.monitor
    _player_state_manager = context.player_state_manager

def get_global_monitor() -> Optional[BehaviorMonitor]:
    """兼容旧API"""
    if _context_instance:
        return _context_instance.monitor
    return _monitor  # 回退到旧的全局变量
```

**阶段2: 渐进式替换**
- 新代码使用 `GameContext` 显式传递
- 旧代码逐步重构

**阶段3: 旧API废弃**
```python
@deprecated("Use GameContext.monitor instead")
def get_global_monitor() -> Optional[BehaviorMonitor]:
    ...
```

---

## 三、引入依赖注入

### 3.1 DI容器设计

```python
# core/container.py
from typing import TypeVar, Type, Dict, Any, Callable
from dataclasses import dataclass

T = TypeVar('T')

@dataclass
class ServiceDescriptor:
    """服务描述符"""
    interface: Type
    implementation: Type
    instance: Optional[Any] = None
    factory: Optional[Callable] = None
    lifetime: str = "singleton"  # singleton | transient | scoped

class DIContainer:
    """轻量级依赖注入容器"""
    
    def __init__(self):
        self._registrations: Dict[Type, ServiceDescriptor] = {}
        self._singletons: Dict[Type, Any] = {}
    
    def register_instance(self, interface: Type[T], instance: T) -> 'DIContainer':
        """注册已有实例"""
        self._singletons[interface] = instance
        return self
    
    def register_factory(self, interface: Type[T], factory: Callable[..., T], 
                        lifetime: str = "transient") -> 'DIContainer':
        """注册工厂函数"""
        self._registrations[interface] = ServiceDescriptor(
            interface=interface,
            implementation=None,
            factory=factory,
            lifetime=lifetime
        )
        return self
    
    def register_class(self, interface: Type[T], implementation: Type[T],
                      lifetime: str = "transient") -> 'DIContainer':
        """注册实现类"""
        self._registrations[interface] = ServiceDescriptor(
            interface=interface,
            implementation=implementation,
            lifetime=lifetime
        )
        return self
    
    def resolve(self, interface: Type[T]) -> T:
        """解析依赖"""
        # 检查单例
        if interface in self._singletons:
            return self._singletons[interface]
        
        descriptor = self._registrations.get(interface)
        if not descriptor:
            raise KeyError(f"未注册的依赖: {interface}")
        
        # 创建实例
        if descriptor.factory:
            instance = descriptor.factory(self)
        else:
            # 自动解析构造函数依赖
            instance = self._create_instance(descriptor.implementation)
        
        # 缓存单例
        if descriptor.lifetime == "singleton":
            self._singletons[interface] = instance
        
        return instance
    
    def _create_instance(self, cls: Type[T]) -> T:
        """自动解析构造函数参数"""
        import inspect
        sig = inspect.signature(cls.__init__)
        params = list(sig.parameters.items())[1:]  # 跳过self
        
        args = []
        for name, param in params:
            if param.annotation != inspect.Parameter.empty:
                args.append(self.resolve(param.annotation))
            else:
                raise ValueError(f"{cls.__name__}.{name} 缺少类型注解")
        
        return cls(*args)
```

### 3.2 系统集成

```python
# core/bootstrap.py
from .container import DIContainer
from ..repositories.player_repository import PlayerRepository, InMemoryPlayerRepository
from ..monitoring.behavior_monitor import BehaviorMonitor
from ..monitoring.player_state import PlayerStateManager
from ..team.team_manager import GameMonitoringTeam

def create_container(config: 'SystemConfig') -> DIContainer:
    """创建并配置DI容器"""
    container = DIContainer()
    
    # 注册配置
    container.register_instance(SystemConfig, config)
    
    # 注册仓储（根据环境选择实现）
    if config.use_yaml_repository:
        container.register_factory(
            PlayerRepository,
            lambda c: YamlPlayerRepository(config.players_config_path),
            lifetime="singleton"
        )
    else:
        container.register_factory(
            PlayerRepository,
            lambda c: InMemoryPlayerRepository(config.initial_players),
            lifetime="singleton"
        )
    
    # 注册核心服务
    container.register_class(
        PlayerStateManager,
        lifetime="singleton"
    )
    
    container.register_factory(
        BehaviorMonitor,
        lambda c: BehaviorMonitor(
            threshold=config.behavior_threshold,
            max_sequence_length=config.max_sequence_length,
            player_state_manager=c.resolve(PlayerStateManager)
        ),
        lifetime="singleton"
    )
    
    # 注册Team（需要动态player_id时作为工厂返回）
    container.register_factory(
        GameMonitoringTeam,
        lambda c: GameMonitoringTeam(
            model_client=config.model_client,
            container=c
        ),
        lifetime="transient"
    )
    
    return container
```

### 3.3 使用方式

```python
# 新方式：构造函数注入
class AnalysisTool:
    def __init__(
        self,
        monitor: BehaviorMonitor,
        player_state_manager: PlayerStateManager
    ):
        self._monitor = monitor
        self._player_state_manager = player_state_manager
    
    def analyze_emotion(self, player_id: str) -> str:
        # 直接使用注入的依赖
        behaviors = self._monitor.get_player_history(player_id)
        ...

# 或使用上下文对象
class ModernAgentFactory:
    def __init__(self, context: GameContext):
        self._context = context
    
    def create_emotion_agent(self, player_id: str) -> AssistantAgent:
        player_ctx = self._context.with_player(player_id)
        return AssistantAgent(
            name="EmotionRecognitionAgent",
            tools=[EmotionAnalysisTool(player_ctx)],
            ...
        )
```

---

## 四、规则引擎插件化架构

### 4.1 当前问题

```python
# 当前规则引擎：硬编码11个_check_方法
class PlayerBehaviorRuleEngine:
    def analyze_action_sequence(self, actions):
        rules_to_check = [
            ('连续失败触发消极情绪', self._check_consecutive_failures, ...),
            ('社交退出行为风险', self._check_social_withdrawal_risk, ...),
            # ... 硬编码规则列表
        ]
```

**问题：**
- 规则与引擎紧耦合
- 无法运行时扩展新规则
- 规则间优先级和互斥难管理

### 4.2 插件化规则引擎设计

```python
# rules/engine.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import importlib
import pkgutil

class RulePriority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

@dataclass
class RuleResult:
    """规则执行结果"""
    rule_id: str
    triggered: bool
    scenario_name: str
    description: str
    confidence: float = 1.0
    metadata: Dict[str, Any] = None

@dataclass
class RuleContext:
    """规则执行上下文"""
    player_id: str
    actions: List[Dict[str, Any]]
    recent_actions: List[Dict[str, Any]]
    player_state: Optional['PlayerState'] = None
    session_data: Dict[str, Any] = None

class Rule(ABC):
    """规则基类"""
    
    @property
    @abstractmethod
    def rule_id(self) -> str: ...
    
    @property
    @abstractmethod
    def scenario_name(self) -> str: ...
    
    @property
    def priority(self) -> RulePriority:
        return RulePriority.MEDIUM
    
    @abstractmethod
    def evaluate(self, context: RuleContext) -> RuleResult: ...
    
    def should_skip(self, context: RuleContext) -> bool:
        """前置条件检查，返回True则跳过该规则"""
        return False

class RuleRegistry:
    """规则注册中心"""
    
    def __init__(self):
        self._rules: Dict[str, Rule] = {}
        self._hooks: Dict[str, List[Callable]] = {
            'pre_evaluation': [],
            'post_evaluation': [],
        }
    
    def register(self, rule: Rule) -> 'RuleRegistry':
        """注册规则"""
        self._rules[rule.rule_id] = rule
        return self
    
    def unregister(self, rule_id: str) -> None:
        """注销规则"""
        self._rules.pop(rule_id, None)
    
    def get_applicable_rules(self, context: RuleContext) -> List[Rule]:
        """获取适用的规则列表"""
        applicable = [
            rule for rule in self._rules.values()
            if not rule.should_skip(context)
        ]
        # 按优先级排序
        return sorted(applicable, key=lambda r: r.priority.value)
    
    def evaluate_all(self, context: RuleContext) -> List[RuleResult]:
        """评估所有适用规则"""
        results = []
        
        # 执行前置hook
        for hook in self._hooks['pre_evaluation']:
            hook(context)
        
        for rule in self.get_applicable_rules(context):
            try:
                result = rule.evaluate(context)
                if result.triggered:
                    results.append(result)
            except Exception as e:
                logger.error(f"规则 {rule.rule_id} 执行失败: {e}")
        
        # 执行后置hook
        for hook in self._hooks['post_evaluation']:
            hook(context, results)
        
        return results
    
    def register_hook(self, event: str, callback: Callable) -> None:
        """注册事件hook"""
        if event in self._hooks:
            self._hooks[event].append(callback)
```

### 4.3 具体规则实现示例

```python
# rules/definitions/emotion_rules.py
from ..engine import Rule, RuleResult, RuleContext, RulePriority

class ConsecutiveFailuresRule(Rule):
    """连续失败触发消极情绪规则"""
    
    @property
    def rule_id(self) -> str:
        return "consecutive_failures"
    
    @property
    def scenario_name(self) -> str:
        return "连续失败触发消极情绪"
    
    @property
    def priority(self) -> RulePriority:
        return RulePriority.HIGH
    
    def evaluate(self, context: RuleContext) -> RuleResult:
        actions = context.recent_actions
        if len(actions) < 3:
            return RuleResult(
                rule_id=self.rule_id,
                triggered=False,
                scenario_name=self.scenario_name,
                description="动作数量不足"
            )
        
        failure_actions = ['complete_dungeon', 'recruit_hero', 'lose_pvp']
        consecutive_failures = 0
        failure_details = []
        
        for action in reversed(actions):
            action_name = action.get('action', '')
            if action_name in failure_actions:
                status = action.get('params', {}).get('status', '')
                if self._is_failure(action_name, status):
                    consecutive_failures += 1
                    failure_details.insert(0, action_name)
            else:
                break
        
        triggered = consecutive_failures >= 2
        return RuleResult(
            rule_id=self.rule_id,
            triggered=triggered,
            scenario_name=self.scenario_name,
            description=f"连续失败{consecutive_failures}次: {', '.join(failure_details[:3])}" if triggered else "未检测到连续失败",
            confidence=min(consecutive_failures / 3.0, 1.0),
            metadata={
                'failure_count': consecutive_failures,
                'failure_details': failure_details
            }
        )
    
    def _is_failure(self, action_name: str, status: str) -> bool:
        if action_name == 'lose_pvp':
            return True
        if status == 'fail':
            return True
        return False

class StaminaExhaustionRule(Rule):
    """体力耗尽引导触发规则"""
    
    @property
    def rule_id(self) -> str:
        return "stamina_exhaustion"
    
    @property
    def scenario_name(self) -> str:
        return "体力耗尽引导触发"
    
    @property
    def priority(self) -> RulePriority:
        return RulePriority.CRITICAL
    
    def evaluate(self, context: RuleContext) -> RuleResult:
        stamina_keywords = ['stamina_exhausted', 'attempt_enter_dungeon_no_stamina']
        stamina_count = sum(
            1 for a in context.actions
            if any(kw in a.get('action', '').lower() for kw in stamina_keywords)
        )
        
        threshold = context.session_data.get('stamina_threshold', 3)
        triggered = stamina_count >= threshold
        
        return RuleResult(
            rule_id=self.rule_id,
            triggered=triggered,
            scenario_name=self.scenario_name,
            description=f"检测到{stamina_count}次体力耗尽事件" if triggered else "未达阈值",
            confidence=min(stamina_count / threshold, 1.0),
            metadata={'stamina_count': stamina_count, 'threshold': threshold}
        )
```

### 4.4 自动规则发现

```python
# rules/loader.py
import importlib
import pkgutil
from pathlib import Path

def auto_discover_rules(package_name: str = "rules.definitions") -> List[Rule]:
    """自动发现并加载规则"""
    rules = []
    
    package = importlib.import_module(package_name)
    package_path = Path(package.__file__).parent
    
    for _, module_name, _ in pkgutil.iter_modules([str(package_path)]):
        module = importlib.import_module(f".{module_name}", package_name)
        
        # 寻找Rule的子类
        for name in dir(module):
            obj = getattr(module, name)
            if (isinstance(obj, type) and 
                issubclass(obj, Rule) and 
                obj is not Rule and
                not getattr(obj, '__abstractmethods__', None)):
                rules.append(obj())
    
    return rules

# 在应用启动时
registry = RuleRegistry()
for rule in auto_discover_rules():
    registry.register(rule)
```

### 4.5 规则组合与互斥

```python
@dataclass
class RuleComposition:
    """规则组合逻辑"""
    rule_ids: List[str]
    logic: str = "OR"  # AND, OR, NOT, SEQUENCE
    result_scenario: str = ""

class RuleOrchestrator:
    """规则编排器，处理复杂交互"""
    
    def __init__(self, registry: RuleRegistry):
        self._registry = registry
        self._compositions: List[RuleComposition] = []
    
    def add_composition(self, composition: RuleComposition) -> None:
        """添加规则组合"""
        self._compositions.append(composition)
    
    def evaluate_with_compositions(self, context: RuleContext) -> List[RuleResult]:
        """评估包含组合逻辑"""
        base_results = self._registry.evaluate_all(context)
        triggered_ids = {r.rule_id for r in base_results if r.triggered}
        
        for comp in self._compositions:
            if self._evaluate_composition(comp, triggered_ids):
                # 添加组合结果
                base_results.append(RuleResult(
                    rule_id=f"composition_{comp.logic}",
                    triggered=True,
                    scenario_name=comp.result_scenario,
                    description=f"规则组合触发: {comp.logic}"
                ))
        
        return base_results
    
    def _evaluate_composition(self, comp: RuleComposition, triggered: set) -> bool:
        if comp.logic == "AND":
            return all(r in triggered for r in comp.rule_ids)
        elif comp.logic == "OR":
            return any(r in triggered for r in comp.rule_ids)
        elif comp.logic == "NOT":
            return not any(r in triggered for r in comp.rule_ids)
        return False
```

---

## 五、UI与业务逻辑分离

### 5.1 当前问题

`streamlit_dashboard.py` 承载了1400+行代码，混合了：
- Streamlit UI组件（按钮、布局、样式）
- 业务逻辑（动作处理、Agent触发、规则检查）
- 数据转换（格式转换、JSON解析）
- 会话状态管理

### 5.2 分层架构设计

```
┌─────────────────────────────────────────────┐
│           Presentation Layer                │
│  (UI/components + pages + views)           │
├─────────────────────────────────────────────┤
│           Application Layer                 │
│  (services + usecases + orchestrators)     │
├─────────────────────────────────────────────┤
│           Domain Layer                     │
│  (models + repositories + rules)           │
├─────────────────────────────────────────────┤
│           Infrastructure Layer              │
│  (storage + external APIs + config)        │
└─────────────────────────────────────────────┘
```

### 5.3 具体重构方案

#### 5.3.1 Application Service层

```python
# application/services/action_service.py
from typing import List, Dict, Any, Protocol
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class ActionResult(Enum):
    SUCCESS = "success"
    RULE_TRIGGERED = "rule_triggered"
    AGENT_TRIGGERED = "agent_triggered"
    ERROR = "error"

@dataclass
class ActionProcessingResult:
    """动作处理结果"""
    result: ActionResult
    player_id: str
    action_name: str
    triggered_scenarios: List[Dict] = None
    emotion_type: str = "neutral"
    should_intervene: bool = False
    message: str = ""

class ActionProcessingService:
    """动作处理应用服务"""
    
    def __init__(
        self,
        rule_engine: RuleRegistry,
        player_state_manager: PlayerStateManager,
        agent_trigger: 'AgentTriggerService',
        action_repository: 'ActionRepository'
    ):
        self._rule_engine = rule_engine
        self._player_state = player_state_manager
        self._agent_trigger = agent_trigger
        self._action_repo = action_repository
    
    async def process_action(
        self,
        player_id: str,
        action_name: str,
        action_params: Dict[str, Any] = None
    ) -> ActionProcessingResult:
        """
        处理玩家动作的核心流程：
        1. 保存动作
        2. 规则引擎分析
        3. 更新玩家状态
        4. 判断是否需要触发Agent
        """
        try:
            # 1. 创建并保存动作
            action = PlayerAction(
                player_id=player_id,
                action_name=action_name,
                params=action_params or {},
                timestamp=datetime.now()
            )
            await self._action_repo.save(action)
            
            # 2. 准备规则上下文
            recent_actions = await self._action_repo.get_recent_actions(player_id, limit=3)
            all_actions = await self._action_repo.get_player_actions(player_id)
            
            context = RuleContext(
                player_id=player_id,
                actions=all_actions,
                recent_actions=recent_actions,
                player_state=self._player_state.get_player_state(player_id)
            )
            
            # 3. 规则引擎评估
            results = self._rule_engine.evaluate_all(context)
            triggered = [r for r in results if r.triggered]
            
            # 4. 情绪分析
            emotion_type = self._determine_emotion_type(triggered)
            
            # 5. 更新玩家负面行为计数
            should_intervene = False
            if emotion_type == "negative":
                current_count = await self._increment_negative_count(player_id)
                threshold = 3  # 可配置
                should_intervene = current_count >= threshold
                
                if should_intervene:
                    await self._agent_trigger.trigger_intervention(player_id, triggered)
                    await self._reset_negative_count(player_id)
            
            return ActionProcessingResult(
                result=ActionResult.AGENT_TRIGGERED if should_intervene else ActionResult.SUCCESS,
                player_id=player_id,
                action_name=action_name,
                triggered_scenarios=[r.to_dict() for r in triggered],
                emotion_type=emotion_type,
                should_intervene=should_intervene
            )
            
        except Exception as e:
            return ActionProcessingResult(
                result=ActionResult.ERROR,
                player_id=player_id,
                action_name=action_name,
                message=str(e)
            )
    
    async def _increment_negative_count(self, player_id: str) -> int:
        # 实现计数递增
        pass
    
    async def _reset_negative_count(self, player_id: str) -> None:
        # 重置计数
        pass
    
    def _determine_emotion_type(self, triggered_results: List[RuleResult]) -> str:
        """根据触发的规则判断情绪类型"""
        priority = {'negative': 2, 'abnormal': 1, 'positive': 0}
        max_priority = -1
        
        for result in triggered_results:
            for key, value in priority.items():
                if key in result.scenario_name.lower() and value > max_priority:
                    max_priority = value
                    return key
        
        return "neutral"
```

#### 5.3.2 UI组件层

```python
# ui/components/player_status_panel.py
import streamlit as st
from typing import Protocol

class PlayerStatePresenter(Protocol):
    """Player状态展示协议"""
    def get_player_name(self) -> str: ...
    def get_team_stamina(self) -> List[int]: ...
    def get_emotion(self) -> str: ...
    def get_churn_risk(self) -> str: ...

class PlayerStatusPanel:
    """玩家状态面板组件（纯UI，无业务逻辑）"""
    
    def __init__(self, presenter: PlayerStatePresenter):
        self._presenter = presenter
    
    def render(self):
        """渲染面板"""
        st.markdown('<h2 class="section-header">玩家状态</h2>', unsafe_allow_html=True)
        
        # 玩家基本信息
        st.markdown(
            f'<div class="player-info"><strong>玩家ID:</strong> {self._presenter.get_player_name()}</div>',
            unsafe_allow_html=True
        )
        
        # 情绪状态
        emotion = self._presenter.get_emotion()
        st.metric("当前情绪", emotion)
        
        # 流失风险
        churn_risk = self._presenter.get_churn_risk()
        st.metric("流失风险", churn_risk)

# ui/components/action_grid.py
class ActionGridComponent:
    """动作网格组件"""
    
    ACTION_NAME_MAPPING = {
        "login": "登录游戏",
        "logout": "退出登录",
        "enter_dungeon": "进入副本",
        # ... 36个动作
    }
    
    def __init__(self, on_action_click: Callable[[str], None]):
        self._on_click = on_action_click
        self._definitions = PlayerActionDefinitions()
    
    def render(self):
        """渲染动作网格"""
        categories = [
            ("🎮 核心游戏动作", self._definitions.core_game_actions),
            ("👥 社交动作", self._definitions.social_actions),
            ("💰 经济动作", self._definitions.economic_actions),
            ("📋 元数据动作", self._definitions.meta_actions),
        ]
        
        for title, actions in categories:
            self._render_category(title, actions)
    
    def _render_category(self, title: str, actions: List[str]):
        st.markdown(f"### {title}")
        
        cols = st.columns(3)
        for idx, action in enumerate(actions):
            action_name = action.split('(')[0]
            chinese_name = self.ACTION_NAME_MAPPING.get(action_name, action_name)
            
            with cols[idx % 3]:
                if st.button(
                    chinese_name,
                    key=f"action_{action_name}",
                    use_container_width=True
                ):
                    self._on_click(action_name)
```

#### 5.3.3 Page层

```python
# ui/pages/dashboard.py
class DashboardPage:
    """Dashboard页面（协调层）"""
    
    def __init__(
        self,
        container: DIContainer,
        action_service: ActionProcessingService
    ):
        self._container = container
        self._action_service = action_service
        self._init_session_state()
    
    def _init_session_state(self):
        """初始化session state"""
        defaults = {
            'current_player_id': "孤独的凤凰战士",
            'behavior_logs': [],
            'agent_logs': [],
            'player_negative_counts': {},
            'action_sequence': [],
        }
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value
    
    def render(self):
        """渲染整个页面"""
        st.set_page_config(...)
        st.markdown("...")  # CSS样式
        
        # 三栏布局
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            self._render_player_panel()
        
        with col2:
            self._render_agent_panel()
        
        with col3:
            self._render_action_panel()
    
    def _render_player_panel(self):
        """渲染左侧面板"""
        presenter = self._create_presenter()
        panel = PlayerStatusPanel(presenter)
        panel.render()
    
    def _render_action_panel(self):
        """渲染右侧面板"""
        grid = ActionGridComponent(
            on_action_click=self._handle_action_click
        )
        grid.render()
    
    async def _handle_action_click(self, action_name: str):
        """处理动作点击（异步）"""
        player_id = st.session_state.current_player_id
        
        result = await self._action_service.process_action(player_id, action_name)
        
        # 更新UI状态
        self._add_behavior_log(player_id, action_name)
        self._add_agent_log(f"🎯 执行动作: {action_name}")
        
        if result.triggered_scenarios:
            for scenario in result.triggered_scenarios:
                self._add_agent_log(f"🎭 触发场景: {scenario['scenario']}")
        
        if result.should_intervene:
            self._add_agent_log(f"🚨 达到阈值，触发Agent干预")
        
        st.rerun()
```

#### 5.3.4 Presenter模式

```python
# ui/presenters/player_presenter.py
class PlayerStatePresenter:
    """Player状态展示器（适配领域模型到UI）"""
    
    def __init__(self, player_state: PlayerState):
        self._state = player_state
    
    def get_player_name(self) -> str:
        return self._state.player_name or self._state.player_id
    
    def get_team_stamina(self) -> List[int]:
        return self._state.team_stamina or [100, 100, 100, 100]
    
    def get_emotion(self) -> str:
        emotion = self._state.emotion or "未知"
        confidence = self._state.emotion_confidence or 0.0
        return f"{emotion} ({confidence:.0%})"
    
    def get_emotion_keywords(self) -> str:
        return ", ".join(self._state.emotion_keywords or [])
    
    def get_churn_risk(self) -> str:
        level = self._state.churn_risk_level or "未知"
        score = self._state.churn_risk_score or 0.0
        return f"{level} ({score:.2f})"
    
    def get_recent_behaviors(self, limit: int = 5) -> List[Dict]:
        """获取最近行为（适配展示格式）"""
        # 从repository获取并格式化
        pass
```

### 5.4 Streamlit专用优化

```python
# ui/adapters/streamlit_adapter.py
class StreamlitSessionStateAdapter:
    """Streamlit session state适配器"""
    
    def __init__(self, prefix: str = ""):
        self._prefix = prefix
    
    def get(self, key: str, default=None):
        full_key = f"{self._prefix}{key}"
        return st.session_state.get(full_key, default)
    
    def set(self, key: str, value):
        full_key = f"{self._prefix}{key}"
        st.session_state[full_key] = value
    
    def append_to_list(self, key: str, value, max_size: int = None):
        """追加到列表并限制大小"""
        lst = self.get(key, [])
        lst.append(value)
        if max_size and len(lst) > max_size:
            lst = lst[-max_size:]
        self.set(key, lst)

# ui/utils/async_utils.py
import asyncio
from functools import wraps

def st_async(func):
    """Streamlit异步装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(func(*args, **kwargs))
    return wrapper
```

---

## 六、重构路线图

### 阶段1: 基础设施搭建 (Week 1-2)

**目标**: 为新架构铺设基础设施，保持向后兼容

**任务清单**:
- [ ] 创建 `core/` 包结构
- [ ] 实现 `GameContext` 领域上下文
- [ ] 实现简易DI容器
- [ ] 创建 `repositories/` 抽象和内存实现
- [ ] 添加兼容层保持现有代码运行

**产出**:
- `core/context.py` - 新上下文系统
- `core/container.py` - DI容器
- `repositories/` - 仓储层

### 阶段2: 规则引擎重构 (Week 3-4)

**目标**: 实现插件化规则引擎

**任务清单**:
- [ ] 创建 `rules/` 包结构
- [ ] 实现 `Rule` 抽象基类
- [ ] 实现 `RuleRegistry` 注册中心
- [ ] 迁移现有11条规则到插件架构
- [ ] 实现自动规则发现机制
- [ ] 编写规则单元测试

**产出**:
- `rules/engine.py` - 规则引擎核心
- `rules/definitions/` - 所有规则定义
- 规则开发文档

### 阶段3: 业务逻辑迁移 (Week 5-6)

**目标**: 分离UI和业务逻辑

**任务清单**:
- [ ] 创建 `application/` 层
- [ ] 实现 `ActionProcessingService`
- [ ] 实现 `AgentTriggerService`
- [ ] 重构 `streamlit_dashboard.py` 使用新服务
- [ ] 添加Presenter层

**产出**:
- `application/services/` - 应用服务
- 重构后的 `streamlit_dashboard.py`

### 阶段4: 全局依赖清理 (Week 7-8)

**目标**: 移除全局依赖，完成架构迁移

**任务清单**:
- [ ] 重构所有使用 `get_global_xxx()` 的代码
- [ ] 添加构造函数注入
- [ ] 移除兼容层
- [ ] 完整集成测试
- [ ] 性能基准测试

**产出**:
- 清理后的代码库
- 性能测试报告

---

## 七、风险缓解

| 风险 | 影响 | 缓解策略 |
|------|------|----------|
| 重构引入Bug | 高 | 每阶段增加单元测试覆盖率到80%+ |
| 性能下降 | 中 | 增加抽象层基准，对比重构前后性能 |
| API破坏性变更 | 高 | 保持向后兼容层至少1个版本 |
| 团队学习成本 | 中 | 编写详细迁移指南，结对编程 |
| 进度延迟 | 中 | 采用增量交付，MVP优先 |

---

## 八、测试策略

### 单元测试

```python
# tests/rules/test_emotion_rules.py
class TestConsecutiveFailuresRule:
    def setup_method(self):
        self.rule = ConsecutiveFailuresRule()
    
    def test_triggers_on_three_failures(self):
        context = RuleContext(
            player_id="player_1",
            actions=[
                {'action': 'complete_dungeon', 'params': {'status': 'fail'}},
                {'action': 'complete_dungeon', 'params': {'status': 'fail'}},
                {'action': 'complete_dungeon', 'params': {'status': 'fail'}},
            ],
            recent_actions=[...]
        )
        
        result = self.rule.evaluate(context)
        
        assert result.triggered is True
        assert "连续失败" in result.description
```

### 集成测试

```python
# tests/integration/test_action_processing.py
class TestActionProcessingFlow:
    async def test_full_flow_triggers_agent(self):
        # 使用内存仓储和模拟Agent
        container = create_test_container()
        service = container.resolve(ActionProcessingService)
        
        # 模拟3次消极行为
        for _ in range(3):
            result = await service.process_action("player_1", "click_exit_game_button")
        
        assert result.should_intervene is True
```

---

## 九、附录

### A. 术语表

| 术语 | 说明 |
|------|------|
| 原子动作 | 游戏中最细粒度的玩家操作，如"login", "enter_dungeon" |
| 高层级场景 | 由一组原子动作组合而成的业务场景，如"玩家流失风险" |
| Agent | AutoGen框架中的智能体，负责特定领域分析 |
| GroupChat | AutoGen中多Agent协作的会话机制 |

### B. 参考资料

1. AutoGen Documentation - https://microsoft.github.io/autogen/
2. Clean Architecture - Robert C. Martin
3. Domain-Driven Design - Eric Evans
4. Streamlit Best Practices - https://docs.streamlit.io/

### C. 变更日志

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 1.0.0 | 2026-04-13 | 初始版本 |

---

**文档结束**
