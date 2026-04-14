# 迭代3: UI与业务分离

## 概述
本迭代将 Streamlit Dashboard 与业务逻辑分离，实现清晰的关注点分离。

---

## 第1天: 分析现有UI

### 当前问题分析

查看 `streamlit_dashboard.py` (720行) 的职责混合：

```python
# 问题1: 业务逻辑与UI混在一起
async def process_atomic_action(player_id: str, action_name: str):
    """140行的混合函数"""
    # ... UI日志记录
    add_agent_log(f"🎯 执行动作: {action_name}")
    
    # ... 规则引擎调用
    triggered_scenarios = monitor.add_atomic_action(player_id, action_name)
    
    # ... 情绪分析
    final_emotion_type = "neutral"
    if triggered_scenarios:
        sequence_emotion = monitor.rule_engine.get_emotion_type_from_scenarios(triggered_scenarios)
    
    # ... 阈值检查
    if current_count >= monitor.threshold:
        await _trigger_async_intervention(system, player_id)
    
    # ... 更多UI更新
    add_agent_log(f"📊 状态更新完成...")

# 问题2: 全局状态直接访问
monitor = st.session_state.monitor
player_state_manager = st.session_state.player_state_manager

# 问题3: 大量的内联样式和布局
st.markdown("...")  # CSS样式
st.columns([1, 2, 1])  # 布局

# 问题4: 异步处理嵌套
async def _trigger_async_intervention(system, player_id: str):
    # 复杂的线程和流处理
    def run_intervention(capture_obj):
        sys.stdout = capture_obj
        loop = asyncio.new_event_loop()
        ...
```

### 目标架构

```
ui/
├── adapters/              # Streamlit适配层
│   ├── __init__.py
│   ├── streamlit_adapter.py
│   └── async_utils.py
├── components/            # 可复用组件
│   ├── __init__.py
│   ├── player_status_panel.py
│   ├── action_grid.py
│   ├── agent_logs.py
│   └── military_order_panel.py
├── layouts/               # 页面布局
│   ├── __init__.py
│   └── dashboard_layout.py
├── pages/                 # 页面定义
│   ├── __init__.py
│   └── main_dashboard.py
└── presenters/            # 展示层
    ├── __init__.py
    └── player_presenter.py

application/
├── services/              # 应用服务
│   ├── __init__.py
│   ├── action_service.py
│   └── agent_service.py
└── usecases/              # 用例编排
    ├── __init__.py
    └── process_player_action.py
```

---

## 第2天: 应用服务层

### Action Service

**文件**: `application/services/action_service.py`

