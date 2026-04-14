# 迭代1: 依赖注入实施指南

## 概述
本迭代聚焦于建立依赖注入基础设施，实现从全局状态到显式依赖的过渡。

---

## 第1天: 基础设施搭建

### 目标目录结构

```
autogen-agent/
├── core/
│   ├── __init__.py
│   ├── container.py          # DI容器
│   ├── context.py            # 领域上下文
│   └── bootstrap.py          # 系统引导
├── application/
│   ├── __init__.py
│   └── services/
│       ├── __init__.py
│       └── action_service.py
├── domain/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── player_action.py
│   └── repositories/
│       ├── __init__.py
│       └── player_repository.py
└── infrastructure/
    ├── __init__.py
    └── repositories/
        └── memory_player_repository.py
```

### 步骤1: 创建DI容器

**文件**: `core/container.py`

这是一个经过优化的轻量级DI容器实现，包含完整文档和类型支持：

```python
"""
依赖注入容器实现

设计目标:
1. 轻量级、无外部依赖
2. 支持构造函数注入
3. 支持单例和瞬态生命周期
4. 类型安全的解析
"""

from typing import TypeVar, Type, Dict, Any, Callable, Optional, get_type_hints
from enum import Enum
import inspect
import threading

T = TypeVar('T')

class LifetimeScope(Enum):
    """服务生命周期作用域"""
    SINGLETON = "singleton"      # 全局单例
    TRANSIENT = "transient"      # 每次解析新实例
    SCOPED = "scoped"            # 作用域内单例

class ServiceDescriptor:
    """
    服务描述符
    
    描述如何创建特定接口的实例
    """
    
    def __init__(
        self,
        interface: Type,
        implementation: Optional[Type] = None,
        factory: Optional[Callable] = None,
        instance: Optional[Any] = None,
        lifetime: LifetimeScope = LifetimeScope.TRANSIENT
    ):
        self.interface = interface
        self.implementation = implementation
        self.factory = factory
        self.instance = instance  # 单例缓存
        self.lifetime = lifetime
    
    def __repr__(self):
        return f"<ServiceDescriptor {self.interface.__name__} -> {self.implementation.__name__ if self.implementation else 'factory'}>"


class DIContainer:
    """
    轻量级依赖注入容器
    
    使用示例:
    
    ```python
    container = DIContainer()
    
    # 注册类
    container.register_class(Config, lifetime=LifetimeScope.SINGLETON)
    
    # 注册接口映射到实现
    container.register_interface(Logger, ConsoleLogger)
    
    # 注册工厂
    container.register_factory(BehaviorMonitor, 
                               lambda c: BehaviorMonitor(c.resolve(PlayerStateManager)))
    
    # 注册实例
    container.register_instance(SystemConfig, config)
    
    # 解析
    monitor = container.resolve(BehaviorMonitor)
    ```
    """
    
    def __init__(self):
        self._registrations: Dict[Type, ServiceDescriptor] = {}
        self._singletons: Dict[Type, Any] = {}
        self._lock = threading.RLock()
        self._resolution_stack: set = set()  # 检测循环依赖
    
    def register_class(
        self,
        cls: Type[T],
        *,
        lifetime: LifetimeScope = LifetimeScope.TRANSIENT
    ) -> 'DIContainer':
        """
        注册类自身（自注册）
        
        Args:
            cls: 类类型
            lifetime: 生命周期
        """
        descriptor = ServiceDescriptor(
            interface=cls,
            implementation=cls,
            lifetime=lifetime
        )
        self._registrations[cls] = descriptor
        return self
    
    def register_interface(
        self,
        interface: Type[T],
        implementation: Type[T],
        *,
        lifetime: LifetimeScope = LifetimeScope.TRANSIENT
    ) -> 'DIContainer':
        """
        注册接口到实现的映射
        
        Args:
            interface: 抽象接口
            implementation: 具体实现类
            lifetime: 生命周期
        """
        descriptor = ServiceDescriptor(
            interface=interface,
            implementation=implementation,
            lifetime=lifetime
        )
        self._registrations[interface] = descriptor
        return self
    
    def register_factory(
        self,
        interface: Type[T],
        factory: Callable[['DIContainer'], T],
        *,
        lifetime: LifetimeScope = LifetimeScope.TRANSIENT
    ) -> 'DIContainer':
        """
        注册工厂函数
        
        Args:
            interface: 接口类型
            factory: 工厂函数，接收容器参数
            lifetime: 生命周期
        """
        descriptor = ServiceDescriptor(
            interface=interface,
            factory=factory,
            lifetime=lifetime
        )
        self._registrations[interface] = descriptor
        return self
    
    def register_instance(self, interface: Type[T], instance: T) -> 'DIContainer':
        """
        注册已有实例（总是单例）
        
        Args:
            interface: 接口类型
            instance: 实例对象
        """
        descriptor = ServiceDescriptor(
            interface=interface,
            instance=instance,
            lifetime=LifetimeScope.SINGLETON
        )
        self._registrations[interface] = descriptor
        self._singletons[interface] = instance
        return self
    
    def resolve(self, interface: Type[T]) -> T:
        """
        解析依赖
        
        Args:
            interface: 要解析的接口/类
            
        Returns:
            接口的实现实例
            
        Raises:
            KeyError: 未注册的依赖
            CircularDependencyError: 检测到循环依赖
        """
        # 检查循环依赖
        if interface in self._resolution_stack:
            raise CircularDependencyError(
                f"检测到循环依赖: {' -> '.join(self._resolution_stack)} -> {interface}"
            )
        
        with self._lock:
            # 检查是否是单例
            if interface in self._singletons:
                return self._singletons[interface]
            
            descriptor = self._registrations.get(interface)
            if not descriptor:
                # 可以尝试自动注册（可选功能）
                raise KeyError(f"未注册的依赖: {interface.__name__}")
            
            # 创建实例
            self._resolution_stack.add(interface)
            try:
                instance = self._create_from_descriptor(descriptor)
            finally:
                self._resolution_stack.discard(interface)
            
            # 缓存单例
            if descriptor.lifetime == LifetimeScope.SINGLETON:
                self._singletons[interface] = instance
            
            return instance
    
    def _create_from_descriptor(self, descriptor: ServiceDescriptor) -> Any:
        """根据描述符创建实例"""
        if descriptor.instance:
            return descriptor.instance
        
        if descriptor.factory:
            return descriptor.factory(self)
        
        if descriptor.implementation:
            return self._create_with_injection(descriptor.implementation)
        
        raise ValueError(f"无法创建 {descriptor.interface} 的实例")
    
    def _create_with_injection(self, cls: Type[T]) -> T:
        """
        自动解析构造函数参数并创建实例
        
        使用inspect检测构造函数签名，自动注入依赖
        """
        try:
            # 获取__init__方法的签名
            init_method = getattr(cls, '__init__', None)
            if init_method is None:
                return cls()
            
            # 获取参数类型提示
            type_hints = get_type_hints(init_method)
            
            # 获取完整的参数列表
            sig = inspect.signature(init_method)
            parameters = list(sig.parameters.items())
            
            # 跳过'self'
            if parameters:
                parameters = parameters[1:]
            
            # 准备构造函数参数
            args = []
            kwargs = {}
            
            for param_name, param in parameters:
                param_type = type_hints.get(param_name)
                
                # 如果有默认值且没有类型提示，跳过
                if param.default is not inspect.Parameter.empty and param_type is None:
                    continue
                
                # 如果参数有Optional，提取实际类型
                if param_type:
                    origin = getattr(param_type, '__origin__', None)
                    if origin is not None:
                        # 处理 Optional, List, Dict等泛型
                        if origin is type(None) or origin is None:
                            # Optional[X] -> X
                            args_type = getattr(param_type, '__args__', None)
                            if args_type:
                                param_type = args_type[0]
                    
                    try:
                        resolved = self.resolve(param_type)
                        
                        # 根据参数类型位置决定使用args还是kwargs
                        if param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
                            args.append(resolved)
                        elif param.kind == inspect.Parameter.KEYWORD_ONLY:
                            kwargs[param_name] = resolved
                            
                    except KeyError:
                        if param.default is not inspect.Parameter.empty:
                            # 使用默认值
                            continue
                        # 不改变原有逻辑：允许None参数
                        if 'Optional' in str(param_type):
                            if param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
                                args.append(None)
                            else:
                                kwargs[param_name] = None
                        else:
                            raise
            
            return cls(*args, **kwargs)
            
        except Exception as e:
            raise RuntimeError(f"创建 {cls.__name__} 实例失败: {e}") from e
    
    def create_scope(self) -> 'DIScope':
        """创建新的作用域（用于SCOPED生命周期）"""
        return DIScope(self)
    
    def is_registered(self, interface: Type) -> bool:
        """检查是否已注册"""
        return interface in self._registrations
    
    def list_registrations(self) -> Dict[Type, ServiceDescriptor]:
        """列出所有注册（用于调试）"""
        return dict(self._registrations)


class DIScope:
    """
    依赖注入作用域
    
    用于管理SCOPED生命周期的实例
    通常在HTTP请求或任务处理开始时创建，结束时清理
    """
    
    def __init__(self, container: DIContainer):
        self._container = container
        self._scoped_instances: Dict[Type, Any] = {}
    
    def resolve(self, interface: Type[T]) -> T:
        """在作用域内解析"""
        # 检查是否是scoped且已在当前作用域中
        descriptor = self._container._registrations.get(interface)
        if descriptor and descriptor.lifetime == LifetimeScope.SCOPED:
            if interface in self._scoped_instances:
                return self._scoped_instances[interface]
            
            instance = self._container.resolve(interface)
            self._scoped_instances[interface] = instance
            return instance
        
        # 非scoped，委托给容器
        return self._container.resolve(interface)
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        # 清理scoped实例
        self._scoped_instances.clear()


class CircularDependencyError(Exception):
    """循环依赖错误"""
    pass


# 辅助装饰器
def inject(cls: Type[T]) -> Type[T]:
    """
    标记类支持自动注入
    
    使用方式:
    ```python
    @inject
    class MyService:
        def __init__(self, other_service: OtherService):
            self.other = other_service
    ```
    """
    # 可以在这里添加额外的元数据处理
    return cls
```

