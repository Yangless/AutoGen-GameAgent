"""
系统引导模块

职责:
- 初始化DI容器
- 注册所有服务
- 设置兼容性全局上下文

这是应用程序的入口点。
"""

from typing import Optional, Any
import os
import sys

# 确保项目根目录在路径中
if __package__ is not None:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .container import DIContainer, LifetimeScope
from .context import GameContext, SystemConfig, set_global_context
from ..domain.repositories.player_repository import PlayerRepository, CommanderOrderRepository
from ..domain.schemas import EmotionWorkerOutput
from ..infrastructure.memory.memory_service import MemoryService
from ..infrastructure.repositories.memory_player_repository import (
    InMemoryPlayerRepository, InMemoryCommanderOrderRepository
)
from ..infrastructure.validation.output_validator import OutputValidator
from ..agents.orchestrator import OrchestratorAgent
from autogen_core import SingleThreadedAgentRuntime


# 默认玩家数据（从旧代码迁移）
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
    "叶良辰": {
        "player_name": "叶良辰",
        "team_stamina": [30, 30, 30, 90],
        "backpack_items": ["1个大面包", "2个辎重箱"],
        "team_levels": [45, 40, 30, 25],
        "skill_levels": [10, 8, 6, 1],
        "reserve_troops": 50000,
        "player_type": "中级玩家",
        "combat_preference": "支援作战",
        "current_stamina": 30,
        "max_stamina": 100,
        "vip_level": 3,
        "stamina_items": [
            {"item_id": "stamina_potion_small", "name": "小体力药水", "count": 5, "recovery_amount": 20, "expire_time": "2024-12-28T23:59:59"},
            {"item_id": "energy_drink", "name": "能量饮料", "count": 1, "recovery_amount": 80, "expire_time": "2024-12-21T23:59:59"}
        ]
    },
    "孤独的凤凰战士": {
        "player_name": "孤独的凤凰战士",
        "team_stamina": [25, 60, 90, 90],
        "backpack_items": ["1个小面包", "1个大面包"],
        "team_levels": [30, 25, 20, 10],
        "skill_levels": [6, 4, 2, 1],
        "reserve_troops": 10000,
        "player_type": "初级玩家",
        "combat_preference": "支援作战",
        "current_stamina": 10,
        "max_stamina": 80,
        "vip_level": 1,
        "stamina_items": [
            {"item_id": "stamina_potion_small", "name": "小体力药水", "count": 2, "recovery_amount": 20, "expire_time": "2024-12-26T23:59:59"},
            {"item_id": "stamina_potion_medium", "name": "中体力药水", "count": 1, "recovery_amount": 50, "expire_time": "2024-12-23T23:59:59"}
        ]
    }
}