```python
"""
动作处理应用服务

职责:
- 处理玩家动作的核心业务逻辑
- 协调规则引擎和状态管理
- 决定是否需要干预
- 无UI依赖，纯业务逻辑
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum, auto
from datetime import datetime

from ...core.context import PlayerContext, GameContext
from ...rules import RuleEngine, RuleResult


class ActionResult(Enum):
    SUCCESS = auto()           # 正常记录
    RULE_TRIGGERED = auto()    # 触发了规则
    INTERVENTION_TRIGGERED = auto()  # 触发了干预
    ERROR = auto()             # 错误


@dataclass
class ActionProcessingResult:
    """动作处理结果"""
    result: ActionResult
    player_id: str
    action_name: str
    message: str
    triggered_rules: List[RuleResult] = field(default_factory=list)
    should_intervene: bool = False
    current_negative_count: int = 0
    threshold: int = 3
    emotion_type: str = "neutral"
    action_sequence_length: int = 0


class ActionProcessingService:
    """
    动作处理服务
    
    核心协调器，负责:
    1. 记录动作到监控器
    2. 执行规则引擎分析
    3. 更新负面对象计数
    4. 判断干预条件
    
    使用示例:
    ```python
    service = ActionProcessingService(game_context)
    result = await service.process_action("player_1", "click_exit")
    
    if result.should_intervene:
        await agent_service.trigger_intervention(result.player_id)
    ```
    """
    
    def __init__(self, game_context: GameContext):
        self._context = game_context
        self._monitor = game_context.monitor
        self._negative_counts: Dict[str, int] = {}
    
    async def process_action(
        self,
        player_id: str,
        action_name: str,
        action_params: Dict[str, Any] = None
    ) -> ActionProcessingResult:
        """
        处理玩家动作
        
        Args:
            player_id: 玩家ID
            action_name: 动作名称
            action_params: 可选参数
            
        Returns:
            处理结果，包含是否触发干预的标记
        """
        try:
            # 1. 添加到监控器并获取触发规则
            triggered = self._monitor.add_atomic_action(
                player_id, action_name, action_params
            )
            
            # 2. 获取情绪类型
            emotion_type = "neutral"
            if triggered:
                emotion_type = self._get_emotion_from_rules(triggered)
            
            # 3. 更新负面计数
            should_intervene = False
            if emotion_type == "negative":
                current_count = self._increment_negative_count(player_id)
                should_intervene = current_count >= self._monitor.threshold
            else:
                current_count = self._get_negative_count(player_id)
            
            # 4. 获取序列长度
            sequence = self._monitor.get_player_action_sequence(player_id)
            
            return ActionProcessingResult(
                result=ActionResult.INTERVENTION_TRIGGERED if should_intervene else ActionResult.RULE_TRIGGERED if triggered else ActionResult.SUCCESS,
                player_id=player_id,
                action_name=action_name,
                message="处理完成",
                triggered_rules=[type('obj', (), r) for r in triggered],
                should_intervene=should_intervene,
                current_negative_count=current_count,
                threshold=self._monitor.threshold,
                emotion_type=emotion_type,
                action_sequence_length=len(sequence)
            )
            
        except Exception as e:
            return ActionProcessingResult(
                result=ActionResult.ERROR,
                player_id=player_id,
                action_name=action_name,
                message=f"错误: {str(e)}",
                triggered_rules=[],
                should_intervene=False
            )
    
    def _get_emotion_from_rules(self, rules: List[Dict]) -> str:
        """从规则结果推断情绪"""
        # 检查是否有高度消极场景
        for rule in rules:
            scenario = rule.get('scenario', '')
            if any(kw in scenario for kw in ['失败', '风险', '退出', '攻击']):
                return "negative"
            if any(kw in scenario for kw in ['充值', '胜利', '成就']):
                return "positive"
            if '机器人' in scenario or '高频' in scenario:
                return "abnormal"
        return "neutral"
    
    def _increment_negative_count(self, player_id: str) -> int:
        """增加负面计数"""
        self._negative_counts[player_id] = self._negative_counts.get(player_id, 0) + 1
        return self._negative_counts[player_id]
    
    def _get_negative_count(self, player_id: str) -> int:
        """获取当前负面计数"""
        return self._negative_counts.get(player_id, 0)
    
    def reset_negative_count(self, player_id: str) -> None:
        """重置负面计数"""
        self._negative_counts[player_id] = 0
    
    def get_info(self, player_id: str) -> Dict[str, Any]:
        """获取玩家处理信息"""
        return {
            'player_id': player_id,
            'negative_count': self._get_negative_count(player_id),
            'threshold': self._monitor.threshold,
            'sequence_length': len(self._monitor.get_player_action_sequence(player_id))
        }
```

### Agent Service

**文件**: `application/services/agent_service.py`