### 步骤2: 创建领域上下文

**文件**: `core/context.py`

```python
"""
领域上下文

提供应用级别的上下文对象，替代全局变量
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional, Dict, Any
from datetime import datetime

if TYPE_CHECKING:
    from ..monitoring.behavior_monitor import BehaviorMonitor
    from ..monitoring.player_state import PlayerStateManager
    from ..domain.repositories.player_repository import PlayerRepository


@dataclass(frozen=True)
class SystemConfig:
    """系统配置"""
    behavior_threshold: int = 3
    max_sequence_length: int = 50
    recent_actions_window: int = 3
    auto_reset_after_intervention: bool = True
    use_yaml_repository: bool = False
    players_config_path: str = "config/players.yaml"
    initial_players: Optional[Dict] = None


@dataclass
class PlayerSnapshot:
    """玩家状态快照（用于分析）"""
    player_id: str
    emotion: Optional[str] = None
    emotion_confidence: float = 0.0
    churn_risk_level: Optional[str] = None
    churn_risk_score: float = 0.0
    is_bot: bool = False
    bot_confidence: float = 0.0
    team_stamina: Optional[list] = None
    backpack_items: Optional[list] = None
    timestamp: datetime = field(default_factory=datetime.now)


class GameContext:
    """
    游戏应用上下文
    
    作为核心协调对象，提供系统级别的依赖访问
    通过构造函数显式传递，替代全局变量
    
    使用示例:
    ```python
    context = GameContext(
        monitor=monitor,
        player_state_manager=state_manager,
        config=config
    )
    
    # 使用
    history = context.monitor.get_player_history("player_1")
    ```
    """
    
    def __init__(
        self,
        monitor: 'BehaviorMonitor',
        player_state_manager: 'PlayerStateManager',
        config: SystemConfig = None
    ):
        self._monitor = monitor
        self._player_state_manager = player_state_manager
        self._config = config or SystemConfig()
    
    @property
    def monitor(self) -> 'BehaviorMonitor':
        """行为监控器"""
        return self._monitor
    
    @property
    def player_state_manager(self) -> 'PlayerStateManager':
        """玩家状态管理器"""
        return self._player_state_manager
    
    @property
    def config(self) -> SystemConfig:
        """系统配置"""
        return self._config
    
    def for_player(self, player_id: str) -> 'PlayerContext':
        """
        创建玩家级上下文
        
        Args:
            player_id: 玩家ID
            
        Returns:
            玩家上下文
        """
        return PlayerContext(self, player_id)
    
    def get_player_snapshot(self, player_id: str) -> PlayerSnapshot:
        """获取玩家状态快照"""
        state = self._player_state_manager.get_player_state(player_id)
        return PlayerSnapshot(
            player_id=player_id,
            emotion=state.emotion,
            emotion_confidence=state.emotion_confidence,
            churn_risk_level=state.churn_risk_level,
            churn_risk_score=state.churn_risk_score,
            is_bot=state.is_bot,
            bot_confidence=state.bot_confidence,
            team_stamina=state.team_stamina,
            backpack_items=state.backpack_items
        )


class PlayerContext:
    """
    玩家级上下文
    
    提供针对特定玩家的便捷访问
    """
    
    def __init__(self, game_context: GameContext, player_id: str):
        self._game = game_context
        self._player_id = player_id
    
    @property
    def game_context(self) -> GameContext:
        """上一级游戏上下文"""
        return self._game
    
    @property
    def player_id(self) -> str:
        """当前玩家ID"""
        return self._player_id
    
    @property
    def player_state(self):
        """当前玩家状态"""
        return self._game.player_state_manager.get_player_state(self._player_id)
    
    def get_action_history(self, limit: int = None):
        """获取玩家动作历史"""
        history = self._game.monitor.get_player_history(self._player_id)
        if limit:
            return history[-limit:]
        return history
    
    def get_action_sequence(self):
        """获取玩家动作序列"""
        return self._game.monitor.get_player_action_sequence(self._player_id)


# 兼容性层（临时）
_global_context: Optional[GameContext] = None


def set_global_context(context: GameContext) -> None:
    """
    设置全局上下文（兼容性）
    
    警告: 将逐步废弃，使用依赖注入
    """
    global _global_context
    _global_context = context


def get_global_context() -> Optional[GameContext]:
    """
    获取全局上下文（兼容性）
    
    用于迁移期间的兼容
    """
    return _global_context
```

