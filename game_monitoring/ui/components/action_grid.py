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
    actions: List[Tuple[str, str]]


class ActionGridComponent:
    """
    动作网格组件

    展示分类的原子动作按钮
    """

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