```python
"""
Agent服务

职责:
- 协调Agent调用
- 处理异步执行
- 管理日志捕获
"""

import asyncio
import threading
from typing import Optional, Callable
from dataclasses import dataclass
from datetime import datetime

from ...team.team_manager import GameMonitoringTeam
from ...core.context import GameContext


@dataclass
class InterventionResult:
    """干预结果"""
    player_id: str
    success: bool
    message: str
    logs: list = None
    timestamp: datetime = None


class AgentService:
    """
    Agent服务
    
    封装Agent调用的复杂性
    """
    
    def __init__(
        self,
        game_context: GameContext,
        team_factory: Callable[[], GameMonitoringTeam] = None,
        log_capture: 'LogCapture' = None
    ):
        self._context = game_context
        self._team_factory = team_factory
        self._log_capture = log_capture
    
    async def trigger_intervention(
        self,
        player_id: str,
        on_log: Callable[[str], None] = None
    ) -> InterventionResult:
        """
        触发Agent干预
        
        Args:
            player_id: 玩家ID
            on_log: 日志回调函数
            
        Returns:
            干预结果
        """
        try:
            if self._team_factory:
                team = self._team_factory()
            else:
                # 从全局获取（兼容）
                from ...context import get_global_monitor
                monitor = get_global_monitor()
                # TODO: 从容器获取team
                team = None
            
            if not team:
                return InterventionResult(
                    player_id=player_id,
                    success=False,
                    message="Team未初始化",
                    logs=[],
                    timestamp=datetime.now()
                )
            
            # 启动后台线程执行
            logs = []
            
            def run_team():
                """在后台线程中运行"""
                
            # 简化版本：直接调用
            await team.trigger_analysis_and_intervention(
                player_id,
                self._context.monitor
            )
            
            return InterventionResult(
                player_id=player_id,
                success=True,
                message="干预已触发",
                logs=logs,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            return InterventionResult(
                player_id=player_id,
                success=False,
                message=str(e),
                timestamp=datetime.now()
            )
    
    async def generate_military_order(
        self,
        player_name: str,
        commander_order: str
    ) -> str:
        """生成军令"""
        # TODO: 实现军令生成
        return "军令内容"
```

---

## 第3天: 适配器层

### Streamlit Session State Adapter

**文件**: `ui/adapters/streamlit_adapter.py`

```python
"""
Streamlit适配层

将Streamlit的session_state适配为通用接口
"""

from typing import TypeVar, Generic, Optional, Any, List

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    st = None

T = TypeVar('T')


class SessionStateAdapter:
    """
    Session State 适配器
    
    抽象Streamlit特定的session_state操作
    便于测试和将来迁移
    """
    
    def __init__(self, prefix: str = ""):
        self._prefix = prefix
        self._fallback_storage = {} if not STREAMLIT_AVAILABLE else None
    
    def _full_key(self, key: str) -> str:
        """生成完整键名"""
        return f"{self._prefix}{key}"
    
    def get(self, key: str, default: T = None) -> T:
        """获取值"""
        if not STREAMLIT_AVAILABLE:
            return self._fallback_storage.get(self._full_key(key), default)
        return st.session_state.get(self._full_key(key), default)
    
    def set(self, key: str, value: T) -> None:
        """设置值"""
        if not STREAMLIT_AVAILABLE:
            self._fallback_storage[self._full_key(key)] = value
            return
        st.session_state[self._full_key(key)] = value
    
    def has(self, key: str) -> bool:
        """检查是否存在"""
        if not STREAMLIT_AVAILABLE:
            return self._full_key(key) in self._fallback_storage
        return self._full_key(key) in st.session_state
    
    def append_to_list(
        self,
        key: str,
        value: T,
        max_size: int = None
    ) -> List[T]:
        """
        追加到列表
        
        Args:
            key: 列表键名
            value: 要追加的值
            max_size: 最大长度，超过则从头部截断
            
        Returns:
            更新后的列表
        """
        lst = self.get(key, [])
        if lst is None:
            lst = []
        lst = lst.copy()  # 创建副本避免修改
        lst.append(value)
        
        if max_size and len(lst) > max_size:
            lst = lst[-max_size:]
        
        self.set(key, lst)
        return lst
    
    def increment(self, key: str, default: int = 0) -> int:
        """自增计数器"""
        current = self.get(key, default)
        new_value = current + 1
        self.set(key, new_value)
        return new_value
    
    def clear(self, key: str) -> None:
        """清空值"""
        if self.has(key):
            if not STREAMLIT_AVAILABLE:
                del self._fallback_storage[self._full_key(key)]
            else:
                del st.session_state[self._full_key(key)]


class LogAdapter:
    """日志适配器"""
    
    def __init__(
        self,
        state_adapter: SessionStateAdapter,
        log_key: str = "behavior_logs",
        max_logs: int = 100
    ):
        self._state = state_adapter
        self._log_key = log_key
        self._max_logs = max_logs
    
    def log(self, message: str) -> None:
        """添加日志"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self._state.append_to_list(self._log_key, log_entry, self._max_logs)
    
    def get_logs(self, count: int = None) -> List[str]:
        """获取日志"""
        logs = self._state.get(self._log_key, [])
        if count:
            return logs[-count:]
        return logs
    
    def clear(self) -> None:
        """清空日志"""
        self._state.set(self._log_key, [])


# 便捷函数
def create_state_adapter(prefix: str = "game_") -> SessionStateAdapter:
    """创建状态适配器"""
    return SessionStateAdapter(prefix)


def create_log_adapter(
    prefix: str = "",
    log_key: str = "logs"
) -> LogAdapter:
    """创建日志适配器"""
    return LogAdapter(create_state_adapter(prefix), log_key)
```