---

## 第2天: Repository实现

### Player Repository抽象

**文件**: `domain/repositories/player_repository.py`

```python
"""
Player仓储接口

遵循Repository模式，抽象玩家数据访问
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


@dataclass
class PlayerEntity:
    """玩家领域实体"""
    player_name: str
    team_stamina: List[int]
    backpack_items: List[str]
    team_levels: List[int]
    skill_levels: List[int]
    reserve_troops: int
    player_type: str
    combat_preference: str
    current_stamina: int
    max_stamina: int
    vip_level: int
    stamina_items: List[Dict[str, Any]]


class PlayerRepository(ABC):
    """
    玩家数据仓储抽象
    
    定义玩家数据的访问契约，不依赖具体存储实现
    """
    
    @abstractmethod
    def get_by_name(self, player_name: str) -> Optional[PlayerEntity]:
        """根据名称获取玩家"""
        pass
    
    @abstractmethod
    def get_all_names(self) -> List[str]:
        """获取所有玩家名称"""
        pass
    
    @abstractmethod
    def save(self, player_name: str, entity: PlayerEntity) -> None:
        """保存玩家数据"""
        pass
    
    @abstractmethod
    def exists(self, player_name: str) -> bool:
        """检查玩家是否存在"""
        pass


class CommanderOrderRepository(ABC):
    """指挥官军令仓储抽象"""
    
    @abstractmethod
    def get_current_order(self) -> str:
        """获取当前总军令"""
        pass
    
    @abstractmethod
    def save_order(self, order: str) -> None:
        """保存军令"""
        pass
```

