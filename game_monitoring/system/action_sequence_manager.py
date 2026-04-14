# -*- coding: utf-8 -*-
"""
动作序列管理器
管理用户点击的原子动作序列，并协调规则引擎分析和智能体触发
"""

import asyncio
from typing import List, Dict, Any, Protocol

from ..monitoring.behavior_monitor import BehaviorMonitor
from ..ui.interactive_ui import InteractiveActionUI


class MonitoringTeam(Protocol):
    async def trigger_analysis_and_intervention(self, player_id: str, monitor: Any):
        ...


class ActionSequenceManager:
    """
    动作序列管理器
    
    负责协调以下流程：
    1. 用户通过UI点击原子动作
    2. 动作序列传递给BehaviorMonitor进行规则引擎分析
    3. 如果触发高层级场景，启动相应的智能体团队
    """
    
    def __init__(self, monitor: BehaviorMonitor, team: MonitoringTeam):
        self.monitor = monitor
        self.team = team
        self.ui = InteractiveActionUI()
        self.current_player_id = "player_001"
        self.session_active = False
        
    async def start_interactive_session(self):
        """启动交互式会话"""
        print("\n" + "="*60)
        print("🎮 新一代游戏监控系统 - 动态触发模式")
        print("="*60)
        print("\n📋 系统说明:")
        print("   • 点击原子动作模拟玩家行为")
        print("   • 规则引擎实时分析动作序列")
        print("   • 自动触发相应的智能体干预")
        print("   • 实现 A(原子动作) -> B(规则引擎) -> C(智能体) 流程")
        print("-" * 60)
        
        self.session_active = True
        
        # 启动UI交互循环
        await self._run_enhanced_interactive_loop()
        
    async def _run_enhanced_interactive_loop(self):
        """运行增强的交互循环"""
        while self.session_active:
            self.ui.display_action_categories()
            
            try:
                choice = input("\n请选择操作 (0-8): ").strip()
                
                if choice == '0':
                    print("👋 退出交互式界面")
                    self.session_active = False
                    break
                elif choice == '1':
                    await self._handle_core_actions_with_analysis()
                elif choice == '2':
                    await self._handle_social_actions_with_analysis()
                elif choice == '3':
                    await self._handle_economic_actions_with_analysis()
                elif choice == '4':
                    await self._handle_meta_actions_with_analysis()
                elif choice == '5':
                    self.ui.display_current_sequence()
                elif choice == '6':
                    await self._analyze_and_trigger_agents()
                elif choice == '7':
                    self._clear_current_sequence()
                elif choice == '8':
                    await self._simulate_preset_scenario()
                else:
                    print("❌ 无效选择，请重新输入")
                    
                if choice != '0':
                    input("\n按回车键继续...")
                    
            except KeyboardInterrupt:
                print("\n👋 用户中断，退出程序")
                self.session_active = False
                break
            except Exception as e:
                print(f"❌ 发生错误: {str(e)}")
                
    async def _handle_core_actions_with_analysis(self):
        """处理核心游戏动作并进行实时分析"""
        self.ui.display_core_actions()
        try:
            action_choice = int(input("\n请选择动作编号: ")) - 1
            if 0 <= action_choice < len(self.ui.action_definitions.core_game_actions):
                action = self.ui.action_definitions.core_game_actions[action_choice]
                await self._process_action_with_analysis(action)
            else:
                print("❌ 无效的动作编号")
        except ValueError:
            print("❌ 请输入有效的数字")
            
    async def _handle_social_actions_with_analysis(self):
        """处理社交动作并进行实时分析"""
        self.ui.display_social_actions()
        try:
            action_choice = int(input("\n请选择动作编号: ")) - 1
            if 0 <= action_choice < len(self.ui.action_definitions.social_actions):
                action = self.ui.action_definitions.social_actions[action_choice]
                await self._process_action_with_analysis(action)
            else:
                print("❌ 无效的动作编号")
        except ValueError:
            print("❌ 请输入有效的数字")
            
    async def _handle_economic_actions_with_analysis(self):
        """处理经济动作并进行实时分析"""
        self.ui.display_economic_actions()
        try:
            action_choice = int(input("\n请选择动作编号: ")) - 1
            if 0 <= action_choice < len(self.ui.action_definitions.economic_actions):
                action = self.ui.action_definitions.economic_actions[action_choice]
                await self._process_action_with_analysis(action)
            else:
                print("❌ 无效的动作编号")
        except ValueError:
            print("❌ 请输入有效的数字")
            
    async def _handle_meta_actions_with_analysis(self):
        """处理元数据动作并进行实时分析"""
        self.ui.display_meta_actions()
        try:
            action_choice = int(input("\n请选择动作编号: ")) - 1
            if 0 <= action_choice < len(self.ui.action_definitions.meta_actions):
                action = self.ui.action_definitions.meta_actions[action_choice]
                await self._process_action_with_analysis(action)
            else:
                print("❌ 无效的动作编号")
        except ValueError:
            print("❌ 请输入有效的数字")
            
    async def _process_action_with_analysis(self, action: str):
        """处理动作并进行实时分析"""
        # 提取动作名称（去掉参数部分）
        action_name = action.split('(')[0]
        
        # 添加到UI序列
        self.ui.add_action_to_sequence(action)
        
        # 添加到监控器并进行规则引擎分析
        triggered_scenarios = self.monitor.add_atomic_action(
            self.current_player_id, 
            action_name
        )
        
        # 如果触发了场景，启动智能体分析
        if triggered_scenarios:
            print(f"\n🚨 检测到 {len(triggered_scenarios)} 个触发场景:")
            for scenario in triggered_scenarios:
                print(f"   • {scenario['scenario']}: {scenario['trigger_reason']}")
            
            # 询问是否启动智能体分析
            response = input("\n是否立即启动智能体团队分析? (y/n): ").strip().lower()
            if response == 'y':
                await self._trigger_agent_analysis(triggered_scenarios)
        else:
            print("✅ 动作已记录，暂未触发特定场景")
            
    async def _analyze_and_trigger_agents(self):
        """分析当前序列并触发智能体"""
        if not self.ui.action_sequence:
            print("❌ 动作序列为空，无法分析")
            return
            
        # 重新分析整个序列
        triggered_scenarios = self.monitor.analyze_current_sequence(self.current_player_id)
        
        if triggered_scenarios:
            print(f"\n🚨 序列分析结果: 检测到 {len(triggered_scenarios)} 个场景")
            for scenario in triggered_scenarios:
                print(f"   • {scenario['scenario']}: {scenario['trigger_reason']}")
            
            await self._trigger_agent_analysis(triggered_scenarios)
        else:
            print("✅ 当前序列未触发任何特定场景")

    def _clear_current_sequence(self):
        """同步清空 UI 和监控器中的当前序列。"""
        self.ui.clear_sequence()
        self.monitor.clear_player_sequence(self.current_player_id)
            
    async def _trigger_agent_analysis(self, scenarios: List[Dict[str, str]]):
        """触发智能体团队分析"""
        print(f"\n🤖 启动智能体团队分析...")
        
        # 构建分析任务描述
        scenario_summary = "\n".join([f"- {s['scenario']}: {s['trigger_reason']}" for s in scenarios])
        
        # 获取玩家动作历史
        action_history = "\n".join([
            f"- [{a['timestamp'].strftime('%H:%M:%S')}] {a['action']}"
            for a in self.ui.action_sequence[-10:]  # 最近10个动作
        ])
        
        task = f"""
        **智能体团队紧急分析任务**
        
        **玩家ID:** {self.current_player_id}
        
        **触发场景:**
        {scenario_summary}
        
        **近期动作历史:**
        {action_history}
        
        **分析要求:**
        请基于规则引擎检测到的场景和玩家动作序列，进行深度分析并提供相应的干预建议。
        这是新一代动态触发系统的实际运行，请展示多智能体协作的专业能力。
        """
        
        # 启动智能体团队分析
        await self.team.trigger_analysis_and_intervention(self.current_player_id, self.monitor)
        
    async def _simulate_preset_scenario(self):
        """模拟预设场景"""
        print("\n🎯 预设场景模拟:")
        print("1. 玩家流失风险场景")
        print("2. 游戏挫败情绪场景")
        print("3. 高价值玩家场景")
        print("4. 疑似机器人场景")
        
        try:
            scenario_choice = int(input("\n请选择场景 (1-4): "))
            
            if scenario_choice == 1:
                await self._simulate_churn_risk_scenario()
            elif scenario_choice == 2:
                await self._simulate_frustration_scenario()
            elif scenario_choice == 3:
                await self._simulate_high_value_scenario()
            elif scenario_choice == 4:
                await self._simulate_bot_scenario()
            else:
                print("❌ 无效的场景选择")
                
        except ValueError:
            print("❌ 请输入有效的数字")
            
    async def _simulate_churn_risk_scenario(self):
        """模拟玩家流失风险场景"""
        print("\n🔄 正在模拟玩家流失风险场景...")
        
        # 模拟一系列导致流失风险的动作
        churn_actions = [
            "sell_item", "sell_item", "sell_item", "sell_item",  # 批量出售
            "cancel_auto_renew",  # 取消自动续费
            "click_exit_game_button"  # 点击退出
        ]
        
        for action in churn_actions:
            self.ui.add_action_to_sequence(f"{action}()")
            triggered_scenarios = self.monitor.add_atomic_action(self.current_player_id, action)
            print(f"   添加动作: {action}")
            await asyncio.sleep(0.5)  # 模拟时间间隔
            
        # 触发分析
        final_scenarios = self.monitor.analyze_current_sequence(self.current_player_id)
        if final_scenarios:
            await self._trigger_agent_analysis(final_scenarios)
            
    async def _simulate_frustration_scenario(self):
        """模拟游戏挫败情绪场景"""
        print("\n😤 正在模拟游戏挫败情绪场景...")
        
        frustration_actions = [
            "enter_dungeon", "complete_dungeon",  # 失败的副本
            "enter_dungeon", "complete_dungeon",  # 再次失败
            "lose_pvp", "lose_pvp", "lose_pvp"  # 连续PVP失败
        ]
        
        for action in frustration_actions:
            self.ui.add_action_to_sequence(f"{action}()")
            # 为失败动作添加特殊参数
            params = {}
            if action == "complete_dungeon":
                params = {"status": "failure"}
            
            triggered_scenarios = self.monitor.add_atomic_action(self.current_player_id, action, params)
            print(f"   添加动作: {action} {params}")
            await asyncio.sleep(0.5)
            
        final_scenarios = self.monitor.analyze_current_sequence(self.current_player_id)
        if final_scenarios:
            await self._trigger_agent_analysis(final_scenarios)
            
    async def _simulate_high_value_scenario(self):
        """模拟高价值玩家场景"""
        print("\n💎 正在模拟高价值玩家场景...")
        
        high_value_actions = [
            "make_payment",  # 充值
            "recruit_hero",  # 招募传说英雄
            "complete_dungeon"  # 困难副本成功
        ]
        
        for action in high_value_actions:
            params = {}
            if action == "make_payment":
                params = {"amount": 100, "product_id": "premium_pack"}
            elif action == "recruit_hero":
                params = {"rarity": "legendary"}
            elif action == "complete_dungeon":
                params = {"status": "success", "difficulty": "hard"}
                
            self.ui.add_action_to_sequence(f"{action}()")
            triggered_scenarios = self.monitor.add_atomic_action(self.current_player_id, action, params)
            print(f"   添加动作: {action} {params}")
            await asyncio.sleep(0.5)
            
        final_scenarios = self.monitor.analyze_current_sequence(self.current_player_id)
        if final_scenarios:
            await self._trigger_agent_analysis(final_scenarios)
            
    async def _simulate_bot_scenario(self):
        """模拟疑似机器人场景"""
        print("\n🤖 正在模拟疑似机器人场景...")
        
        # 快速连续动作模拟机器人行为
        bot_actions = ["login", "enter_dungeon", "attack_npc_tribe", "sell_item", "logout"] * 3
        
        for action in bot_actions:
            self.ui.add_action_to_sequence(f"{action}()")
            triggered_scenarios = self.monitor.add_atomic_action(self.current_player_id, action)
            print(f"   添加动作: {action}")
            await asyncio.sleep(0.1)  # 极短间隔模拟机器人
            
        final_scenarios = self.monitor.analyze_current_sequence(self.current_player_id)
        if final_scenarios:
            await self._trigger_agent_analysis(final_scenarios)


if __name__ == "__main__":
    # 测试动作序列管理器
    from autogen_core import SingleThreadedAgentRuntime

    from ..monitoring.behavior_monitor import BehaviorMonitor
    from ..team.team_manager import GameMonitoringTeamV2
    from config import custom_model_client
    
    async def test_manager():
        monitor = BehaviorMonitor()
        team = GameMonitoringTeamV2(
            model_client=custom_model_client,
            runtime=SingleThreadedAgentRuntime(),
        )
        manager = ActionSequenceManager(monitor, team)
        
        await manager.start_interactive_session()
    
    asyncio.run(test_manager())
