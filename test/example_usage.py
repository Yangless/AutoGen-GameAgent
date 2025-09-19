#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
军令生成新架构使用示例

这个示例展示了如何使用重构后的军令生成系统：
- LLM作为内容生成引擎
- Agent作为任务执行者
- 工具函数作为中间层
"""

import asyncio
from autogen_agentchat.messages import TextMessage
from game_monitoring.tools.military_order_tool import (
    create_llm_content_generator,
    generate_military_order_with_llm,
    generate_batch_military_orders
)
from game_monitoring.agents.military_order_agent import create_military_order_agent
import trace

async def example_direct_llm_usage():
    """
    示例1: 直接使用LLM生成引擎
    适用场景: 需要直接控制生成过程的情况
    """
    print("\n=== 示例1: 直接使用LLM生成引擎 ===")
    
    # 创建LLM生成引擎
    llm_generator = create_llm_content_generator()
    
    # 构建详细的生成提示
    prompt = """
    请为玩家"战神无敌"生成一份个性化军令。
    玩家信息：
    - 主力队伍等级：55级
    - 队伍体力：85%
    - 特殊能力：擅长攻城作战
    
    请生成正式的军令文档。
    """
    
    try:
        user_message = TextMessage(content=prompt, source="user")
        response = await llm_generator.on_messages([user_message], cancellation_token=None)
        
        if response and response.chat_message:
            print("✅ LLM直接生成成功")
            print(f"生成内容: {response.chat_message.content[:200]}...")
        else:
            print("❌ LLM生成失败")
    except Exception as e:
        print(f"❌ 异常: {e}")


def example_tool_function_usage():
    """
    示例2: 使用工具函数
    适用场景: 需要结构化输出和错误处理的情况
    """
    print("\n=== 示例2: 使用工具函数 ===")
    
    # 玩家数据
    player_data = {
        "player_id": "战神无敌",
        "player_name": "战神无敌",
        "teams": [
            {"team_number": 1, "level": 55, "stamina": 85},
            {"team_number": 2, "level": 52, "stamina": 90}
        ]
    }
    
    try:
        result = generate_military_order_with_llm(
            player_data=player_data,
            context="攻城作战",
            special_requirements="注重团队配合"
        )
        
        print("✅ 工具函数调用成功")
        print(f"玩家: {result['player_name']}")
        print(f"军令长度: {len(result['military_order'])}字符")
        print(f"队伍分析: {len(result['team_analysis'])}支队伍")
        
    except Exception as e:
        print(f"❌ 工具函数调用失败: {e}")


async def example_agent_usage():
    """
    示例3: 使用Agent执行任务
    适用场景: 需要智能任务理解和执行的情况
    """
    print("\n=== 示例3: 使用Agent执行任务 ===")
    
    # 创建军令生成Agent
    agent = create_military_order_agent()
    
    # 简单的任务指令
    task_instruction = """
    请为玩家"龙战天下"生成军令。
    他有3支队伍：60级主力队、55级副队、50级辅助队。
    当前正在准备大型攻城战。
    """
    
    try:
        user_message = TextMessage(content=task_instruction, source="user")
        response = await agent.on_messages([user_message], cancellation_token=None)
        
        if response and response.chat_message:
            print("✅ Agent任务执行成功")
            print(f"Agent回复长度: {len(response.chat_message.content)}字符")
            # 尝试解析JSON回复
            import json
            try:
                result = json.loads(response.chat_message.content)
                print(f"解析结果 - 玩家: {result.get('player_name', 'N/A')}")
                print(f"解析结果 - 状态: {result.get('status', 'N/A')}")
            except:
                print("回复不是JSON格式，直接显示文本内容")
        else:
            print("❌ Agent任务执行失败")
            
    except Exception as e:
        print(f"❌ Agent调用异常: {e}")


def example_batch_processing():
    """
    示例4: 批量处理
    适用场景: 需要为多个玩家生成军令的情况
    """
    print("\n=== 示例4: 批量处理 ===")
    
    # 多个玩家数据
    players_data = [
        {
            "player_id": "player_001",
            "player_name": "霸王无双",
            "teams": [{"team_number": 1, "level": 58, "stamina": 95}]
        },
        {
            "player_id": "player_002", 
            "player_name": "剑客行",
            "teams": [{"team_number": 1, "level": 53, "stamina": 80}]
        }
    ]
    
    try:
        results = generate_batch_military_orders(
            players_data=players_data,
            context="联盟战争",
            special_requirements="强调协同作战"
        )
        
        print(f"✅ 批量处理成功，生成了{len(results)}份军令")
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['player_name']}: {len(result['military_order'])}字符")
            
    except Exception as e:
        print(f"❌ 批量处理失败: {e}")


async def main():
    """
    主函数：运行所有示例
    """
    print("军令生成新架构使用示例")
    print("=" * 50)
    
    # 运行所有示例
    await example_direct_llm_usage()
    example_tool_function_usage()
    await example_agent_usage()
    example_batch_processing()
    
    print("\n=== 架构总结 ===")
    print("1. LLM生成引擎: 纯粹的内容创作，专注于文本生成质量")
    print("2. 工具函数: 封装业务逻辑，提供结构化接口")
    print("3. Agent智能体: 理解任务需求，智能选择工具执行")
    print("4. 批量处理: 支持大规模军令生成需求")
    print("\n新架构实现了职责分离，提高了系统的可维护性和扩展性！")


if __name__ == "__main__":
    asyncio.run(main())