"""
Core模块 - 依赖注入和上下文管理

该模块提供:
- DIContainer: 轻量级依赖注入容器
- GameContext: 领域上下文对象
- SystemConfig: 系统配置
- bootstrap: 系统引导函数
"""

from .container import DIContainer, LifetimeScope, CircularDependencyError
from .context import GameContext, PlayerContext, SystemConfig, PlayerSnapshot
from .bootstrap import bootstrap_application, create_production_container, create_test_container

__all__ = [
    # 容器
    'DIContainer',
    'LifetimeScope',
    'CircularDependencyError',
    # 上下文
    'GameContext',
    'PlayerContext',
    'SystemConfig',
    'PlayerSnapshot',
    # 引导
    'bootstrap_application',
    'create_production_container',
    'create_test_container'
]