### 内存实现

**文件**: `infrastructure/repositories/memory_player_repository.py`

```python
"""
Player仓储内存实现

用于开发和测试
"""

from ...domain.repositories.player_repository import (
    PlayerRepository, PlayerEntity, CommanderOrderRepository
)
from typing import Optional, Dict, List


class InMemoryPlayerRepository(PlayerRepository):
    """
    内存实现
    
    数据在内存中存储，进程重启后丢失
    适合开发和测试环境
    """
    
    def __init__(self, initial_data: Optional[Dict[str, dict]] = None):
        self._storage: Dict[str, PlayerEntity] = {}
        if initial_data:
            for name, data in initial_data.items():
                self._storage[name] = self._dict_to_entity(data)
    
    def get_by_name(self, player_name: str) -> Optional[PlayerEntity]:
        return self._storage.get(player_name)
    
    def get_all_names(self) -> List[str]:
        return list(self._storage.keys())
    
    def save(self, player_name: str, entity: PlayerEntity) -> None:
        self._storage[player_name] = entity
    
    def exists(self, player_name: str) -> bool:
        return player_name in self._storage
    
    def _dict_to_entity(self, data: dict) -> PlayerEntity:
        """字典转实体"""
        return PlayerEntity(
            player_name=data.get("player_name", ""),
            team_stamina=data.get("team_stamina", [100, 100, 100, 100]),
            backpack_items=data.get("backpack_items", []),
            team_levels=data.get("team_levels", [1, 1, 1, 1]),
            skill_levels=data.get("skill_levels", [1, 1, 1, 1]),
            reserve_troops=data.get("reserve_troops", 0),
            player_type=data.get("player_type", "普通玩家"),
            combat_preference=data.get("combat_preference", "平稳作战"),
            current_stamina=data.get("current_stamina", 100),
            max_stamina=data.get("max_stamina", 100),
            vip_level=data.get("vip_level", 1),
            stamina_items=data.get("stamina_items", [])
        )


class InMemoryCommanderOrderRepository(CommanderOrderRepository):
    """军令内存仓储"""
    
    def __init__(self, default_order: str = ""):
        self._order = default_order or self._default_order()
    
    def get_current_order(self) -> str:
        return self._order
    
    def save_order(self, order: str) -> None:
        self._order = order
    
    def _default_order(self) -> str:
        return """事件：今天（9月15号）早上10点，听信件指挥进行攻城！
...
"""
```

