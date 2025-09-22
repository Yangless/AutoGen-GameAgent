# -*- coding: utf-8 -*-
"""
体力引导Agent测试脚本
测试streamlit_dashboard.py中的问题代码段和stamina_guide_agent.py的工具调用功能
"""

import asyncio
import json
from datetime import datetime
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from game_monitoring.agents.stamina_guide_agent import create_stamina_guide_agent
from game_monitoring.tools.stamina_guide_tool import (
    get_player_inventory_status,
    execute_personalized_guidance_popup
)

def test_single_tool_calls():
    """
    测试单个工具调用是否正确执行
    """
    print("=== 测试单个工具调用 ===")
    
    # 测试1: 测试get_player_inventory_status工具
    print("\n1. 测试 get_player_inventory_status 工具:")
    try:
        result1 = get_player_inventory_status("test_player_001")
        print(f"✅ 工具调用成功")
        print(f"返回结果: {result1[:200]}..." if len(result1) > 200 else f"返回结果: {result1}")
        
        # 验证返回的JSON格式
        parsed_result = json.loads(result1)
        print(f"✅ JSON解析成功，包含字段: {list(parsed_result.keys())}")
    except Exception as e:
        print(f"❌ 工具调用失败: {e}")
    
    # 测试2: 测试execute_personalized_guidance_popup工具
    print("\n2. 测试 execute_personalized_guidance_popup 工具:")
    try:
        result2 = execute_personalized_guidance_popup("test_player_001")
        print(f"✅ 工具调用成功")
        print(f"返回结果: {result2[:200]}..." if len(result2) > 200 else f"返回结果: {result2}")
        
        # 验证返回的JSON格式
        parsed_result = json.loads(result2)
        print(f"✅ JSON解析成功，状态: {parsed_result.get('status')}")
    except Exception as e:
        print(f"❌ 工具调用失败: {e}")

async def test_agent_with_different_messages():
    """
    测试不同的guide_message是否会正确返回
    """
    print("\n=== 测试Agent处理不同消息 ===")
    
    # 创建Agent实例
    try:
        stamina_agent = create_stamina_guide_agent()
        print("✅ Agent创建成功")
    except Exception as e:
        print(f"❌ Agent创建失败: {e}")
        return
    
    # 测试不同的消息
    test_messages = [
        "玩家test_player_001体力耗尽次数达到阈值",
        "玩家player_123需要体力引导",
        "体力不足，请提供引导建议",
        "玩家user_456的体力已经用完了"
    ]
    
    for i, guide_message in enumerate(test_messages, 1):
        print(f"\n{i}. 测试消息: '{guide_message}'")
        try:
            # 创建TextMessage实例
            message = TextMessage(content=guide_message, source="user")
            print(f"📤 发送消息给体力引导Agent")
            
            # 创建取消令牌
            cancellation_token = CancellationToken()
            
            # 使用on_messages方法处理消息
            response = await stamina_agent.on_messages([message], cancellation_token)
            print(f"📥 收到Agent响应")
            
            # 分析响应
            if response:
                print(f"✅ Agent响应成功")
                print(f"响应类型: {type(response)}")
                if hasattr(response, 'messages') and response.messages:
                    for msg in response.messages:
                        print(f"消息内容: {str(msg)[:200]}..." if len(str(msg)) > 200 else f"消息内容: {str(msg)}")
                else:
                    print(f"响应内容: {str(response)[:200]}..." if len(str(response)) > 200 else f"响应内容: {str(response)}")
            else:
                print(f"⚠️ Agent返回空响应")
                
        except Exception as e:
            print(f"❌ Agent处理消息失败: {e}")
            import traceback
            print(f"错误详情: {traceback.format_exc()}")
        
        print("-" * 50)

async def test_streamlit_code_segment():
    """
    测试从streamlit_dashboard.py提取的代码段
    """
    print("\n=== 测试Streamlit代码段 ===")
    
    # 模拟streamlit session state
    class MockSessionState:
        def __init__(self):
            self.current_player_id = "test_player_streamlit"
    
    # 模拟st对象
    class MockSt:
        def __init__(self):
            self.session_state = MockSessionState()
    
    st = MockSt()
    
    # 模拟add_stamina_guide_log函数
    def add_stamina_guide_log(message):
        print(f"[LOG] {message}")
    
    # 执行提取的代码段
    try:
        add_stamina_guide_log("🚨 检测到体力耗尽模式，触发引导Agent")
        
        # 触发体力引导Agent
        from game_monitoring.agents.stamina_guide_agent import create_stamina_guide_agent
        from autogen_agentchat.messages import TextMessage
        from autogen_core import CancellationToken
        
        # 使用工厂函数创建Agent实例
        stamina_agent = create_stamina_guide_agent()
        
        # 构建简单的引导请求消息，让Agent自己获取背包信息
        guide_message = f"玩家{st.session_state.current_player_id}体力耗尽次数达到阈值"
        
        # 使用Agent处理引导请求 - 符合Autogen最佳实践
        async def call_agent():
            # 创建TextMessage实例，符合Autogen v0.4规范
            message = TextMessage(content=guide_message, source="user")
            add_stamina_guide_log("📤 发送消息给体力引导Agent")
            
            # 创建取消令牌
            cancellation_token = CancellationToken()
            
            # 使用on_messages方法处理消息，这是Autogen v0.4的标准方式
            response = await stamina_agent.on_messages([message], cancellation_token)
            add_stamina_guide_log("📥 收到Agent响应")
            return response
        
        # 执行异步调用
        response = await call_agent()
        
        print("✅ Streamlit代码段执行成功")
        if response:
            print(f"响应类型: {type(response)}")
            print(f"响应内容: {str(response)[:300]}..." if len(str(response)) > 300 else f"响应内容: {str(response)}")
        else:
            print("⚠️ 返回空响应")
            
    except Exception as e:
        print(f"❌ Streamlit代码段执行失败: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")

async def main():
    """
    主测试函数
    """
    print("开始体力引导Agent测试")
    print(f"测试时间: {datetime.now()}")
    print("=" * 60)
    
    # 测试1: 单个工具调用
    test_single_tool_calls()
    
    # 测试2: Agent处理不同消息
    await test_agent_with_different_messages()
    
    # 测试3: Streamlit代码段
    await test_streamlit_code_segment()
    
    print("\n=" * 60)
    print("测试完成")

if __name__ == "__main__":
    # 运行异步测试
    asyncio.run(main())