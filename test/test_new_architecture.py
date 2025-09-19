#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新的军令生成架构

新架构说明：
1. LLM (create_llm_content_generator): 纯粹的内容生成引擎
2. Tool (generate_military_order_with_llm): Agent可调用的工具函数
3. Agent (MilitaryOrderAgent): 任务执行智能体
"""

import json
from game_monitoring.tools.military_order_tool import (
    generate_military_order_with_llm,
    create_llm_content_generator
)
from game_monitoring.agents.military_order_agent import create_military_order_agent
from autogen_agentchat.messages import TextMessage

def test_llm_content_generator():
    """测试纯粹的LLM内容生成引擎"""
    print("=== 测试1: LLM内容生成引擎 ===")
    
    # 创建LLM生成引擎
    llm_generator = create_llm_content_generator()
    
    # 直接给LLM一个生成军令的prompt
    prompt = """
请为玩家"龙傲天"生成一份个性化军令：

**玩家情况：**
- 主力队伍：50级，体力100%，可打12级地
- 预备兵：5000
- 携带道具：加速道具、攻击道具

**作战目标：**
- 事件：攻城战
- 时间：早上10点
- 目标坐标：(752, 613)
- 集结点：(732, 767)

请生成一份适合该玩家的个性化作战军令。
"""
    
    try:
        import asyncio
        
        async def call_llm():
            user_message = TextMessage(content=prompt, source="user")
            response = await llm_generator.on_messages([user_message], cancellation_token=None)
            return response
        
        response = asyncio.run(call_llm())
        
        if response and response.chat_message:
            print("✅ LLM生成成功")
            print(f"生成内容长度: {len(response.chat_message.content)}字符")
            print(f"内容预览: {response.chat_message.content[:100]}...")
        else:
            print("❌ LLM生成失败")
    except Exception as e:
        print(f"❌ LLM调用异常: {e}")

def test_tool_function():
    """测试工具函数"""
    print("\n=== 测试2: 工具函数 ===")
    
    try:
        # 调用工具函数
        result = generate_military_order_with_llm(
            player_name="龙傲天",
            player_id="longtian",
            team_levels=[50, 45, 40, 35],
            team_stamina=[100, 90, 80, 70],
            backpack_items=["加速道具", "攻击道具"],
            reserve_troops=5000
        )
        
        # 解析结果
        result_data = json.loads(result)
        print("✅ 工具函数调用成功")
        print(f"玩家: {result_data['player_name']}")
        print(f"军令长度: {len(result_data['military_order'])}字符")
        print(f"生成时间: {result_data['generated_at']}")
        
    except Exception as e:
        print(f"❌ 工具函数调用失败: {e}")

def test_agent_task_execution():
    """测试Agent任务执行"""
    print("\n=== 测试3: Agent任务执行 ===")
    
    try:
        # 创建Agent
        agent = create_military_order_agent()
        
        # 给Agent一个任务指令
        task_instruction = "请为玩家龙傲天生成一份个性化军令，他的主力队伍是50级。"
        
        import asyncio
        
        async def call_agent():
            user_message = TextMessage(content=task_instruction, source="user")
            response = await agent.on_messages([user_message], cancellation_token=None)
            return response
        
        response = asyncio.run(call_agent())
        
        if response and response.chat_message:
            print("✅ Agent任务执行成功")
            print(f"Agent回复: {response.chat_message.content}")
        else:
            print("❌ Agent任务执行失败")
            
    except Exception as e:
        print(f"❌ Agent调用异常: {e}")

def main():
    """主测试函数"""
    print("开始测试新的军令生成架构...\n")
    
    # 测试1: LLM内容生成引擎
    test_llm_content_generator()
    
    # 测试2: 工具函数
    test_tool_function()
    
    # 测试3: Agent任务执行
    test_agent_task_execution()
    
    print("\n=== 架构说明 ===")
    print("1. LLM引擎: 专注于内容生成，接收详细的prompt，输出军令文本")
    print("2. 工具函数: 封装LLM调用逻辑，处理数据转换和错误处理")
    print("3. Agent智能体: 理解任务需求，选择合适的工具，执行完整的任务流程")
    print("\n新架构的优势:")
    print("- 职责分离: LLM专注生成，Agent专注任务执行")
    print("- 可扩展性: 可以轻松添加新的工具和功能")
    print("- 可测试性: 每个组件都可以独立测试")
    print("- 可维护性: 代码结构清晰，易于理解和修改")

if __name__ == "__main__":
    main()