---

## 第3天: System Bootstrap

**文件**: `core/bootstrap.py`

```python
"""
系统引导模块

负责系统初始化和依赖配置
"""

from .container import DIContainer, LifetimeScope
from .context import GameContext, SystemConfig
from ..domain.repositories.player_repository import (
    PlayerRepository, CommanderOrderRepository
)
from ..infrastructure.repositories.memory_player_repository import (
    InMemoryPlayerRepository, InMemoryCommanderOrderRepository
)


# 硬编码的初始玩家数据（从旧的context迁移）
DEFAULT_PLAYERS = {
    "龙傲天": {
        "player_name": "龙傲天",
        "team_stamina": [90, 120, 120, 120],
        "backpack_items": ["1个面包"],
        "team_levels": [50, 45, 40, 38],
        "skill_levels": [10, 8, 6, 1],
        "reserve_troops": 40000,
        "player_type": "高级玩家",
        "combat_preference": "主力攻城",
        "current_stamina": 90,
        "max_stamina": 120,
        "vip_level": 5,
        "stamina_items": [
            {"item_id": "stamina_potion_small", "name": "小体力药水", "count": 8, "recovery_amount": 20, "expire_time": "2024-12-25T23:59:59"},
            {"item_id": "stamina_potion_medium", "name": "中体力药水", "count": 3, "recovery_amount": 50, "expire_time": "2024-12-30T23:59:59"},
            {"item_id": "stamina_potion_large", "name": "大体力药水", "count": 2, "recovery_amount": 100, "expire_time": "2024-12-22T23:59:59"}
        ]
    },
    # ... 其他玩家数据
}


def create_production_container(
    config: SystemConfig = None,
    custom_model_client=None
) -> DIContainer:
    """
    创建生产环境容器
    
    Args:
        config: 系统配置
        custom_model_client: 可选的自定义模型客户端
        
    Returns:
        配置好的DI容器
    """
    container = DIContainer()
    config = config or SystemConfig()
    
    # 1. 注册配置
    container.register_instance(SystemConfig, config)
    
    # 2. 注册Repository
    if config.use_yaml_repository:
        # 可以扩展YAML实现
        raise NotImplementedError("YAML repository not implemented")
    else:
        # 使用内存实现
        container.register_instance(
            PlayerRepository,
            InMemoryPlayerRepository(DEFAULT_PLAYERS)
        )
        container.register_instance(
            CommanderOrderRepository,
            InMemoryCommanderOrderRepository()
        )
    
    # 3. 注册领域服务（注意: 需要先导入以避免导入循环）
    from ..monitoring.player_state import PlayerStateManager
    container.register_class(PlayerStateManager, lifetime=LifetimeScope.SINGLETON)
    
    # 4. 注册BehaviorMonitor（使用工厂以注入依赖）
    from ..monitoring.behavior_monitor import BehaviorMonitor
    container.register_factory(
        BehaviorMonitor,
        lambda c: BehaviorMonitor(
            threshold=c.resolve(SystemConfig).behavior_threshold,
            max_sequence_length=c.resolve(SystemConfig).max_sequence_length,
            player_state_manager=c.resolve(PlayerStateManager)
        ),
        lifetime=LifetimeScope.SINGLETON
    )
    
    # 5. 注册模型客户端（如果提供）
    if custom_model_client:
        container.register_instance('model_client', custom_model_client)
    
    # 6. 注册GameContext
    container.register_factory(
        GameContext,
        lambda c: GameContext(
            monitor=c.resolve(BehaviorMonitor),
            player_state_manager=c.resolve(PlayerStateManager),
            config=c.resolve(SystemConfig)
        ),
        lifetime=LifetimeScope.SINGLETON
    )
    
    return container


def create_test_container(**overrides) -> DIContainer:
    """
    创建测试容器
    
    使用Mock对象和简化配置
    
    Args:
        **overrides: 覆盖配置的参数
        
    Returns:
        测试用DI容器
    """
    config = SystemConfig(
        behavior_threshold=overrides.get('threshold', 2),
        auto_reset_after_intervention=False
    )
    
    container = DIContainer()
    container.register_instance(SystemConfig, config)
    
    # 空的测试数据
    container.register_instance(
        PlayerRepository,
        InMemoryPlayerRepository({"test_player": {}})
    )
    
    return container


def bootstrap_application(
    config: SystemConfig = None,
    custom_model_client = None
) -> DIContainer:
    """
    引导整个应用
    
    主入口点，创建并初始化所有组件
    
    使用示例:
    ```python
    from core.bootstrap import bootstrap_application
    
    container = bootstrap_application()
    context = container.resolve(GameContext)
    
    # 开始业务逻辑
    history = context.monitor.get_player_history("player_1")
    ```
    
    Args:
        config: 可选的系统配置
        custom_model_client: 可选的模型客户端
        
    Returns:
        完全配置的DI容器
    """
    config = config or SystemConfig()
    container = create_production_container(config, custom_model_client)
    
    # 设置兼容性全局上下文
    from .context import set_global_context
    set_global_context(container.resolve(GameContext))
    
    return container
```

