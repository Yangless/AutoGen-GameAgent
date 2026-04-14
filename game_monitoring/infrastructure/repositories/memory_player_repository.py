"""
Player存储内存实现

用于开发和测试环境
"""

from typing import Optional, Dict, Any, List
from datetime import datetime

from ...domain.repositories.player_repository import (
    PlayerRepository, CommanderOrderRepository, PlayerEntity
)


class InMemoryPlayerRepository(PlayerRepository):
    """
    Player存储内存实现

    数据存储在内存中，进程重启后丢失。
    适合用于:
    1. 开发环境快速迭代
    2. 单元测试（避免IO）
    3. 演示和原型

    线程安全: 非线程安全，单线程使用

    使用示例:
    ```python
    repo = InMemoryPlayerRepository()

    # 保存
    repo.save(PlayerEntity("player_1", ...))

    # 读取
    player = repo.get_by_name("player_1")
    ```
    """

    def __init__(self, initial_data: Optional[Dict[str, dict]] = None):
        """
        创建内存仓储

        Args:
            initial_data: 可选的初始数据字典
        """
        self._storage: Dict[str, PlayerEntity] = {}
        self._id_to_name: Dict[str, str] = {}

        if initial_data:
            for name, data in initial_data.items():
                entity = self._dict_to_entity(data)
                self._storage[name] = entity
                self._id_to_name[entity.player_id] = name

    def get_by_name(self, player_name: str) -> Optional[PlayerEntity]:
        """根据名称获取玩家"""
        return self._storage.get(player_name)

    def get_by_id(self, player_id: str) -> Optional[PlayerEntity]:
        """根据ID获取玩家"""
        name = self._id_to_name.get(player_id)
        if name:
            return self._storage.get(name)
        return None

    def get_all_names(self) -> List[str]:
        """获取所有玩家名称"""
        return list(self._storage.keys())

    def get_all_ids(self) -> List[str]:
        """获取所有玩家ID"""
        return list(self._id_to_name.keys())

    def save(self, entity: PlayerEntity) -> None:
        """保存玩家实体"""
        self._storage[entity.player_name] = entity
        self._id_to_name[entity.player_id] = entity.player_name

    def delete(self, player_name: str) -> bool:
        """删除玩家"""
        entity = self._storage.pop(player_name, None)
        if entity:
            self._id_to_name.pop(entity.player_id, None)
            return True
        return False

    def exists(self, player_name: str) -> bool:
        """检查玩家是否存在"""
        return player_name in self._storage

    def _dict_to_entity(self, data: dict) -> PlayerEntity:
        """将原始数据字典转换为PlayerEntity"""
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

    def __repr__(self):
        return f"<InMemoryPlayerRepository players={len(self._storage)}>"


class InMemoryCommanderOrderRepository(CommanderOrderRepository):
    """
    指挥官军令内存存储

    使用示例:
    ```python
    repo = InMemoryCommanderOrderRepository()
    repo.save_order("今日攻城...")
    order = repo.get_current_order()
    ```
    """

    DEFAULT_ORDER = """事件：今天（9月15号）早上10点，听信件指挥进行攻城！

配置：请每人至少派出4支部队，第1队主力需要能打12级地，第2队需要能打11级地，第3队需要能打8级地，第4队需要能打6级地；能打12级直接去前线（752，613），注意兵种克属，派遣过去并驻守城池xx，城池最大可募兵三万，队伍重伤后可原地花费铜币募兵，不要回去，加油守住这个城池。能打11级的队伍如果是国家队伍的话，也可以酌情考虑派往前线，若非国家队，提前派遣部队至将军雕像（732，767），不列颠文明的队伍到城池附近，提前转化为器械部队；需提醒一下在打城前将派遣的队伍进行再次分类，为精锐攻城，和拆耐久部分；其余队伍作为攻城拆迁队，在主力将城池精锐部队耗完后，发起攻城，拆除城池耐久。

介绍：集结等建好后发起，将军雕像S（已建成）使用【集结】或【派遣】进行快速行军前往，目不消耗体力和十气。"""

    def __init__(self, default_order: str = None):
        self._history: List[Dict[str, Any]] = []
        if default_order:
            self.save_order(default_order)
        else:
            # 预填充默认军令
            self._history.append({
                'order': self.DEFAULT_ORDER,
                'timestamp': datetime.now(),
                'note': '初始化默认军令'
            })

    def get_current_order(self) -> str:
        """获取当前军令"""
        if self._history:
            return self._history[-1]['order']
        return ""

    def save_order(self, order: str, note: str = "") -> None:
        """保存军令"""
        self._history.append({
            'order': order,
            'timestamp': datetime.now(),
            'note': note
        })

    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取军令历史"""
        return self._history[-limit:]

    def append_log(self, note: str) -> None:
        """添加操作日志"""
        if self._history:
            last = self._history[-1]
            logs = last.get('logs', [])
            logs.append({
                'note': note,
                'timestamp': datetime.now()
            })
            last['logs'] = logs
