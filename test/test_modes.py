#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试两种数据生成模式的脚本
"""

import asyncio
from main import GamePlayerMonitoringSystem

async def test_random_mode():
    """测试随机生成模式"""
    print("\n" + "="*60)
    print("🎲 测试随机生成模式")
    print("="*60)
    
    system = GamePlayerMonitoringSystem()
    await system.simulate_monitoring_session(duration_seconds=10, mode="random")

async def test_preset_mode():
    """测试预设序列模式"""
    print("\n" + "="*60)
    print("📦 测试预设序列模式")
    print("="*60)
    
    system = GamePlayerMonitoringSystem()
    
    # 测试不同类型的数据集
    for dataset_type in ["negative", "positive", "mixed"]:
        print(f"\n🔍 测试数据集类型: {dataset_type}")
        print("-" * 40)
        await system.simulate_monitoring_session(
            duration_seconds=5, 
            mode="preset", 
            dataset_type=dataset_type
        )
        print("\n" + "⏸️ " * 20)

async def main():
    """主测试函数"""
    print("🧪 开始测试两种数据生成模式...")
    
    # 测试随机模式
    await test_random_mode()
    
    # 等待一下
    await asyncio.sleep(2)
    
    # 测试预设模式
    await test_preset_mode()
    
    print("\n✅ 所有测试完成!")

if __name__ == "__main__":
    asyncio.run(main())