---

## 第4天: 迁移策略

### 迁移检查清单

对于每个模块，按照以下步骤进行迁移：

#### ⬜ Module: `tools/emotion_tool.py`

**当前状态分析**:
- 使用 `from ..context import get_global_monitor, get_global_player_state_manager`
- 直接调用全局函数获取依赖

**迁移步骤**:
1. 修改函数签名接受 `monitor` 和 `player_state_manager` 参数
2. 创建包装版本用于向后兼容
3. 更新调用者传递依赖

**迁移后代码**:

```python
# tools/emotion_tool.py

def analyze_emotion_with_deps(
    player_id: str,
    *,
    monitor: 'BehaviorMonitor' = None,
    player_state_manager: 'PlayerStateManager' = None
) -> str:
    """
    分析玩家情绪状态
    
    Args:
        player_id: 玩家ID
        monitor: 可选的监控器实例（从DI容器传递）
        player_state_manager: 可选的状态管理器（从DI容器传递）
        
    Note:
        如果不传递monitor和player_state_manager，将使用全局回退（已废弃）
    """
    # 兼容性处理
    if monitor is None:
        from ..context import get_global_monitor
        monitor = get_global_monitor()
        
    if player_state_manager is None:
        from ..context import get_global_player_state_manager
        player_state_manager = get_global_player_state_manager()
    
    # 原有逻辑...
    behaviors = monitor.get_player_history(player_id)
    # ...
```