### Async Utilities

**文件**: `ui/adapters/async_utils.py`

```python
"""
异步工具

处理Streamlit中的异步执行
"""

import asyncio
import threading
from typing import Callable, Any
from functools import wraps


def run_in_thread(
    async_func: Callable,
    *args,
    daemon: bool = True,
    on_complete: Callable = None,
    on_error: Callable = None
) -> threading.Thread:
    """
    在后台线程中运行异步函数
    
    Args:
        async_func: 异步函数
        args: 函数参数
        daemon: 是否守护线程
        on_complete: 完成回调
        on_error: 错误回调
        
    Returns:
        线程对象
    """
    def target():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(async_func(*args))
            loop.close()
            
            if on_complete:
                on_complete(result)
        except Exception as e:
            if on_error:
                on_error(e)
    
    thread = threading.Thread(target=target, daemon=daemon)
    thread.start()
    return thread


def st_async(func: Callable) -> Callable:
    """
    Streamlit异步装饰器
    
    将异步函数包装为同步调用
    
    使用示例:
    ```python
    @st_async
    async def process_action(action_name: str):
        result = await service.process(action_name)
        return result
    
    # 在Streamlit中
    if st.button("执行"):
        result = process_action("click_exit")
    ```
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(func(*args, **kwargs))
    return wrapper


class AsyncActionHandler:
    """
    异步动作处理器
    
    封装异步操作的状态管理和回调
    """
    
    def __init__(self):
        self._pending = {}
        self._results = {}
    
    async def execute(
        self,
        action_id: str,
        async_func: Callable,
        *args
    ) -> Any:
        """执行异步操作"""
        self._pending[action_id] = True
        
        try:
            result = await async_func(*args)
            self._results[action_id] = {'success': True, 'data': result}
            return result
        except Exception as e:
            self._results[action_id] = {'success': False, 'error': str(e)}
            raise
        finally:
            del self._pending[action_id]
    
    def is_pending(self, action_id: str) -> bool:
        """检查是否进行中"""
        return action_id in self._pending
    
    def get_result(self, action_id: str) -> dict:
        """获取结果"""
        return self._results.get(action_id)
```

---

## 第4天: 组件层

### Player Status Panel Component

**文件**: `ui/components/player_status_panel.py`

