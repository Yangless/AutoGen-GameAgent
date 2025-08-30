from autogen_agentchat.ui import Console

class GameMonitoringConsole:
    """
    游戏监控系统的控制台UI封装类
    
    提供统一的控制台输出接口，用于显示团队协作过程和系统状态。
    """
    
    def __init__(self):
        self.console = Console
    
    async def display_team_stream(self, team_stream):
        """
        显示团队协作的实时流式输出
        
        Args:
            team_stream: MagenticOneGroupChat.run_stream() 返回的流式对象
        """
        print("\n" + "="*25 + " 团队实时动态 " + "="*23)
        await self.console(team_stream)
        print("="*62 + "\n")
    
    @staticmethod
    def print_system_header():
        """打印系统启动头部信息"""
        print("=" * 50)
        print("🎮 游戏玩家实时行为监控助手")
        print("=" * 50)
    
    @staticmethod
    def print_session_info(mode: str, dataset_type: str = None, duration: int = 60):
        """打印会话配置信息"""
        print(f"📋 运行参数:")
        print(f"   - 数据模式: {mode}")
        if mode == "preset" and dataset_type:
            print(f"   - 数据集类型: {dataset_type}")
        print(f"   - 持续时间: {duration}秒")
        print("-" * 50)
    
    @staticmethod
    def print_usage_info():
        """打印使用说明"""
        print("\n💡 使用说明:")
        print("   python main.py [mode] [dataset_type] [duration]")
        print("   - mode: 'random' (随机生成) 或 'preset' (预设序列)")
        print("   - dataset_type: 'mixed', 'negative', 'positive' (仅preset模式)")
        print("   - duration: 持续时间（秒）")
        print("\n示例:")
        print("   python main.py random")
        print("   python main.py preset negative 30")
        print("   python main.py preset mixed 45")
        print()
    
    @staticmethod
    def print_behavior_log(player_id: str, action: str):
        """打印玩家行为日志"""
        print(f"📝 玩家行为: {player_id} - {action}")
    
    @staticmethod
    def print_trigger_alert(player_id: str):
        """打印触发警报信息"""
        print(f"⚠️  触发监控阈值: 玩家 {player_id} 行为触发")
    
    @staticmethod
    def print_reset_counter(player_id: str):
        """打印重置计数器信息"""
        print(f"🔄 已重置玩家 {player_id} 的负面行为计数")
    
    @staticmethod
    def print_reset_count(player_id: str):
        """打印重置计数器信息（别名）"""
        print(f"🔄 已重置玩家 {player_id} 的负面行为计数")
    
    @staticmethod
    def print_dataset_loading(dataset_type: str):
        """打印数据集加载信息"""
        print(f"📦 加载预设数据集 (类型: {dataset_type})...")
    
    @staticmethod
    def print_dataset_generated(num_players: int):
        """打印数据集生成信息"""
        print(f"✅ 已生成 {num_players} 个玩家的行为数据")
    
    @staticmethod
    def print_unsupported_mode(mode: str):
        """打印不支持的模式错误"""
        print(f"❌ 不支持的模式: {mode}，请使用 'random' 或 'preset'")
    
    @staticmethod
    def print_session_start(duration: int, mode: str):
        """打印会话开始信息"""
        print(f"\n🚀 开始模拟监控会话 (持续 {duration} 秒, 模式: {mode})...")
    
    @staticmethod
    def print_session_end():
        """打印会话结束信息"""
        print("\n✅ 监控会话结束")
        print("\n🎯 系统演示完成!")
    
    @staticmethod
    def print_dataset_info(dataset_type: str, num_players: int):
        """打印数据集信息"""
        print(f"📦 加载预设数据集 (类型: {dataset_type})...")
        print(f"✅ 已生成 {num_players} 个玩家的行为数据")
    
    @staticmethod
    def print_player_processing(player_id: str):
        """打印玩家处理信息"""
        print(f"\n👤 处理玩家: {player_id}")
    
    @staticmethod
    def print_team_activation(player_id: str):
        """打印团队激活信息"""
        print(f"\n🤖 启动多智能体团队，为玩家 {player_id} 进行分析和干预...")
    
    @staticmethod
    def print_error(message: str):
        """打印错误信息"""
        print(f"❌ {message}")
    
    @staticmethod
    def print_success(message: str):
        """打印成功信息"""
        print(f"✅ {message}")