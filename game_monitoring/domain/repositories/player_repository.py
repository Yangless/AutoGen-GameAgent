"""
Player存储库接口

遵循Repository模式，将数据访问逻辑从业务逻辑中解耦。

设计原则:
1. 仓储接口定义在Domain层，不依赖具体实现
2. Infrastructure层提供具体实现（内存、数据库等）
3. 使用依赖注入切换实现
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class PlayerEntity:
    """
    玩家领域实体

    这是领域层的核心实体，包含玩家的业务属性。

    注意: 这不是ORM实体，而是领域实体
    属性根据业务需求设计，可能不完全对应数据库表
    """
    player_name: str
    # 队伍和数据
    team_stamina: List[int] = field(default_factory=lambda: [100, 100, 100, 100])
    team_levels: List[int] = field(default_factory=lambda: [1, 1, 1, 1])
    skill_levels: List[int] = field(default_factory=lambda: [1, 1, 1, 1])
    # 道具
    backpack_items: List[str] = field(default_factory=list)
    stamina_items: List[Dict[str, Any]] = field(default_factory=list)
    # 资源
    reserve_troops: int = 0
    current_stamina: int = 100
    max_stamina: int = 100
    # 玩家分类
    player_type: str = "普通玩家"  # 高级/中级/初级
    combat_preference: str = "平稳作战"  # 主力攻城/支援作战
    vip_level: int = 1

    # 业务属性（非必需但常用）
    player_id: Optional[str] = None
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """实体创建后补充默认值"""
        if self.player_id is None:
            self.player_id = self.player_name.lower().replace(" ", "_")
        if self.created_at is None:
            self.created_at = datetime.now()


class PlayerRepository(ABC):
    """
    玩家数据存储抽象

    定义玩家数据的访问契约，不依赖具体存储技术。

    使用示例:
    ```python
    # 依赖接口，不关心具体实现
    def get_player_stamina(repo: PlayerRepository, name: str):
        player = repo.get_by_name(name)
        return player.team_stamina if player else [0, 0, 0, 0]

    # 调用时传入具体实现
    stamina = get_player_stamina(InMemoryPlayerRepository())
    ```
    """

    @abstractmethod
    def get_by_name(self, player_name: str) -> Optional[PlayerEntity]:
        """
        根据名称获取玩家

        Args:
            player_name: 玩家显示名称

        Returns:
            玩家实体或None
        """
        pass

    @abstractmethod
    def get_by_id(self, player_id: str) -> Optional[PlayerEntity]:
        """
        根据ID获取玩家

        Args:
            player_id: 玩家ID

        Returns:
            玩家实体或None
        """
        pass

    @abstractmethod
    def get_all_names(self) -> List[str]:
        """获取所有玩家名称列表"""
        pass

    @abstractmethod
    def get_all_ids(self) -> List[str]:
        """获取所有玩家ID列表"""
        pass

    @abstractmethod
    def save(self, entity: PlayerEntity) -> None:
        """
        保存玩家实体

        如果存在则更新，不存在则创建

        Args:
            entity: 玩家实体
        """
        pass

    @abstractmethod
    def delete(self, player_name: str) -> bool:
        """
        删除玩家

        Args:
            player_name: 玩家名称

        Returns:
            是否成功删除
        """
        pass

    @abstractmethod
    def exists(self, player_name: str) -> bool:
        """检查玩家是否存在"""
        pass

    def to_dict(self, entity: PlayerEntity) -> Dict[str, Any]:
        """实体转字典（帮助方法）"""
        return {
            'player_name': entity.player_name,
            'player_id': entity.player_id,
            'team_stamina': entity.team_stamina,
            'team_levels': entity.team_levels,
            'skill_levels': entity.skill_levels,
            'backpack_items': entity.backpack_items,
            'stamina_items': entity.stamina_items,
            'reserve_troops': entity.reserve_troops,
            'current_stamina': entity.current_stamina,
            'max_stamina': entity.max_stamina,
            'player_type': entity.player_type,
            'combat_preference': entity.combat_preference,
            'vip_level': entity.vip_level,
            'created_at': entity.created_at.isoformat() if entity.created_at else None
        }

    def from_dict(self, data: Dict[str, Any]) -> PlayerEntity:
        """字典转实体（帮助方法）"""
        created_at = None
        if data.get('created_at'):
            try:
                created_at = datetime.fromisoformat(data['created_at'])
            except ValueError:
                pass

        return PlayerEntity(
            player_name=data.get('player_name', ''),
            player_id=data.get('player_id'),
            team_stamina=data.get('team_stamina', [100, 100, 100, 100]),
            team_levels=data.get('team_levels', [1, 1, 1, 1]),
            skill_levels=data.get('skill_levels', [1, 1, 1, 1]),
            backpack_items=data.get('backpack_items', []),
            stamina_items=data.get('stamina_items', []),
            reserve_troops=data.get('reserve_troops', 0),
            current_stamina=data.get('current_stamina', 100),
            max_stamina=data.get('max_stamina', 100),
            player_type=data.get('player_type', '普通玩家'),
            combat_preference=data.get('combat_preference', '平稳作战'),
            vip_level=data.get('vip_level', 1),
            created_at=created_at
        )


class CommanderOrderRepository(ABC):
    """
    指挥官军令存储抽象

    管理游戏级别的公共命令配置
    """

    @abstractmethod
    def get_current_order(self) -> str:
        """获取当前总军令"""
        pass

    @abstractmethod
    def save_order(self, order: str) -> None:
        """保存军令"""
        pass

    @abstractmethod
    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取军令历史

        Args:
            limit: 返回条数

        Returns:
            军令历史列表，包含时间和内容
        """
        pass

    def append_log(self, note: str) -> None:
        """
        添加操作日志（可选）

        Args:
            note: 日志内容
        """
        pass