```python
"""
玩家状态面板组件

纯UI组件，无业务逻辑
"""

import streamlit as st
from typing import Protocol


class PlayerStateView(Protocol):
    """Player状态展示协议"""
    
    def get_player_id(self) -> str: ...
    def get_player_name(self) -> str: ...
    def get_team_stamina(self) -> list: ...
    def get_emotion(self) -> str: ...
    def get_emotion_confidence(self) -> float: ...
    def get_churn_risk_level(self) -> str: ...
    def get_churn_risk_score(self) -> float: ...
    def get_bot_status(self) -> tuple: ...  # (is_bot, confidence)
    def get_last_updated(self) -> str: ...


class PlayerStatusPanel:
    """
    玩家状态面板
    
    职责：展示玩家当前状态信息
    
    使用示例:
    ```python
    view = PlayerStatusViewImpl(player_state)
    panel = PlayerStatusPanel(view)
    panel.render()
    ```
    """
    
    def __init__(self, view: PlayerStateView):
        self._view = view
    
    def render(self):
        """渲染面板"""
        st.markdown(
            '<h2 class="section-header">玩家状态</h2>',
            unsafe_allow_html=True
        )
        
        # 基本信息
        st.markdown(
            f'<div class="player-info">'
            f'<strong>玩家:</strong> {self._view.get_player_name()} '
            f'({self._view.get_player_id()})</div>',
            unsafe_allow_html=True
        )
        
        # 体力
        st.subheader("⚡ 队伍体力")
        stamina = self._view.get_team_stamina()
        cols = st.columns(4)
        for i, (col, val) in enumerate(zip(cols, stamina[:4])):
            col.metric(f"队伍{i+1}", f"{val}%")
        
        # 情绪
        st.subheader("😊 情绪状态")
        emotion = self._view.get_emotion()
        confidence = self._view.get_emotion_confidence()
        st.metric("当前情绪", emotion, f"置信度: {confidence:.0%}")
        
        # 流失风险
        st.subheader("⚠️ 流失风险")
        risk_level = self._view.get_churn_risk_level()
        risk_score = self._view.get_churn_risk_score()
        st.metric("风险等级", risk_level, f"风险分数: {risk_score:.2f}")
        
        # 机器人
        st.subheader("🤖 机器人检测")
        is_bot, confidence = self._view.get_bot_status()
        st.metric("是否机器人", "是" if is_bot else "否", f"置信度: {confidence:.0%}")


class PlayerStatusPanelCompact:
    """紧凑版玩家状态面板（用于侧栏）"""
    
    def __init__(self, view: PlayerStateView):
        self._view = view
    
    def render(self):
        """渲染紧凑面板"""
        st.subheader(f"👤 {self._view.get_player_name()}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("情绪", self._view.get_emotion())
        with col2:
            st.metric("风险", self._view.get_churn_risk_level())
```

### Action Grid Component

**文件**: `ui/components/action_grid.py`

