#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的stamina_agent.run_stream调用
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from game_monitoring.agents.stamina_guide_agent import create_stamina_guide_agent

async def test_stamina_agent():
    """测试体力引导Agent的run_stream方法"""
    print("🧪 开始测试体力引导Agent...")
    
    try:
        # 创建Agent实例
        stamina_agent = create_stamina_guide_agent()
        print("✅ Agent创建成功")
        
        # 测试消息
        guide_message = "玩家孤独的凤凰战士体力耗尽次数达到阈值"
        print(f"📤 发送测试消息: {guide_message}")
        
        # 使用run_stream方法
        response_stream = stamina_agent.run_stream(task=guide_message)
        print("✅ run_stream调用成功，开始处理流式响应...")
        
        # 收集所有流式响应
        final_response = None
        response_count = 0
        
        async for response in response_stream:
            response_count += 1
            print(f"📥 收到响应 #{response_count}: {type(response)}")
            
            if hasattr(response, 'messages') and response.messages:
                # 获取最后一条消息作为最终响应
                final_response = response.messages[-1]
                print(f"  - 从messages获取: {type(final_response)}")
            elif hasattr(response, 'chat_message'):
                # 直接获取chat_message
                final_response = response.chat_message
                print(f"  - 从chat_message获取: {type(final_response)}")
            else:
                print(f"  - 响应属性: {dir(response)}")
        
        # 处理最终响应
        if final_response and hasattr(final_response, 'content'):
            response_text = final_response.content
            print(f"💡 最终响应内容: {response_text}")
            print("✅ 测试成功！")
        else:
            print(f"❌ 最终响应格式不正确: {type(final_response)}")
            if final_response:
                print(f"   响应属性: {dir(final_response)}")
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_stamina_agent())