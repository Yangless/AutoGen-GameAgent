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
from game_monitoring.simulator.behavior_simulator import PlayerBehaviorSimulator, PlayerBehaviorRuleEngine
from game_monitoring.simulator.player_behavior import PlayerBehavior, PlayerActionDefinitions
from game_monitoring.context import get_global_monitor, get_global_player_state_manager


import mlflow

# Turn on auto tracing for AutoGen


# Optional: Set a tracking URI and an experiment
mlflow.set_tracking_uri("http://127.0.0.1:5000")
mlflow.set_experiment("GameMonitoring_TeamManager_test2")
mlflow.autogen.autolog()
# 设置MLflow追踪配置，将team_manager作为一个整体监控
# mlflow.start_run(run_name="team_manager_monitoring", nested=True)

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
    
    /* 原子动作按钮样式优化 */
    .stButton > button {
        width: 100%;
        height: 2.5rem;
        font-size: 0.9rem;
        border-radius: 0.5rem;
        border: 1px solid #ddd;
        background-color: #ffffff;
        color: #333333;
        transition: all 0.2s ease;
        margin-bottom: 0.5rem;
    }
    
    .stButton > button:hover {
        background-color: #f0f2f6;
        border-color: #1f77b4;
        color: #1f77b4;
        transform: translateY(-1px);
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .stButton > button:active {
        transform: translateY(0);
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    
    /* 动作分类标题样式 */
    .action-category {
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e0e0e0;
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

# 专门用于团队分析的日志捕获类
class TeamAnalysisLogCapture:
    def __init__(self):
        self.logs = []
        self.max_logs = 10000
        self.is_capturing = False
    
    def start_capture(self):
        """开始捕获日志"""
        self.is_capturing = True
        self.logs.clear()  # 清空之前的日志
    
    def stop_capture(self):
        """停止捕获日志"""
        self.is_capturing = False
    
    def write(self, text):
        if self.is_capturing and text.strip():  # 只在捕获状态下记录日志
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]  # 包含毫秒
            self.logs.append(f"[{timestamp}] {text.strip()}")
            # 保持最近的日志
            if len(self.logs) > self.max_logs:
                self.logs = self.logs[-self.max_logs:]
            # 更新session state中的团队分析日志
            if 'team_analysis_logs' in st.session_state:
                st.session_state.team_analysis_logs = self.logs.copy()
    
    def flush(self):
        pass
    
    def get_all_logs(self):
        return self.logs.copy()
    
    def clear_logs(self):
        self.logs.clear()
        if 'team_analysis_logs' in st.session_state:
            st.session_state.team_analysis_logs = []




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
if 'team_analysis_capture' not in st.session_state:
    st.session_state.team_analysis_capture = TeamAnalysisLogCapture()
if 'team_analysis_logs' not in st.session_state:
    st.session_state.team_analysis_logs = []
if 'agent_analysis_logs' not in st.session_state:
    st.session_state.agent_analysis_logs = []
if 'player_negative_counts' not in st.session_state:
    st.session_state.player_negative_counts = {}
# 新增原子动作相关状态
if 'action_definitions' not in st.session_state:
    st.session_state.action_definitions = PlayerActionDefinitions()
if 'rule_engine' not in st.session_state:
    st.session_state.rule_engine = PlayerBehaviorRuleEngine()
if 'action_sequence' not in st.session_state:
    st.session_state.action_sequence = []

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
    if len(st.session_state.behavior_logs) > 100:
        st.session_state.behavior_logs = st.session_state.behavior_logs[-100:]

def add_agent_log(message: str):
    """添加Agent日志"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    st.session_state.agent_logs.append(log_entry)
    # 保持最近30条记录
    if len(st.session_state.agent_logs) > 50:
        st.session_state.agent_logs = st.session_state.agent_logs[-50:]

async def process_atomic_action(player_id: str, action_name: str):
    """处理原子动作并通过规则引擎分析
    
    主要流程：
    1. 记录动作到历史和序列
    2. 使用规则引擎分析动作序列
    3. 分析单个动作的情绪倾向
    4. 综合判断并更新计数
    5. 检查是否需要触发干预
    """
    from game_monitoring.simulator.player_behavior import PlayerBehavior
    
    system = st.session_state.system
    monitor = st.session_state.monitor
    
    # === 第一步：记录动作数据 ===
    current_time = datetime.now()
    
    # 添加动作到全局序列（用于UI显示）
    action_data = {
        'action': action_name,
        'params': {},
        'timestamp': current_time,
        'player_id': player_id
    }
    st.session_state.action_sequence.append(action_data)
    
    # 创建PlayerBehavior对象并添加到behavior_history
    behavior = PlayerBehavior(
        player_id=player_id,
        timestamp=current_time,
        action=action_name,
        result="success"
    )
    monitor.behavior_history.append(behavior)
    
    # 记录基础日志
    add_behavior_log(player_id, action_name)
    add_agent_log(f"🎯 执行动作: {action_name}")
    
    # === 第二步：规则引擎序列分析 ===
    triggered_scenarios = monitor.add_atomic_action(player_id, action_name)
    
    # === 第三步：获取详细序列信息用于显示 ===
    full_sequence = monitor.get_player_action_sequence(player_id)
    recent_actions = monitor.get_recent_actions_for_analysis(player_id)
    
    # 输出详细的序列和场景信息
    add_agent_log(f"📋 完整动作序列 ({len(full_sequence)} 个): {[a['action'] for a in full_sequence]}")
    add_agent_log(f"🔍 分析窗口 ({len(recent_actions)} 个): {[a['action'] for a in recent_actions]}")
    
    if triggered_scenarios:
        add_agent_log(f"🎭 触发场景数量: {len(triggered_scenarios)}")
        for i, scenario in enumerate(triggered_scenarios, 1):
            scenario_name = scenario.get('scenario', '未知场景')
            scenario_desc = scenario.get('description', '无描述')
            add_agent_log(f"   {i}. {scenario_name}: {scenario_desc}")
    else:
        add_agent_log("🎭 未触发任何场景")
    
    # === 第四步：单个动作情绪分析 ===
    # single_action_emotion = monitor.rule_engine.analyze_single_action_emotion(action_name)
    
    # === 第五步：综合情绪判断 ===
    final_emotion_type = "neutral"
    
    # 优先使用序列分析结果（更准确）
    if triggered_scenarios:
        sequence_emotion = monitor.rule_engine.get_emotion_type_from_scenarios(triggered_scenarios)
        final_emotion_type = sequence_emotion
        add_agent_log(f"📈 序列分析情绪: {sequence_emotion}")
    
    # # 如果序列分析为中性，则使用单个动作分析结果
    # if final_emotion_type == "neutral" and single_action_emotion != "neutral":
    #     final_emotion_type = single_action_emotion
    #     add_agent_log(f"🎯 单动作情绪: {single_action_emotion}")
    
    # add_agent_log(f"😊 最终情绪类型: {final_emotion_type}")
    
    # === 第六步：更新计数和触发干预 ===
    if final_emotion_type == "negative":
        # 更新消极行为计数
        st.session_state.player_negative_counts.setdefault(player_id, 0)
        st.session_state.player_negative_counts[player_id] += 1
        current_count = st.session_state.player_negative_counts[player_id]
        
        add_agent_log(f"⚠️ 检测到消极行为，计数更新: {current_count}")
        
        # 检查是否达到干预阈值
        if current_count >= monitor.threshold:
            add_agent_log(f"🚨 玩家 {player_id} 达到负面行为阈值 ({current_count}/{monitor.threshold})")
            
            # 异步触发智能体干预
            await _trigger_async_intervention(system, player_id)
            
            # 重置计数器
            st.session_state.player_negative_counts[player_id] = 0
            add_agent_log(f"🔄 重置玩家 {player_id} 的负面行为计数为0")
    
    # === 第七步：记录最终状态 ===
    current_negative_count = st.session_state.player_negative_counts.get(player_id, 0)
    sequence_length = len(monitor.get_player_action_sequence(player_id))
    add_agent_log(f"📊 状态更新完成 - 负面计数: {current_negative_count}/{monitor.threshold}, 序列长度: {sequence_length}")


async def _trigger_async_intervention(system, player_id: str):
    """异步触发智能体干预"""
    try:
        import asyncio
        import threading
        
        # 在主线程中获取团队分析日志捕获器
        team_capture = st.session_state.team_analysis_capture
        
        def run_intervention(capture_obj):
            # 保存原始stdout
            original_stdout = sys.stdout
            
            try:
                # 开始捕获团队分析日志
                capture_obj.start_capture()
                
                # 重定向stdout到团队分析捕获器
                sys.stdout = capture_obj
                
                # 创建新的事件循环并运行干预
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(system.trigger_analysis_and_intervention(player_id))
                loop.close()
                
            finally:
                # 恢复原始stdout
                sys.stdout = original_stdout
                # 停止捕获
                capture_obj.stop_capture()
        
        # 在后台线程中运行干预，传递捕获对象
        intervention_thread = threading.Thread(target=run_intervention, args=(team_capture,))
        intervention_thread.daemon = True
        intervention_thread.start()
        
        add_agent_log(f"🎯 已触发玩家 {player_id} 的智能体分析和干预")
    except Exception as e:
        add_agent_log(f"❌ 触发干预时出错: {str(e)}")




async def trigger_behavior_and_analysis(player_id: str, behavior_type: str, specific_action: str = None):
    """触发行为并进行分析（保留兼容性）"""
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
        
        # 使用新的团队分析日志捕获机制
        team_capture = st.session_state.team_analysis_capture
        original_stdout = sys.stdout
        
        try:
            # 开始捕获团队分析日志
            team_capture.start_capture()
            add_agent_log(f"🎯 开始捕获团队分析日志...")
            
            # 重定向标准输出到团队分析捕获器
            sys.stdout = team_capture
            
            # 触发分析和干预
            await system.trigger_analysis_and_intervention(player_id)
            
            add_agent_log(f"✅ 团队分析完成，共捕获 {len(team_capture.get_all_logs())} 条日志")
            
        finally:
            # 恢复标准输出
            sys.stdout = original_stdout
            # 停止捕获
            team_capture.stop_capture()
        
        # 重置计数
        st.session_state.player_negative_counts[player_id] = 0
        add_agent_log(f"🔄 重置玩家 {player_id} 的负面行为计数为0")
    else:
        add_agent_log(f"📊 行为已记录，当前负面行为计数: {st.session_state.player_negative_counts.get(player_id, 0)}") # CHANGED

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
            # 基础系统日志 - 显示所有日志，不进行过滤
            if st.session_state.agent_logs:
                # 显示所有日志，不进行过滤
                all_logs = st.session_state.agent_logs
                # 显示最新的日志在最上面
                for log in reversed(all_logs):
                    st.markdown(f'<div class="agent-log">{log}</div>', unsafe_allow_html=True)
            else:
                st.info("等待系统活动...")
        
        with tab2:
            # Agent团队分析日志
            st.markdown("**🧠 团队分析实时日志**")
            
            # 添加清空日志按钮
            col_clear, col_count = st.columns([1, 3])
            with col_clear:
                if st.button("🗑️ 清空日志", key="clear_team_logs"):
                    if 'team_analysis_capture' in st.session_state:
                        st.session_state.team_analysis_capture.clear_logs()
                        st.rerun()
            
            with col_count:
                log_count = 0
                if 'team_analysis_capture' in st.session_state and st.session_state.team_analysis_capture:
                    log_count = len(st.session_state.team_analysis_capture.get_all_logs())
                st.write(f"📊 当前日志条数: {log_count}")
            
            # 显示团队分析日志 - 直接从 team_analysis_capture 获取日志
            team_logs = []
            if 'team_analysis_capture' in st.session_state and st.session_state.team_analysis_capture:
                team_logs = st.session_state.team_analysis_capture.get_all_logs()
            
            if team_logs:
                # 按时间线从前往后显示（最早的在最上面，最新的在最下面）
                log_entries_html = "".join([f'<div class="agent-log">{log}</div>' for log in team_logs])
                
                # 使用CSS容器包裹所有日志条目，支持滚动
                log_container_html = f'''
                <div class="log-container" style="height: 400px; overflow-y: auto; border: 1px solid #ddd; border-radius: 5px; padding: 10px; background-color: #f9f9f9; margin-bottom: 1rem;">
                    {log_entries_html}
                </div>
                '''
                
                st.markdown(log_container_html, unsafe_allow_html=True)
                
                # 自动滚动到底部的JavaScript
                st.markdown("""
                <script>
                setTimeout(function() {
                    var container = document.querySelector('.log-container');
                    if (container) {
                        container.scrollTop = container.scrollHeight;
                    }
                }, 100);
                </script>
                """, unsafe_allow_html=True)
            else:
                st.info("💭 等待Agent团队分析...\n\n当检测到玩家负面行为达到阈值时，系统将自动触发多智能体团队分析，所有分析过程将在此处实时显示。")
        
        # 系统状态信息
        st.subheader("📈 系统状态")
        # CHANGED: 直接使用从 session_state 获取的 monitor
        if monitor:
            total_behaviors = len(monitor.behavior_history)
            negative_counts = st.session_state.player_negative_counts
            current_player_count = negative_counts.get(st.session_state.current_player_id, 0)
            action_sequence_length = len(st.session_state.action_sequence)
            
            col2_1, col2_2, col2_3, col2_4 = st.columns(4)
            with col2_1:
                st.metric("总行为记录", total_behaviors)
            with col2_2:
                st.metric("监控阈值", monitor.threshold)
            with col2_3:
                st.metric("当前玩家负面行为", current_player_count, delta=1 if current_player_count >= monitor.threshold else None)
            with col2_4:
                st.metric("动作序列长度", action_sequence_length)
            
            # 显示阈值状态
            if current_player_count >= monitor.threshold:
                st.error(f"🚨 玩家 {st.session_state.current_player_id} 已达到分析阈值！")
            else:
                remaining = monitor.threshold - current_player_count
                st.success(f"✅ 距离触发分析还需 {remaining} 次负面行为")
            
            # 显示动作序列状态
            if action_sequence_length > 0:
                st.info(f"📊 当前动作序列包含 {action_sequence_length} 个动作")
                recent_actions = [action['action'] for action in st.session_state.action_sequence[-3:]]
                if recent_actions:
                    st.write(f"**最近动作:** {' → '.join(recent_actions)}")
            
            if negative_counts:
                st.write("**所有玩家负面行为计数:**")
                for pid, count in negative_counts.items():
                    st.write(f"- {pid}: {count}")
    
    # 右侧面板 - 原子动作界面
    with col3:
        st.markdown('<h2 class="section-header">🎯 原子动作界面</h2>', unsafe_allow_html=True)
        
        action_definitions = st.session_state.action_definitions
        
        # 动作名称中英文映射
        action_name_mapping = {
            # 核心游戏动作
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
            # 社交动作
            "join_family": "加入家族",
            "leave_family": "离开家族",
            "join_nation": "加入国家",
            "send_chat_message": "发送聊天",
            "receive_chat_message": "接收聊天",
            "add_friend": "添加好友",
            "remove_friend": "删除好友",
            "receive_praise": "收到赞美",
            "be_invited_to_family": "被邀请入族",
            # 经济动作
            "navigate_to_payment_page": "跳转充值页",
            "make_payment": "进行充值",
            "buy_monthly_card": "购买月卡",
            "cancel_auto_renew": "取消自动续费",
            "receive_daily_reward": "领取日常奖励",
            "receive_event_reward": "领取活动奖励",
            "sell_item": "出售物品",
            "clear_backpack": "清理背包",
            "post_account_for_sale": "发布账号出售",
            # 元数据动作
            "submit_review": "提交评价",
            "contact_support": "联系客服",
            "change_nickname": "修改昵称",
            "click_exit_game_button": "点击退出按钮",
            "uninstall_game": "卸载游戏"
        }
        
        def get_chinese_name(action):
            """获取动作的中文名称"""
            action_name = action.split('(')[0]
            return action_name_mapping.get(action_name, action_name)
        
        def render_action_grid(actions, category_key, cols=3):
            """渲染动作网格布局"""
            if not actions:
                return
            
            # 计算需要的行数
            rows = (len(actions) + cols - 1) // cols
            
            for row in range(rows):
                columns = st.columns(cols)
                for col_idx in range(cols):
                    action_idx = row * cols + col_idx
                    if action_idx < len(actions):
                        action = actions[action_idx]
                        action_name = action.split('(')[0]
                        chinese_name = get_chinese_name(action)
                        
                        with columns[col_idx]:
                            if st.button(
                                chinese_name, 
                                key=f"{category_key}_{action_idx}", 
                                help=f"点击执行: {action}",
                                use_container_width=True
                            ):
                                run_async(process_atomic_action(st.session_state.current_player_id, action_name))
                                st.rerun()
        
        # 核心游戏动作 - 显示所有动作
        st.markdown("### 🎮 核心游戏动作")
        render_action_grid(action_definitions.core_game_actions, "core", cols=3)
        
        # 社交动作 - 显示所有动作
        st.markdown("### 👥 社交动作")
        render_action_grid(action_definitions.social_actions, "social", cols=3)
        
        # 经济动作 - 显示所有动作
        st.markdown("### 💰 经济动作")
        render_action_grid(action_definitions.economic_actions, "economic", cols=3)
        
        # 元数据动作 - 显示所有动作
        st.markdown("### 📋 元数据动作")
        render_action_grid(action_definitions.meta_actions, "meta", cols=3)
        
        # 动作序列管理
        st.markdown("### 📊 动作序列管理")
        col3_1, col3_2 = st.columns(2)
        with col3_1:
            if st.button("📋 查看序列", help="查看当前动作序列"):
                if st.session_state.action_sequence:
                    st.info(f"当前序列长度: {len(st.session_state.action_sequence)}")
                    for i, action in enumerate(st.session_state.action_sequence[-5:], 1):
                        st.write(f"{i}. {action['action']} ({action['timestamp'].strftime('%H:%M:%S')})")
                else:
                    st.info("动作序列为空")
        with col3_2:
            if st.button("🗑️ 清空序列", help="清空当前动作序列"):
                st.session_state.action_sequence = []
                add_agent_log("🗑️ 动作序列已清空")
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