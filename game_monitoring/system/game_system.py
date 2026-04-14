import asyncio
import random
import time

try:
    from config import custom_model_client
except ModuleNotFoundError:
    custom_model_client = None

from ..core.bootstrap import bootstrap_application
from ..core.context import GameContext
from ..simulator import PlayerBehaviorSimulator
from ..team import GameMonitoringTeamV2
from ..ui import GameMonitoringConsole
from .action_sequence_manager import ActionSequenceManager

class GamePlayerMonitoringSystem:
    """游戏玩家监控系统主协调器"""
    
    def __init__(self, model_client=None):
        self.model_client = model_client or custom_model_client
        self.simulator = PlayerBehaviorSimulator()
        self.container = bootstrap_application(custom_model_client=self.model_client)
        self.context = self.container.resolve(GameContext)
        self.monitor = self.context.monitor
        self.player_state_manager = self.context.player_state_manager
        self.team = self.container.resolve(GameMonitoringTeamV2)
        
        # 创建UI控制台
        self.ui = GameMonitoringConsole()
        
        # 创建动作序列管理器（新的动态触发模式）
        self.action_manager = ActionSequenceManager(self.monitor, self.team)
        
        print("🎮 游戏Agent助手系统已初始化 (支持动态触发架构)")

    async def trigger_analysis_and_intervention(self, player_id: str):
        """触发对指定玩家的分析和干预"""
        self.ui.print_team_activation(player_id)
        result = await self.team.trigger_analysis_and_intervention(player_id, self.monitor)
        if hasattr(self.ui, "print_intervention_result"):
            self.ui.print_intervention_result(result)
        return result
        # 计数器重置现在在streamlit_dashboard.py中处理

    async def simulate_monitoring_session(self, duration_seconds: int = 60, mode: str = "random", dataset_type: str = "mixed"):
        """
        模拟监控会话
        
        Args:
            duration_seconds: 会话持续时间（秒）
            mode: 数据生成模式 - "random" 随机生成, "preset" 预设序列, 或 "interactive" 交互式动态触发
            dataset_type: 当mode="preset"时，指定数据集类型（"mixed", "negative", "positive"）
        """
        self.ui.print_session_start(duration_seconds, mode)
        
        if mode == "random":
            # 随机生成模式
            players = [f"player_{random.randint(100, 999)}" for _ in range(5)]
            start_time = time.time()
            
            while time.time() - start_time < duration_seconds:
                player_id = random.choice(players)
                behavior = self.simulator.generate_behavior(player_id)
                self.ui.print_behavior_log(player_id, behavior.action)
                
                # 将生成的行为数据保存到monitor中
                if self.monitor.add_behavior(behavior):
                    await self.trigger_analysis_and_intervention(player_id)
                    if hasattr(self.monitor, "reset_negative_count"):
                        self.monitor.reset_negative_count(player_id)
                    # 计数器重置现在在streamlit_dashboard.py中处理
                    self.ui.print_reset_count(player_id)
                
                await asyncio.sleep(random.uniform(2, 4)) # 增加间隔以便观察
                
        elif mode == "preset":
            # 预设序列模式
            self.ui.print_dataset_loading(dataset_type)
            
            # 生成预设数据集
            dataset = self.simulator.generate_mock_dataset(dataset_type, num_players=5)
            self.ui.print_dataset_generated(len(dataset))
            
            # 将数据加载到监控器中并触发分析
            for player_id, behaviors in dataset.items():
                self.ui.print_player_processing(player_id)
                
                for behavior in behaviors:
                    self.ui.print_behavior_log(player_id, behavior.action)
                    
                    # 将行为数据保存到monitor中
                    if self.monitor.add_behavior(behavior):
                        await self.trigger_analysis_and_intervention(player_id)
                        if hasattr(self.monitor, "reset_negative_count"):
                            self.monitor.reset_negative_count(player_id)
                        # 计数器重置现在在streamlit_dashboard.py中处理
                        self.ui.print_reset_count(player_id)
                    
                    # 模拟实时处理间隔
                    await asyncio.sleep(1)
                    
        elif mode == "interactive":
            # 新的交互式动态触发模式
            print("\n🚀 启动交互式动态触发模式...")
            print("   这是新一代AI智能体触发流程:")
            print("   A(原子动作) -> B(规则引擎) -> C(智能体分析)")
            print("-" * 50)
            
            # 启动动作序列管理器
            await self.action_manager.start_interactive_session()
            
        else:
            supported_modes = ["random", "preset", "interactive"]
            print(f"❌ 不支持的模式: {mode}，请使用: {', '.join(supported_modes)}")
            return
        
        self.ui.print_session_end()
