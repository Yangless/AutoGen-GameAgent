# -*- coding: utf-8 -*-
"""
交互式UI界面
支持用户点击原子动作来模拟玩家行为序列
"""

import asyncio
from typing import List, Dict, Any
from datetime import datetime
from ..simulator.player_behavior import PlayerActionDefinitions
from ..simulator.behavior_simulator import PlayerBehaviorRuleEngine


class InteractiveActionUI:
    """
    交互式动作UI界面
    展示原子动作列表，支持用户点击模拟动作序列
    """
    
    def __init__(self):
        self.action_definitions = PlayerActionDefinitions()
        self.rule_engine = PlayerBehaviorRuleEngine()
        self.current_player_id = "player_001"
        self.action_sequence: List[Dict[str, Any]] = []
        
    def display_action_categories(self):
        """显示动作分类菜单"""
        print("\n" + "="*60)
        print("🎮 游戏玩家行为模拟器 - 原子动作界面")
        print("="*60)
        print("\n📋 可用动作分类:")
        print("1. 核心游戏动作 (Core Game Actions)")
        print("2. 社交动作 (Social Actions)")
        print("3. 经济动作 (Economic Actions)")
        print("4. 元数据动作 (Meta Actions)")
        print("5. 查看当前动作序列")
        print("6. 分析动作序列并触发规则引擎")
        print("7. 清空动作序列")
        print("8. 模拟预设场景")
        print("0. 退出")
        
    def display_core_actions(self):
        """显示核心游戏动作"""
        print("\n🎯 核心游戏动作:")
        for i, action in enumerate(self.action_definitions.core_game_actions, 1):
            print(f"{i:2d}. {action}")
            
    def display_social_actions(self):
        """显示社交动作"""
        print("\n👥 社交动作:")
        for i, action in enumerate(self.action_definitions.social_actions, 1):
            print(f"{i:2d}. {action}")
            
    def display_economic_actions(self):
        """显示经济动作"""
        print("\n💰 经济动作:")
        for i, action in enumerate(self.action_definitions.economic_actions, 1):
            print(f"{i:2d}. {action}")
            
    def display_meta_actions(self):
        """显示元数据动作"""
        print("\n⚙️ 元数据动作:")
        for i, action in enumerate(self.action_definitions.meta_actions, 1):
            print(f"{i:2d}. {action}")
            
    def add_action_to_sequence(self, action_name: str, params: Dict[str, Any] = None):
        """添加动作到序列"""
        action_data = {
            'action': action_name.split('(')[0],  # 提取动作名称
            'params': params or {},
            'timestamp': datetime.now(),
            'player_id': self.current_player_id
        }
        self.action_sequence.append(action_data)
        print(f"✅ 已添加动作: {action_name}")
        
    def display_current_sequence(self):
        """显示当前动作序列"""
        print("\n📝 当前动作序列:")
        if not self.action_sequence:
            print("   (空序列)")
            return
            
        for i, action in enumerate(self.action_sequence, 1):
            timestamp = action['timestamp'].strftime('%H:%M:%S')
            print(f"{i:2d}. [{timestamp}] {action['action']} - 玩家: {action['player_id']}")
            
    def analyze_sequence_with_rules(self):
        """使用规则引擎分析动作序列"""
        if not self.action_sequence:
            print("❌ 动作序列为空，无法分析")
            return []
            
        print("\n🔍 正在使用规则引擎分析动作序列...")
        triggered_scenarios = []
        
        # 检查各种规则
        rules_to_check = [
            ('登录行为', self.rule_engine.check_login),
            ('进入副本', self.rule_engine.check_enter_dungeon),
            ('世界聊天', self.rule_engine.check_open_world_chat),
            ('困难副本成功', self.rule_engine.check_successful_hard_dungeon_completion),
            ('升级成功', self.rule_engine.check_successful_upgrade),
            ('传说英雄招募', self.rule_engine.check_legendary_hero_recruitment),
            ('连续副本失败', lambda actions: self.rule_engine.check_consecutive_dungeon_failures(actions, 3)),
            ('多次PVP失败', lambda actions: self.rule_engine.check_multiple_pvp_losses(actions, 3)),
            ('连续招募失败', lambda actions: self.rule_engine.check_consecutive_recruit_failures(actions, 5)),
            ('批量出售物品', lambda actions: self.rule_engine.check_bulk_item_sell(actions, 3)),
            ('异常高频动作', lambda actions: self.rule_engine.check_abnormally_high_action_rate(actions, 1, 5))
        ]
        
        print("\n📊 规则检查结果:")
        for rule_name, rule_func in rules_to_check:
            try:
                result = rule_func(self.action_sequence)
                if result:
                    print(f"✅ {rule_name}: 触发 ({len(result)} 个匹配动作)")
                    triggered_scenarios.append({
                        'rule_name': rule_name,
                        'matched_actions': result,
                        'scenario_type': self._map_rule_to_scenario(rule_name)
                    })
                else:
                    print(f"⭕ {rule_name}: 未触发")
            except Exception as e:
                print(f"❌ {rule_name}: 检查失败 - {str(e)}")
                
        return triggered_scenarios
        
    def _map_rule_to_scenario(self, rule_name: str) -> str:
        """将规则名称映射到高层级场景"""
        scenario_mapping = {
            '登录行为': '正常游戏活跃',
            '进入副本': '副本挑战行为',
            '世界聊天': '社交互动活跃',
            '困难副本成功': '高技能玩家表现',
            '升级成功': '角色成长积极',
            '传说英雄招募': '高价值消费行为',
            '连续副本失败': '游戏挫败感风险',
            '多次PVP失败': 'PVP挫败情绪',
            '连续招募失败': '抽卡挫败风险',
            '批量出售物品': '玩家流失风险',
            '异常高频动作': '疑似机器人行为'
        }
        return scenario_mapping.get(rule_name, '未知场景类型')
        
    def clear_sequence(self):
        """清空动作序列"""
        self.action_sequence.clear()
        print("🗑️ 动作序列已清空")
        
    async def run_interactive_session(self):
        """运行交互式会话"""
        while True:
            self.display_action_categories()
            
            try:
                choice = input("\n请选择操作 (0-7): ").strip()
                
                if choice == '0':
                    print("👋 退出交互式界面")
                    break
                elif choice == '1':
                    self._handle_core_actions()
                elif choice == '2':
                    self._handle_social_actions()
                elif choice == '3':
                    self._handle_economic_actions()
                elif choice == '4':
                    self._handle_meta_actions()
                elif choice == '5':
                    self.display_current_sequence()
                elif choice == '6':
                    scenarios = self.analyze_sequence_with_rules()
                    if scenarios:
                        print(f"\n🚨 检测到 {len(scenarios)} 个触发场景，可以启动智能体分析...")
                        # 这里可以集成到现有的智能体触发流程
                elif choice == '7':
                    self.clear_sequence()
                else:
                    print("❌ 无效选择，请重新输入")
                    
                input("\n按回车键继续...")
                
            except KeyboardInterrupt:
                print("\n👋 用户中断，退出程序")
                break
            except Exception as e:
                print(f"❌ 发生错误: {str(e)}")
                
    def _handle_core_actions(self):
        """处理核心游戏动作选择"""
        self.display_core_actions()
        try:
            action_choice = int(input("\n请选择动作编号: ")) - 1
            if 0 <= action_choice < len(self.action_definitions.core_game_actions):
                action = self.action_definitions.core_game_actions[action_choice]
                self.add_action_to_sequence(action)
            else:
                print("❌ 无效的动作编号")
        except ValueError:
            print("❌ 请输入有效的数字")
            
    def _handle_social_actions(self):
        """处理社交动作选择"""
        self.display_social_actions()
        try:
            action_choice = int(input("\n请选择动作编号: ")) - 1
            if 0 <= action_choice < len(self.action_definitions.social_actions):
                action = self.action_definitions.social_actions[action_choice]
                self.add_action_to_sequence(action)
            else:
                print("❌ 无效的动作编号")
        except ValueError:
            print("❌ 请输入有效的数字")
            
    def _handle_economic_actions(self):
        """处理经济动作选择"""
        self.display_economic_actions()
        try:
            action_choice = int(input("\n请选择动作编号: ")) - 1
            if 0 <= action_choice < len(self.action_definitions.economic_actions):
                action = self.action_definitions.economic_actions[action_choice]
                self.add_action_to_sequence(action)
            else:
                print("❌ 无效的动作编号")
        except ValueError:
            print("❌ 请输入有效的数字")
            
    def _handle_meta_actions(self):
        """处理元数据动作选择"""
        self.display_meta_actions()
        try:
            action_choice = int(input("\n请选择动作编号: ")) - 1
            if 0 <= action_choice < len(self.action_definitions.meta_actions):
                action = self.action_definitions.meta_actions[action_choice]
                self.add_action_to_sequence(action)
            else:
                print("❌ 无效的动作编号")
        except ValueError:
            print("❌ 请输入有效的数字")


if __name__ == "__main__":
    # 测试交互式UI
    ui = InteractiveActionUI()
    asyncio.run(ui.run_interactive_session())