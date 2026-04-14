"""
Domain层 - 领域模型和业务规则

该层包含:
- 领域实体和值对象
- 仓储接口（Repository接口）
- 领域服务接口

原则:
1. 不依赖任何外部框架
2. 不依赖基础设施层
3. 使用Python dataclasses定义实体
"""

from .repositories.player_repository import (
    PlayerRepository,
    CommanderOrderRepository,
    PlayerEntity
)

__all__ = [
    'PlayerRepository',
    'CommanderOrderRepository',
    'PlayerEntity'
]