```python
"""
动作网格组件

36个原子动作的网格布局
"""

import streamlit as st
from typing import Callable, List, Tuple
from dataclasses import dataclass


@dataclass
class ActionCategory:
    """动作分类"""
    title: str
    icon: str
    actions: List[Tuple[str, str]]  # (action_name, display_name)


class ActionGridComponent:
    """
    动作网格组件
    
    展示分类的原子动作按钮
    """
    
    ACTION_NAME_MAPPING = {
        # 核心游戏
        "login": "登录游戏",
        "logout": "退出登录",
        "enter_dungeon": "进入副本",
        "complete_dungeon": "完成副本",
        "move_city": "迁移城市",
        "attack_city": "攻击城市",
        "be_attacked": "被攻击",
        "win_pvp": "PVP获胜",
        "lose_pvp": "PVP失败",
        "occupy_land": "占领土地",
        "attack_npc_tribe": "攻击蛮族",
        "recruit_hero": "招募英雄",
        "upgrade_building": "升级建筑",
        "upgrade_skill": "升级技能",
        "enhance_equipment": "强化装备",
        "dismantle_equipment": "分解装备",
        "unlock_achievement": "解锁成就",
        "unlock_map": "解锁地图",
        "stamina_exhausted": "体力耗尽",
        "attempt_enter_dungeon_no_stamina": "无体力进副本",
        # 社交
        "join_family": "加入家族",
        "leave_family": "离开家族",
        "join_nation": "加入国家",
        "send_chat_message": "发送聊天",
        "receive_chat_message": "接收聊天",
        "add_friend": "添加好友",
        "remove_friend": "删除好友",
        "receive_praise": "收到赞美",
        "be_invited_to_family": "被邀请入族",
        # 经济
        "navigate_to_payment_page": "跳转充值页",
        "make_payment": "进行充值",
        "buy_monthly_card": "购买月卡",
        "cancel_auto_renew": "取消自动续费",
        "receive_daily_reward": "领取日常奖励",
        "receive_event_reward": "领取活动奖励",
        "sell_item": "出售物品",
        "clear_backpack": "清理背包",
        "post_account_for_sale": "发布账号出售",
        # 元数据
        "submit_review": "提交评价",
        "contact_support": "联系客服",
        "change_nickname": "修改昵称",
        "click_exit_game_button": "点击退出按钮",
        "uninstall_game": "卸载游戏",
    }
    
    CATEGORIES: List[ActionCategory] = [
        ActionCategory(
            "核心游戏动作",
            "🎮",
            [
                ("login", "登录"),
                ("logout", "退出"),
                ("enter_dungeon", "进副本"),
                ("complete_dungeon", "完成副本"),
                ("attack_city", "攻城"),
                ("be_attacked", "被攻击"),
                ("win_pvp", "PVP胜"),
                ("lose_pvp", "PVP败"),
                ("recruit_hero", "招募"),
                ("stamina_exhausted", "体力耗尽"),
                ("attempt_enter_dungeon_no_stamina", "无体力"),
                ("dismantle_equipment", "分解装备"),
            ]
        ),
        ActionCategory(
            "社交动作",
            "👥",
            [
                ("join_family", "入家族"),
                ("leave_family", "退家族"),
                ("add_friend", "加好友"),
                ("remove_friend", "删好友"),
                ("send_chat_message", "发消息"),
                ("receive_praise", "被赞美"),
            ]
        ),
        ActionCategory(
            "经济动作",
            "💰",
            [
                ("navigate_to_payment_page", "去充值"),
                ("make_payment", "充值"),
                ("buy_monthly_card", "买月卡"),
                ("cancel_auto_renew", "取消续费"),
                ("sell_item", "卖物品"),
                ("clear_backpack", "清背包"),
                ("post_account_for_sale", "卖账号"),
            ]
        ),
        ActionCategory(
            "元数据",
            "📋",
            [
                ("contact_support", "联系客服"),
                ("submit_review", "评价"),
                ("click_exit_game_button", "点退出"),
                ("uninstall_game", "卸载"),
            ]
        ),
    ]
    
    def __init__(
        self,
        on_action_click: Callable[[str], None],
        columns: int = 3
    ):
        self._on_click = on_action_click
        self._columns = columns
    
    def render(self):
        """渲染网格"""
        for category in self.CATEGORIES:
            self._render_category(category)
    
    def _render_category(self, category: ActionCategory):
        """渲染分类"""
        st.markdown(f"### {category.icon} {category.title}")
        
        rows = (len(category.actions) + self._columns - 1) // self._columns
        
        for row in range(rows):
            cols = st.columns(self._columns)
            for col_idx, col in enumerate(cols):
                action_idx = row * self._columns + col_idx
                if action_idx >= len(category.actions):
                    break
                
                action_name, display_name = category.actions[action_idx]
                
                with col:
                    if st.button(
                        display_name,
                        key=f"action_{action_name}",
                        help=f"执行: {action_name}",
                        use_container_width=True
                    ):
                        self._on_click(action_name)


class ActionGridCompact(ActionGridComponent):
    """紧凑版动作网格"""
    
    CATEGORIES = [
        ActionCategory(
            "常用",
            "⭐",
            [
                ("login", "登录"),
                ("enter_dungeon", "副本"),
                ("stamina_exhausted", "体力耗尽"),
                ("sell_item", "卖物品"),
                ("click_exit_game_button", "退出"),
            ]
        ),
    ]
```

---

## 第5天: 验证和迁移

### 迁移检查清单

从 `streamlit_dashboard.py` 迁移：

#### ✅ 核心数据处理
- [ ] `process_atomic_action` -> `ActionProcessingService.process_action`
- [ ] `_trigger_async_intervention` -> `AgentService.trigger_intervention`
- [ ] `add_behavior_log` -> `LogAdapter.log`

#### ✅ UI组件
- [ ] 玩家状态面板 -> `PlayerStatusPanel`
- [ ] 动作网格 -> `ActionGridComponent`
- [ ] 日志显示 -> 通用日志组件
- [ ] 军令操作面板 -> 独立组件

