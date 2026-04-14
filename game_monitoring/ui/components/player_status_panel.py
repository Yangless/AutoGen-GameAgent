"""
玩家状态面板组件

纯UI组件，无业务逻辑
"""

import streamlit as st
from typing import Protocol, List


class PlayerStateView(Protocol):
    """Player状态展示协议"""
    def get_player_id(self) -> str: ...
    def get_player_name(self) -> str: ...
    def get_team_stamina(self) -> List[int]: ...
    def get_emotion(self) -> str: ...
    def get_emotion_confidence(self) -> float: ...
    def get_churn_risk_level(self) -> str: ...
    def get_churn_risk_score(self) -> float: ...
    def get_bot_status(self) -> tuple: ...


class PlayerStatusPanel:
    """玩家状态面板"""

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
            with col:
                st.metric(f"队伍{i+1}", f"{val}%")

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
        is_bot, bot_confidence = self._view.get_bot_status()
        st.metric("是否机器人", "是" if is_bot else "否", f"置信度: {bot_confidence:.0%}")


class PlayerStatusPanelCompact:
    """紧凑版玩家状态面板"""

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


# 简单的View实现
class SimplePlayerStateView:
    """简单的PlayerStateView实现"""

    def __init__(self, **kwargs):
        self._data = kwargs

    def get_player_id(self) -> str:
        return self._data.get('player_id', 'unknown')

    def get_player_name(self) -> str:
        return self._data.get('player_name', 'Unknown')

    def get_team_stamina(self) -> List[int]:
        return self._data.get('team_stamina', [100, 100, 100, 100])

    def get_emotion(self) -> str:
        return self._data.get('emotion', '未知')

    def get_emotion_confidence(self) -> float:
        return self._data.get('emotion_confidence', 0.0)

    def get_churn_risk_level(self) -> str:
        return self._data.get('churn_risk_level', '未知')

    def get_churn_risk_score(self) -> float:
        return self._data.get('churn_risk_score', 0.0)

    def get_bot_status(self) -> tuple:
        return self._data.get('bot_status', (False, 0.0))