---

## 第5天: 验证测试

### 单元测试框架

**文件**: `tests/core/test_container.py`

```python
import pytest
from core.container import DIContainer, LifetimeScope

class TestDIContainer:
    """DI容器测试"""
    
    def test_register_and_resolve_singleton(self):
        """测试单例模式"""
        class Database:
            pass
        
        container = DIContainer()
        container.register_class(Database, lifetime=LifetimeScope.SINGLETON)
        
        db1 = container.resolve(Database)
        db2 = container.resolve(Database)
        
        assert db1 is db2, "单例应该返回相同实例"
    
    def test_register_and_resolve_transient(self):
        """测试瞬态模式"""
        class Service:
            pass
        
        container = DIContainer()
        container.register_class(Service, lifetime=LifetimeScope.TRANSIENT)
        
        s1 = container.resolve(Service)
        s2 = container.resolve(Service)
        
        assert s1 is not s2, "瞬态应该返回不同实例"
    
    def test_constructor_injection(self):
        """测试构造函数自动注入"""
        class Logger:
            pass
        
        class Service:
            def __init__(self, logger: Logger):
                self.logger = logger
        
        container = DIContainer()
        container.register_class(Logger)
        container.register_class(Service)
        
        service = container.resolve(Service)
        assert isinstance(service.logger, Logger)
    
    def test_factory_registration(self):
        """测试工厂函数注册"""
        class Config:
            def __init__(self, value: str):
                self.value = value
        
        container = DIContainer()
        container.register_factory(
            Config,
            lambda c: Config(value="test"),
            lifetime=LifetimeScope.SINGLETON
        )
        
        config = container.resolve(Config)
        assert config.value == "test"
    
    def test_circular_dependency_detection(self):
        """测试循环依赖检测"""
        class A:
            def __init__(self, b: 'B'):
                self.b = b
        
        class B:
            def __init__(self, a: A):
                self.a = a
        
        container = DIContainer()
        container.register_class(A)
        container.register_class(B)
        
        with pytest.raises(Exception) as exc_info:
            container.resolve(A)
        
        assert "circular" in str(exc_info.value).lower()
    
    def test_unregistered_dependency(self):
        """测试未注册依赖报错"""
        class Unknown:
            pass
        
        container = DIContainer()
        
        with pytest.raises(KeyError):
            container.resolve(Unknown)
```

### 集成测试

**文件**: `tests/integration/test_context.py`

```python
import pytest
from core.bootstrap import bootstrap_application
from core.context import GameContext, SystemConfig
from monitoring.behavior_monitor import BehaviorMonitor
from monitoring.player_state import PlayerStateManager

class TestBootstrap:
    """系统引导测试"""
    
    def test_bootstrap_creates_valid_container(self):
        """测试引导创建有效容器"""
        container = bootstrap_application()
        
        assert container.resolve(GameContext) is not None
        assert container.resolve(BehaviorMonitor) is not None
        assert container.resolve(PlayerStateManager) is not None
    
    def test_context_integration(self):
        """测试上下文集成"""
        container = bootstrap_application()
        context = container.resolve(GameContext)
        
        # 测试基本调用
        history = context.monitor.get_player_history("nonexistent_player")
        assert history == []
        
        # 测试玩家状态
        state = context.player_state_manager.get_player_state("test_player")
        assert state.player_id == "test_player"
    
    def test_player_context(self):
        """测试玩家上下文"""
        config = SystemConfig(initial_players={"player_1": {}})
        container = bootstrap_application(config=config)
        context = container.resolve(GameContext)
        
        player_ctx = context.for_player("player_1")
        assert player_ctx.player_id == "player_1"
```

---

## 验收标准

完成此迭代后，系统应满足：

1. ✅ DI Container正常工作，支持单例/瞬态/作用域生命周期
2. ✅ GameContext替代全局变量，显式传递依赖
3. ✅ 至少迁移3个核心工具函数使用新的依赖注入模式
4. ✅ 单元测试覆盖率达到80%+
5. ✅ Streamlit Dashboard能使用新容器正常运行

---

**文档结束**
