import asyncio
import sys
from game_monitoring.system import GamePlayerMonitoringSystem

async def main(mode: str = "random", dataset_type: str = "mixed", duration: int = 60):
    """
    主函数
    
    Args:
        mode: 数据生成模式 - "random" 随机生成 或 "preset" 预设序列
        dataset_type: 当mode="preset"时，指定数据集类型（"mixed", "negative", "positive"）
        duration: 会话持续时间（秒）
    """
    print("=" * 50)
    print("🎮 游戏玩家实时行为监控助手")
    print("=" * 50)
    
    print(f"📋 运行参数:")
    print(f"   - 数据模式: {mode}")
    if mode == "preset":
        print(f"   - 数据集类型: {dataset_type}")
    print(f"   - 持续时间: {duration}秒")
    print("-" * 50)
    
    system = GamePlayerMonitoringSystem()
    await system.simulate_monitoring_session(duration_seconds=duration, mode=mode, dataset_type=dataset_type)
    print("\n🎯 系统演示完成!")

def run_demo():
    """
    演示函数，展示两种模式的使用
    """
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        dataset_type = sys.argv[2] if len(sys.argv) > 2 else "mixed"
        duration = int(sys.argv[3]) if len(sys.argv) > 3 else 60
    else:
        # 默认演示随机模式
        mode = "random"
        dataset_type = "mixed"
        duration = 60
        
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
    
    asyncio.run(main(mode, dataset_type, duration))

if __name__ == "__main__":
    run_demo()