#### ✅ 状态管理
- [ ] 直接使用 `st.session_state` -> `SessionStateAdapter`
- [ ] 硬编码的日志键名 -> 配置化键名
- [ ] 混合的同步/异步 -> `AsyncActionHandler`

### 验证测试

**文件**: `tests/ui/test_components.py`

```python
import pytest
from unittest.mock import MagicMock, Mock

# 模拟PlayerStateView
class MockPlayerStateView:
    def get_player_id(self): return "player_1"
    def get_player_name(self): return "测试玩家"
    def get_team_stamina(self): return [100, 80, 60, 40]
    def get_emotion(self): return "正常"
    def get_emotion_confidence(self): return 0.8
    def get_churn_risk_level(self): return "低"
    def get_churn_risk_score(self): return 0.2
    def get_bot_status(self): return (False, 0.1)
    def get_last_updated(self): return "10:00:00"


def test_action_grid_triggers_callback():
    """测试动作网格触发回调"""
    clicked = []
    
    def on_click(action: str):
        clicked.append(action)
    
    # 创建网格实例（不实际渲染）
    grid = ActionGridComponent(on_action_click=on_click)
    
    # 验证回调可调用
    grid._on_click("test_action")
    assert clicked == ["test_action"]
```

---

## UI服务层注册

更新 `core/bootstrap.py`:

```python
# 在 create_production_container 中添加UI服务

# Application Services
from application.services.action_service import ActionProcessingService
from application.services.agent_service import AgentService

def create_production_container(...):
    # ... 现有注册
    
    # 服务层
    container.register_factory(
        ActionProcessingService,
        lambda c: ActionProcessingService(
            game_context=c.resolve(GameContext)
        ),
        lifetime=LifetimeScope.SCOPED
    )
    
    container.register_factory(
        AgentService,
        lambda c: AgentService(
            game_context=c.resolve(GameContext)
        ),
        lifetime=LifetimeScope.SCOPED
    )
    
    return container
```

---

## 新旧代码对比

### 旧方式（问题代码）

```python
# streamlit_dashboard.py

# 混合业务逻辑和UI
async def process_atomic_action(player_id: str, action_name: str):
    # UI代码
    add_behavior_log(player_id, action_name)
    add_agent_log(f"执行动作: {action_name}")
    
    # 业务逻辑
    triggered = monitor.add_atomic_action(player_id, action_name)
    
    # 情绪判断
    final_emotion = "neutral"
    if triggered:
        final_emotion = monitor.rule_engine.get_emotion_type_from_scenarios(triggered)
    
    # 计数逻辑
    if final_emotion == "negative":
        current = st.session_state.player_negative_counts.get(player_id, 0) + 1
        st.session_state.player_negative_counts[player_id] = current
        
        if current >= monitor.threshold:
            add_agent_log("已达到阈值")
            await _trigger_async_intervention(system, player_id)
            st.session_state.player_negative_counts[player_id] = 0
```

### 新方式（分离后）

```python
# ui/pages/...py
from application.services import ActionProcessingService
from ui.components import ActionGridComponent, PlayerStatusPanel

# 纯UI协调层
class DashboardPage:
    def __init__(self, container: DIContainer):
        self._action_service = container.resolve(ActionProcessingService)
        self._state = create_state_adapter()
        self._log = LogAdapter(self._state)
    
    async def handle_action(self, action_name: str):
        # 调用服务
        result = await self._action_service.process_action(
            self._current_player_id,
            action_name
        )
        
        # 更新UI
        self._log.log(f"执行: {action_name}")
        
        if result.should_intervene:
            self._log.log("已达到阈值，触发干预")
            await self._agent_service.trigger_intervention(result.player_id)
            self._action_service.reset_negative_count(result.player_id)
        
        st.rerun()
```

---

## 验收标准

1. ✅ `streamlit_dashboard.py` 从720行减少到300行以内
2. ✅ 业务逻辑全部移入 `application/services/`
3. ✅ UI组件全部移入 `ui/components/`
4. ✅ 无业务逻辑直接访问 `st.session_state`
5. ✅ 纯单元测试可运行（无Streamlit依赖）
6. ✅ Streamlit应用正常运行

---

**文档结束**
