import streamlit as st
import asyncio
import time
from datetime import datetime
from typing import List, Dict
import sys
import os
import io
import contextlib
from threading import Thread
import queue
from streamlit_autorefresh import st_autorefresh

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from game_monitoring.system.game_system import GamePlayerMonitoringSystem
from game_monitoring.simulator.behavior_simulator import PlayerBehaviorSimulator
from game_monitoring.simulator.player_behavior import PlayerBehavior
from game_monitoring.context import get_global_monitor, get_global_player_state_manager

import mlflow

# Turn on auto tracing for AutoGen
mlflow.autogen.autolog()

# Optional: Set a tracking URI and an experiment
mlflow.set_tracking_uri("http://127.0.0.1:5000")
mlflow.set_experiment("AutoGen1")


# 页面配置
st.set_page_config(
    page_title="🎮 游戏Agent助手监控系统 Dashboard",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式 - 更新版
st.markdown("""
<style>
    /* 针对Streamlit的主应用容器，移除所有内边距 */
    /* 这是最顶层的容器之一 */
    .stApp {
        padding: 0 !important;
    }

    /* 针对Streamlit的主内容块，减小顶部内边距 */
    /* 使用 !important 强制覆盖默认样式 */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important; /* 也可以顺便调整底部 */
    }

    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-top: 0 !important; /* 使用 !important 强制移除顶部外边距 */
        margin-bottom: 1rem;
    }
    
    /* 以下是您原有的其他样式，保持不变 */
    .section-header {
        font-size: 1.5rem;
        color: #ff7f0e;
        margin-bottom: 1rem;
        border-bottom: 2px solid #ff7f0e;
        padding-bottom: 0.5rem;
    }
    .player-info {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .behavior-log {
        background-color: #e8f4fd;
        padding: 0.5rem;
        border-radius: 0.3rem;
        margin-bottom: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .agent-log {
        background-color: #fff2cc;
        padding: 0.5rem;
        border-radius: 0.3rem;
        margin-bottom: 0.5rem;
        border-left: 4px solid #ff7f0e;
    }
    .log-container {
    height: 400px; /* 您可以根据需要调整这个高度 */
    overflow-y: auto; /* 当内容超出高度时，自动显示垂直滚动条 */
    border: 1px solid #ddd;
    border-radius: 5px;
    padding: 10px;
    background-color: #f9f9f9;
    margin-bottom: 1rem; /* 与下方元素的间距 */
    }
    /* ... 其他样式 ... */
</style>
""", unsafe_allow_html=True)

# 自定义日志捕获类
class StreamlitLogCapture:
    def __init__(self):
        self.logs = []
        self.max_logs = 10000
    
    def write(self, text):
        if text.strip():  # 忽略空行
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.logs.append(f"[{timestamp}] {text.strip()}")
            # 保持最近的日志
            if len(self.logs) > self.max_logs:
                self.logs = self.logs[-self.max_logs:]
            # 更新session state中的agent日志
            if 'agent_logs' in st.session_state:
                st.session_state.agent_logs = self.logs.copy()
    
    def flush(self):
        pass
    
    def get_recent_logs(self, count=20):
        return self.logs[-count:] if self.logs else []

# 初始化session state
if 'system' not in st.session_state:
    st.session_state.system = None
if 'monitor' not in st.session_state: # ADDED: 为 monitor 对象在 session_state 中占位
    st.session_state.monitor = None
if 'player_state_manager' not in st.session_state: # ADDED: 为 player_state_manager 对象在 session_state 中占位
    st.session_state.player_state_manager = None
if 'current_player_id' not in st.session_state:
    st.session_state.current_player_id = "player_001"
if 'behavior_logs' not in st.session_state:
    st.session_state.behavior_logs = []
if 'agent_logs' not in st.session_state:
    st.session_state.agent_logs = []
if 'system_initialized' not in st.session_state:
    st.session_state.system_initialized = False
if 'log_capture' not in st.session_state:
    st.session_state.log_capture = StreamlitLogCapture()
if 'agent_analysis_logs' not in st.session_state:
    st.session_state.agent_analysis_logs = []

# 异步函数包装器
def run_async(coro):
    """在Streamlit中运行异步函数的包装器"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coro)

# 初始化系统
@st.cache_resource
def initialize_system():
    """初始化游戏监控系统"""
    system = GamePlayerMonitoringSystem()
    return system

def add_behavior_log(player_id: str, action: str):
    """添加行为日志"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] 玩家 {player_id}: {action}"
    st.session_state.behavior_logs.append(log_entry)
    # 保持最近50条记录
    if len(st.session_state.behavior_logs) > 50:
        st.session_state.behavior_logs = st.session_state.behavior_logs[-50:]

def add_agent_log(message: str):
    """添加Agent日志"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    st.session_state.agent_logs.append(log_entry)
    # 保持最近30条记录
    if len(st.session_state.agent_logs) > 30:
        st.session_state.agent_logs = st.session_state.agent_logs[-30:]

async def trigger_behavior_and_analysis(player_id: str, behavior_type: str, specific_action: str = None):
    """触发行为并进行分析"""
    system = st.session_state.system
    
    # 生成行为
    if specific_action:
        behavior = PlayerBehavior(
            player_id=player_id,
            timestamp=datetime.now(),
            action=specific_action
        )
    else:
        behavior = system.simulator.generate_targeted_behavior(player_id, behavior_type)
    
    # 记录行为日志
    add_behavior_log(player_id, behavior.action)
    add_agent_log(f"🎯 检测到玩家行为: {behavior.action}")
    
    # 添加到监控系统
    if st.session_state.monitor.add_behavior(behavior): # CHANGED: 直接使用 session_state 中的 monitor
        add_agent_log(f"⚠️ 触发分析阈值，启动多智能体团队分析...")
        
        # 捕获Agent团队的详细处理过程
        original_stdout = sys.stdout
        log_capture = st.session_state.log_capture
        
        try:
            # 重定向标准输出到我们的日志捕获器
            sys.stdout = log_capture
            
            # 触发分析和干预
            await system.trigger_analysis_and_intervention(player_id)
            
            add_agent_log(f"✅ 分析完成")
            
        finally:
            # 恢复标准输出
            
            sys.stdout = original_stdout
        
        # 重置计数
        st.session_state.monitor.player_negative_counts[player_id] = 0 # CHANGED
        add_agent_log(f"🔄 重置玩家 {player_id} 的负面行为计数")
    else:
        add_agent_log(f"📊 行为已记录，当前负面行为计数: {st.session_state.monitor.player_negative_counts.get(player_id, 0)}") # CHANGED

# 主界面
def main():
    # --- 在这里添加自动刷新组件 ---
    st_autorefresh(interval=2000, limit=None, key="auto_refresh_dashboard")

    # 标题
    st.markdown('<h1 class="main-header">🎮 Agent助手监控系统 Dashboard</h1>', unsafe_allow_html=True)
    
    # 初始化系统
    if not st.session_state.system_initialized:
        with st.spinner("正在初始化监控系统..."):
            st.session_state.system = initialize_system()
            # ADDED: 在系统初始化后，获取一次 monitor 和 player_state_manager 并存入 session_state
            st.session_state.monitor = get_global_monitor()
            st.session_state.player_state_manager = get_global_player_state_manager()
            st.session_state.system_initialized = True
            add_agent_log("🚀 监控系统初始化完成")
    
    # 从 session_state 获取核心对象，避免重复调用 get 函数
    monitor = st.session_state.monitor
    player_state_manager = st.session_state.player_state_manager
    system = st.session_state.system
    
    # 三栏布局
    col1, col2, col3 = st.columns([1, 2, 1])
    
    # 左侧面板 - 玩家状态展示
    with col1:
        st.markdown('<h2 class="section-header">👤 玩家状态</h2>', unsafe_allow_html=True)
        
        # 玩家基本信息
        st.markdown(f'<div class="player-info"><strong>玩家ID:</strong> {st.session_state.current_player_id}</div>', unsafe_allow_html=True)
        
        # 获取玩家状态
        # CHANGED: 直接使用从 session_state 获取的 player_state_manager
        if player_state_manager:
            player_state = player_state_manager.get_player_state(st.session_state.current_player_id)
            
            # 情绪状态
            st.subheader("😊 情绪状态")
            emotion = player_state.emotion or "未知"
            emotion_confidence = player_state.emotion_confidence
            st.metric("当前情绪", emotion, f"置信度: {emotion_confidence:.2f}")
            if player_state.emotion_keywords:
                st.write("关键词:", ", ".join(player_state.emotion_keywords))
            
            # 流失风险
            st.subheader("⚠️ 流失风险")
            churn_risk = player_state.churn_risk_level or "未知"
            churn_score = player_state.churn_risk_score
            st.metric("风险等级", churn_risk, f"风险分数: {churn_score:.2f}")
            if player_state.churn_risk_factors:
                st.write("风险因素:", ", ".join(player_state.churn_risk_factors))
            
            # 机器人检测
            st.subheader("🤖 机器人检测")
            is_bot = "是" if player_state.is_bot else "否"
            bot_confidence = player_state.bot_confidence
            st.metric("是否机器人", is_bot, f"置信度: {bot_confidence:.2f}")
            if player_state.bot_patterns:
                st.write("检测模式:", ", ".join(player_state.bot_patterns))
            
            # 最后更新时间
            st.write(f"**最后更新:** {player_state.last_updated.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 行为历史
        st.subheader("📊 最近行为历史")
        # CHANGED: 直接使用从 session_state 获取的 monitor
        if monitor:
            recent_behaviors = monitor.get_player_history(st.session_state.current_player_id)[-5:]
            if recent_behaviors:
                for behavior in recent_behaviors:
                    st.markdown(f'<div class="behavior-log">{behavior.timestamp.strftime("%H:%M:%S")}: {behavior.action}</div>', unsafe_allow_html=True)
            else:
                st.write("暂无行为记录")
    
    # 中央面板 - Agent决策流程
    with col2:
        st.markdown('<h2 class="section-header">🤖 Agent 决策流程</h2>', unsafe_allow_html=True)
        
        # 创建两个标签页：基础日志和Agent分析日志
        tab1, tab2 = st.tabs(["📋 基础日志", "🧠 Agent团队分析"])
        
        with tab1:
            # 基础系统日志
            if st.session_state.agent_logs:
                # 过滤掉Agent分析相关的详细日志
                basic_logs = [log for log in st.session_state.agent_logs if not any(keyword in log for keyword in ["🤖 启动多智能体团队", "团队实时动态", "Chief Orchestrator"])]
                recent_logs = basic_logs[-15:] if basic_logs else ["等待系统活动..."]
                for log in reversed(recent_logs):
                    st.markdown(f'<div class="agent-log">{log}</div>', unsafe_allow_html=True)
            else:
                st.info("等待系统活动...")
        
        with tab2:
            # Agent团队分析日志
            if hasattr(st.session_state, 'log_capture') and st.session_state.log_capture.logs:
                # 获取所有捕获的日志
                all_logs = st.session_state.log_capture.logs
                
                # 将日志条目拼接成一个HTML字符串
                # 我们依然倒序显示，让最新的日志在最上面
                log_entries_html = "".join([f'<div class="agent-log">{log}</div>' for log in reversed(all_logs)])
                
                # 使用我们新定义的CSS容器来包裹所有日志条目
                log_container_html = f'<div class="log-container">{log_entries_html}</div>'
                
                st.markdown(log_container_html, unsafe_allow_html=True)

            else:
                st.info("等待Agent团队分析...")
        
        # 系统状态信息
        st.subheader("📈 系统状态")
        # CHANGED: 直接使用从 session_state 获取的 monitor
        if monitor:
            total_behaviors = len(monitor.behavior_history)
            negative_counts = monitor.player_negative_counts
            current_player_count = negative_counts.get(st.session_state.current_player_id, 0)
            
            col2_1, col2_2, col2_3 = st.columns(3)
            with col2_1:
                st.metric("总行为记录", total_behaviors)
            with col2_2:
                st.metric("监控阈值", monitor.threshold)
            with col2_3:
                st.metric("当前玩家负面行为", current_player_count, delta=1 if current_player_count >= monitor.threshold else None)
            
            # 显示阈值状态
            if current_player_count >= monitor.threshold:
                st.error(f"🚨 玩家 {st.session_state.current_player_id} 已达到分析阈值！")
            else:
                remaining = monitor.threshold - current_player_count
                st.success(f"✅ 距离触发分析还需 {remaining} 次负面行为")
            
            if negative_counts:
                st.write("**所有玩家负面行为计数:**")
                for pid, count in negative_counts.items():
                    st.write(f"- {pid}: {count}")
    
    # 右侧面板 - 行为模拟器
    with col3:
        st.markdown('<h2 class="section-header">🎯 行为模拟器</h2>', unsafe_allow_html=True)
        
        if system:
            simulator = system.simulator
            
            # 积极情绪场景
            st.markdown("### 😊 积极情绪场景")
            positive_scenarios = simulator.positive_scenarios[:4]  # 取前4个
            for i, scenario in enumerate(positive_scenarios):
                if st.button(scenario, key=f"pos_{i}", help="点击模拟积极行为"):
                    run_async(trigger_behavior_and_analysis(st.session_state.current_player_id, "positive", scenario))
                    st.rerun()
            
            # 消极情绪场景
            st.markdown("### 😞 消极情绪场景")
            negative_scenarios = simulator.negative_scenarios[:4]  # 取前4个
            for i, scenario in enumerate(negative_scenarios):
                if st.button(scenario, key=f"neg_{i}", help="点击模拟消极行为"):
                    run_async(trigger_behavior_and_analysis(st.session_state.current_player_id, "negative", scenario))
                    st.rerun()
            
            # 流失风险场景
            st.markdown("### ⚠️ 流失风险场景")
            churn_scenarios = simulator.churn_risk_scenarios[:4]  # 取前4个
            for i, scenario in enumerate(churn_scenarios):
                if st.button(scenario, key=f"churn_{i}", help="点击模拟流失风险行为"):
                    run_async(trigger_behavior_and_analysis(st.session_state.current_player_id, "churn_risk", scenario))
                    st.rerun()
            
            # 机器人行为场景
            st.markdown("### 🤖 机器人行为场景")
            bot_scenarios = simulator.bot_scenarios[:4]  # 取前4个
            for i, scenario in enumerate(bot_scenarios):
                if st.button(scenario, key=f"bot_{i}", help="点击模拟机器人行为"):
                    run_async(trigger_behavior_and_analysis(st.session_state.current_player_id, "bot", scenario))
                    st.rerun()
            
            # 随机行为按钮
            st.markdown("### 🎲 随机行为")
            if st.button("🎲 生成随机行为", help="随机生成一个行为"):
                run_async(trigger_behavior_and_analysis(st.session_state.current_player_id, "basic"))
                st.rerun()
    
    # 底部状态栏
    st.markdown("---")
    status_col1, status_col2, status_col3 = st.columns(3)
    with status_col1:
        st.write(f"🕒 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    with status_col2:
        st.write(f"👤 当前玩家: {st.session_state.current_player_id}")
    with status_col3:
        system_status = "🟢 运行中" if st.session_state.system_initialized else "🔴 未初始化"
        st.write(f"⚙️ 系统状态: {system_status}")

if __name__ == "__main__":
    main()