def create_production_container(
    config: Optional[SystemConfig] = None,
    custom_model_client: Any = None
) -> DIContainer:
    """
    创建生产环境容器

    注册所有核心服务:
    1. 配置
    2. Repository层
    3. Monitoring层
    4. Context层

    Args:
        config: 可选的系统配置
        custom_model_client: 可选的模型客户端

    Returns:
        配置好的DI容器
    """
    container = DIContainer()
    config = config or SystemConfig()

    # 1. 注册配置
    container.register_instance(SystemConfig, config)

    # 2. 注册Repository
    # 根据配置选择实现
    if config.use_yaml_repository:
        # TODO: 实现YAML存储
        raise NotImplementedError("YAML repository not implemented yet")
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

    # 3. 注册领域服务
    # PlayerStateManager - 单例
    from ..monitoring.player_state import PlayerStateManager
    container.register_class(
        PlayerStateManager,
        lifetime=LifetimeScope.SINGLETON
    )

    # BehaviorMonitor - 单例
    from ..monitoring.behavior_monitor import BehaviorMonitor
    container.register_factory(
        'BehaviorMonitorType',
        lambda c: BehaviorMonitor(
            threshold=c.resolve(SystemConfig).behavior_threshold,
            max_sequence_length=c.resolve(SystemConfig).max_sequence_length,
            recent_actions_window=c.resolve(SystemConfig).recent_actions_window
        ),
        lifetime=LifetimeScope.SINGLETON
    )

    # 4. 注册GameContext
    def create_game_context(c: DIContainer) -> GameContext:
        """创建GameContext工厂"""
        monitor = c.resolve('BehaviorMonitorType')
        state_manager = c.resolve(PlayerStateManager)
        cfg = c.resolve(SystemConfig)
        return GameContext(
            monitor=monitor,
            player_state_manager=state_manager,
            config=cfg
        )

    container.register_factory(
        GameContext,
        create_game_context,
        lifetime=LifetimeScope.SINGLETON
    )

    # 5. 注册Application Services
    from ..application.services.action_service import ActionProcessingService
    from ..application.services.agent_service import AgentService

    container.register_factory(
        ActionProcessingService,
        lambda c: ActionProcessingService(c.resolve(GameContext)),
        lifetime=LifetimeScope.SCOPED
    )

    container.register_factory(
        AgentService,
        lambda c: AgentService(c.resolve(GameContext)),
        lifetime=LifetimeScope.SCOPED
    )

    # 6. 注册模型客户端（如果提供）
    if custom_model_client:
        container.register_instance('model_client', custom_model_client)

    # 7. 注册AutoGen Core Runtime和Orchestrator
    container.register_factory(
        SingleThreadedAgentRuntime,
        lambda c: SingleThreadedAgentRuntime(),
        lifetime=LifetimeScope.SINGLETON
    )

    container.register_factory(
        'OrchestratorAgent',
        lambda c: OrchestratorAgent(
            model_client=custom_model_client,
            worker_types=['emotion_worker', 'churn_worker', 'behavior_worker']
        ),
        lifetime=LifetimeScope.SINGLETON
    )

    container.register_factory(
        MemoryService,
        lambda c: MemoryService(
            redis_url=getattr(c.resolve(SystemConfig), 'redis_url', "redis://localhost:6379")
        ),
        lifetime=LifetimeScope.SINGLETON
    )

    container.register_factory(
        'OutputValidator',
        lambda c: OutputValidator(EmotionWorkerOutput, max_retries=3),
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
    container.register_instance(
        CommanderOrderRepository,
        InMemoryCommanderOrderRepository("test order")
    )

    # PlayerStateManager
    from ..monitoring.player_state import PlayerStateManager
    container.register_class(
        PlayerStateManager,
        lifetime=LifetimeScope.SINGLETON
    )

    return container


def bootstrap_application(
    config: Optional[SystemConfig] = None,
    custom_model_client: Any = None,
    setup_global_context: bool = True
) -> DIContainer:
    """
    引导整个应用

    主入口点，创建并初始化所有组件

    使用示例:
    ```python
    from core.bootstrap import bootstrap_application

    container = bootstrap_application()
    context = container.resolve(GameContext)

    # 开始使用
    monitor = context.monitor
    ```

    Args:
        config: 可选的系统配置
        custom_model_client: 可选的模型客户端
        setup_global_context: 是否设置全局上下文（兼容性）

    Returns:
        完全配置的DI容器
    """
    config = config or SystemConfig()

    # 创建容器
    container = create_production_container(config, custom_model_client)

    # 设置兼容性全局上下文
    if setup_global_context:
        context = container.resolve(GameContext)
        set_global_context(context)

    return container


def bootstrap_for_streamlit(
    threshold: int = 3,
    max_sequence_length: int = 50,
    recent_actions_window: int = 3,
    **streamlit_kwargs
) -> DIContainer:
    """
    Streamlit专用的引导函数

    预设适合Streamlit应用的配置

    Args:
        threshold: 负面行为阈值
        max_sequence_length: 最大序列长度
        recent_actions_window: 最近行为窗口
        **streamlit_kwargs: 其他参数

    Returns:
        配置的DI容器
    """
    config = SystemConfig(
        behavior_threshold=threshold,
        max_sequence_length=max_sequence_length,
        recent_actions_window=recent_actions_window,
        auto_reset_after_intervention=streamlit_kwargs.get('auto_reset', False)
    )

    return bootstrap_application(config)
