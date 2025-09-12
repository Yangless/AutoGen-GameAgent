import random
import time
from datetime import datetime
from typing import Dict, List

from .player_behavior import PlayerBehavior


import time
from typing import List, Dict, Any

class PlayerBehaviorRuleEngine:
    """
    一个规则引擎，用于通过分析细粒度的玩家动作序列来识别高层级的行为场景。

    每个 `check_` 方法都对应一条触发规则，并返回一个列表，
    其中包含触发了该规则的具体动作。如果规则未被触发，则返回空列表。
    """
    
    def analyze_action_sequence(self, player_id: str, actions: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """分析玩家动作序列，返回触发的场景列表（基于最近三次行为）"""
        triggered_scenarios = []
        
        # 只分析最近三次行为
        recent_actions = actions[-3:] if len(actions) >= 3 else actions
        
        # 定义规则检查映射
        rules_to_check = [
            ('连续失败触发消极情绪', self._check_consecutive_failures, recent_actions),
            ('社交退出行为风险', self._check_social_withdrawal_risk, recent_actions),
            ('连续被攻击消极行为', self._check_consecutive_attacks, recent_actions),
            ('客服求助流失风险', self._check_support_contact_risk, recent_actions),
            ('游戏卸载流失风险', self._check_uninstall_risk, recent_actions),
            ('充值行为积极表现', self._check_payment_behavior, recent_actions),
            ('社交活跃表现', self._check_social_activity, recent_actions),
            ('游戏成就积极表现', self._check_achievement_behavior, recent_actions),
            ('异常高频操作', self._check_abnormal_frequency, recent_actions),
            ('资产处理风险', self._check_asset_disposal_risk, recent_actions)
        ]
        
        for scenario_name, rule_func, action_data in rules_to_check:
            trigger_result = rule_func(action_data)
            if trigger_result:
                triggered_scenarios.append({
                    'scenario': scenario_name,
                    'player_id': player_id,
                    'trigger_reason': trigger_result if isinstance(trigger_result, str) else f'规则引擎检测到{scenario_name}相关行为模式',
                    'trigger_actions': [a.get('action', '') for a in action_data]
                })
                
        return triggered_scenarios
    
    def _check_consecutive_failures(self, actions: List[Dict]) -> str:
        """检查连续失败三次触发消极情绪"""
        if len(actions) < 3:
            return ""
        
        failure_actions = ['complete_dungeon', 'recruit_hero', 'upgrade_skill', 'upgrade_building', 'lose_pvp']
        consecutive_failures = 0
        failure_details = []
        
        # 从最新的动作开始向前检查连续性
        for i in range(len(actions) - 1, -1, -1):
            action = actions[i]
            action_name = action.get('action', '')
            
            if action_name in failure_actions:
                status = action.get('params', {}).get('status', '')
                rarity = action.get('params', {}).get('rarity', '')
                
                # 判断是否为失败
                is_failure = (
                    status == 'fail' or 
                    action_name == 'lose_pvp' or
                    (action_name == 'recruit_hero' and rarity == 'common')
                )
                
                if is_failure:
                    consecutive_failures += 1
                    failure_details.insert(0, action_name)  # 插入到开头保持时间顺序
                else:
                    break  # 成功打断连续失败
            else:
                # 非相关动作不打断连续性，继续检查
                continue
        
        if consecutive_failures >= 2:
            return f"连续失败{consecutive_failures}次：{', '.join(failure_details[:3])}"
        return ""
    
    def _check_social_withdrawal_risk(self, actions: List[Dict]) -> str:
        """检查离开家族、删除好友、清理背包出现其中两个触发消极行为和流失风险"""
        withdrawal_actions = ['leave_family', 'remove_friend', 'clear_backpack']
        triggered_actions = []
        
        for action in actions:
            action_name = action.get('action', '')
            if action_name in withdrawal_actions:
                triggered_actions.append(action_name)
        
        if len(set(triggered_actions)) >= 2:  # 至少两种不同的退出行为
            return f"社交退出行为：{', '.join(set(triggered_actions))}"
        return ""
    
    def _check_consecutive_attacks(self, actions: List[Dict]) -> str:
        """检查连续3次被攻击触发消极行为"""
        if len(actions) < 3:
            return ""
        
        consecutive_attacks = 0
        
        # 从最新的动作开始向前检查连续性
        for i in range(len(actions) - 1, -1, -1):
            action = actions[i]
            action_name = action.get('action', '')
            
            if action_name == 'be_attacked':
                consecutive_attacks += 1
            else:
                # 其他动作打断连续被攻击
                break
        
        if consecutive_attacks >= 3:
            return f"连续被攻击{consecutive_attacks}次"
        return ""
    
    def _check_support_contact_risk(self, actions: List[Dict]) -> str:
        """检查联系客服触发流失风险"""
        for action in actions:
            if action.get('action') == 'contact_support':
                return "联系客服求助，可能遇到问题"
        return ""
    
    def _check_uninstall_risk(self, actions: List[Dict]) -> str:
        """检查卸载游戏触发流失风险"""
        for action in actions:
            if action.get('action') == 'uninstall_game':
                return "执行卸载游戏操作"
        return ""
    
    def _check_payment_behavior(self, actions: List[Dict]) -> str:
        """检查充值行为积极表现"""
        payment_actions = []
        for action in actions:
            action_name = action.get('action', '')
            if action_name in ['make_payment', 'buy_monthly_card', 'buy_item']:
                payment_actions.append(action_name)
        
        if payment_actions:
            return f"充值消费行为：{', '.join(set(payment_actions))}"
        return ""
    
    def _check_social_activity(self, actions: List[Dict]) -> str:
        """检查社交活跃表现"""
        social_actions = []
        for action in actions:
            action_name = action.get('action', '')
            if action_name in ['join_family', 'add_friend', 'send_chat_message']:
                social_actions.append(action_name)
        
        if social_actions:
            return f"社交活跃行为：{', '.join(set(social_actions))}"
        return ""
    
    def _check_achievement_behavior(self, actions: List[Dict]) -> str:
        """检查游戏成就积极表现"""
        achievement_actions = []
        for action in actions:
            action_name = action.get('action', '')
            status = action.get('params', {}).get('status', '')
            rarity = action.get('params', {}).get('rarity', '')
            difficulty = action.get('params', {}).get('difficulty', '')
            
            # 成功的高难度或高价值行为
            if (
                (action_name == 'complete_dungeon' and status == 'success' and difficulty == 'hard') or
                (action_name == 'recruit_hero' and rarity in ['rare', 'epic', 'legendary']) or
                (action_name in ['upgrade_skill', 'upgrade_building'] and status == 'success')
            ):
                achievement_actions.append(f"{action_name}({status or rarity or difficulty})")
        
        if achievement_actions:
            return f"游戏成就行为：{', '.join(achievement_actions)}"
        return ""
    
    def _check_abnormal_frequency(self, actions: List[Dict]) -> str:
        """检查异常高频操作"""
        if len(actions) == 3:
            # 检查是否为相同动作的高频重复
            action_names = [a.get('action', '') for a in actions]
            if len(set(action_names)) == 1 and action_names[0] not in ['login', 'logout']:
                return f"高频重复操作：{action_names[0]} x3"
        return ""
    
    def _check_asset_disposal_risk(self, actions: List[Dict]) -> str:
        """检查资产处理风险"""
        disposal_actions = []
        for action in actions:
            action_name = action.get('action', '')
            if action_name in ['sell_item', 'cancel_auto_renew', 'post_account_for_sale']:
                disposal_actions.append(action_name)
        
        if disposal_actions:
            return f"资产处理行为：{', '.join(set(disposal_actions))}"
        return ""
    
    def is_negative_behavior(self, action_name: str, simulator_instance) -> bool:
        """判断单个动作是否为消极行为"""
        # 基于PlayerBehaviorSimulator中定义的消极场景判断
        return action_name in simulator_instance.negative_scenarios
    
    def get_emotion_type_from_scenarios(self, triggered_scenarios: List[Dict[str, str]]) -> str:
        """根据触发的场景判断情绪类型"""
        if not triggered_scenarios:
            return "neutral"
        
        scenario_names = [s.get('scenario', '') for s in triggered_scenarios]
        
        # 定义场景优先级和对应的情绪类型
        emotion_mapping = {
            # 消极情绪场景（高优先级）
            '连续失败触发消极情绪': 'negative',
            '社交退出行为风险': 'negative', 
            '连续被攻击消极行为': 'negative',
            '客服求助流失风险': 'negative',
            '游戏卸载流失风险': 'negative',
            '资产处理风险': 'negative',
            # 异常行为场景（中优先级）
            '异常高频操作': 'abnormal',
            # 积极情绪场景（低优先级）
            '充值行为积极表现': 'positive',
            '社交活跃表现': 'positive',
            '游戏成就积极表现': 'positive'
        }
        
        # 按优先级顺序检查场景
        priority_order = ['negative', 'abnormal', 'positive']
        
        for emotion_type in priority_order:
            for scenario_name in scenario_names:
                if emotion_mapping.get(scenario_name) == emotion_type:
                    return emotion_type
        
        return "neutral"
    
    def analyze_single_action_emotion(self, action: str, context: Dict[str, Any] = None) -> str:
        """分析单个动作的情绪倾向（独立于序列分析）"""
        context = context or {}
        
        # 定义单个动作的情绪映射
        action_emotion_map = {
            # 明确的消极动作
            'click_exit_game_button': 'negative',
            'cancel_auto_renew': 'negative',
            'uninstall_game': 'negative',
            'contact_support': 'negative',  # 通常表示遇到问题
            'sell_item': 'negative',  # 可能表示资金紧张或准备离开
            'clear_backpack': 'negative',  # 可能表示准备离开
            'post_account_for_sale': 'negative',
            'leave_family': 'negative',  # 离开家族
            'remove_friend': 'negative',  # 删除好友
            'be_attacked': 'negative',  # 被攻击
            'lose_pvp': 'negative',  # PVP失败
            
            # 明确的积极动作
            'make_payment': 'positive',
            'buy_monthly_card': 'positive',
            'buy_item': 'positive',
            'receive_daily_reward': 'positive',
            'receive_event_reward': 'positive',
            'receive_praise': 'positive',
            'be_invited_to_family': 'positive',
            'add_friend': 'positive',
            'join_family': 'positive',
            
            # 中性动作（大部分游戏动作）
            'login': 'neutral',
            'logout': 'neutral',
            'enter_dungeon': 'neutral',
            'attack_player': 'neutral',
            'send_chat_message': 'neutral',
            'receive_chat_message': 'neutral',
            'recruit_hero': 'neutral',  # 需要根据结果判断
            'complete_dungeon': 'neutral',  # 需要根据结果判断
            'upgrade_skill': 'neutral',  # 需要根据结果判断
            'upgrade_building': 'neutral'  # 需要根据结果判断
        }
        
        return action_emotion_map.get(action, 'neutral')

    # --- 基础游戏行为检测 ---

    def check_login(self, actions: List[Dict]) -> List[Dict]:
        """规则: 记录到 login 动作。"""
        return [a for a in actions if a.get('action') == 'login']

    def check_enter_dungeon(self, actions: List[Dict]) -> List[Dict]:
        """规则: 记录到 enter_dungeon 动作。"""
        return [a for a in actions if a.get('action') == 'enter_dungeon']
    
    def check_open_world_chat(self, actions: List[Dict]) -> List[Dict]:
        """规则: 记录到 send_chat_message 且 channel 为 'world'。"""
        return [a for a in actions if a.get('action') == 'send_chat_message' and a.get('params', {}).get('channel') == 'world']

    # --- 积极情绪相关检测 ---

    def check_successful_hard_dungeon_completion(self, actions: List[Dict]) -> List[Dict]:
        """规则: 记录到 complete_dungeon 且 status='success' 且 difficulty='hard'。"""
        return [
            a for a in actions if a.get('action') == 'complete_dungeon' 
            and a.get('params', {}).get('status') == 'success'
            and a.get('params', {}).get('difficulty') == 'hard'
        ]

    def check_successful_upgrade(self, actions: List[Dict]) -> List[Dict]:
        """规则: 记录到 upgrade_skill 或 upgrade_building 且 status='success'。"""
        return [
            a for a in actions if a.get('action') in ['upgrade_skill', 'upgrade_building']
            and a.get('params', {}).get('status') == 'success'
        ]
        
    def check_legendary_hero_recruitment(self, actions: List[Dict]) -> List[Dict]:
        """规则: 记录到 recruit_hero 且 rarity='legendary'。"""
        return [
            a for a in actions if a.get('action') == 'recruit_hero'
            and a.get('params', {}).get('rarity') == 'legendary'
        ]

    # --- 消极情绪相关检测 ---

    def check_consecutive_dungeon_failures(self, actions: List[Dict], count: int = 2) -> List[Dict]:
        """规则: 短时间内连续记录到多次 complete_dungeon 且 status='fail'。"""
        failure_streak = []
        for action in actions:
            if action.get('action') == 'complete_dungeon' and action.get('params', {}).get('status') == 'fail':
                failure_streak.append(action)
                if len(failure_streak) >= count:
                    return failure_streak  # 找到满足条件的连续失败序列
            else:
                failure_streak = []  # 任何其他动作都会打断连续性
        return []

    def check_multiple_pvp_losses(self, actions: List[Dict], count: int = 2) -> List[Dict]:
        """规则: 短时间内记录到多次 lose_pvp 或 be_attacked (防守失败)。"""
        losses = [a for a in actions if a.get('action') in ['lose_pvp', 'be_attacked']]
        if len(losses) >= count:
            return losses
        return []

    def check_consecutive_recruit_failures(self, actions: List[Dict], count: int = 10) -> List[Dict]:
        """规则: 连续执行 recruit_hero 多次，但 rarity 均未达到 'rare' 或更高。"""
        failure_streak = []
        for action in actions:
            if action.get('action') == 'recruit_hero':
                if action.get('params', {}).get('rarity') == 'common':
                    failure_streak.append(action)
                    if len(failure_streak) >= count:
                        return failure_streak
                else:
                    failure_streak = [] # 抽到稀有或以上卡，打断连续失败
            else:
                # 其他非抽卡动作不打断连续性
                pass
        return []
        
    def check_venting_in_world_chat(self, actions: List[Dict], negative_keywords: List[str]) -> List[Dict]:
        """规则: 在世界频道发泄不满 (包含负面关键词)。"""
        venting_actions = []
        for a in actions:
            if a.get('action') == 'send_chat_message' and a.get('params', {}).get('channel') == 'world':
                message = a.get('params', {}).get('message_content', '').lower()
                if any(keyword in message for keyword in negative_keywords):
                    venting_actions.append(a)
        return venting_actions

    # --- 流失风险相关检测 (部分需要外部状态) ---

    def check_long_time_no_login(self, player_last_login_time: int, days: int = 3) -> bool:
        """规则: 连续N天未登录。这是一个需要外部状态的检查。"""
        current_timestamp = int(time.time())
        seconds_in_day = 86400
        return (current_timestamp - player_last_login_time) >= days * seconds_in_day

    def check_playtime_drop(self, current_week_playtime: float, historical_avg_playtime: float, threshold: float = 0.5) -> bool:
        """规则: 游戏时长急剧下降。需要预先计算好的外部状态。"""
        if historical_avg_playtime == 0: return False
        return (current_week_playtime / historical_avg_playtime) < threshold

    def check_bulk_item_sell(self, actions: List[Dict], count: int = 5) -> List[Dict]:
        """规则: 短时间内大量出售游戏道具。"""
        sell_actions = [a for a in actions if a.get('action') == 'sell_item']
        if len(sell_actions) >= count:
            return sell_actions
        return []
        
    def check_farewell_nickname(self, actions: List[Dict], farewell_keywords: List[str]) -> List[Dict]:
        """规则: 修改昵称为告别语。"""
        farewell_actions = []
        for a in actions:
            if a.get('action') == 'change_nickname':
                new_name = a.get('params', {}).get('new_name', '').lower()
                if any(keyword in new_name for keyword in farewell_keywords):
                    farewell_actions.append(a)
        return farewell_actions

    # --- 机器人行为相关检测 ---
    
    def check_abnormally_high_action_rate(self, actions: List[Dict], time_window_seconds: int = 1, rate_threshold: int = 10) -> List[Dict]:
        """规则: 操作频率异常高。注意: 这是一个计算密集型操作。"""
        from datetime import timedelta
        actions.sort(key=lambda x: x.get('timestamp', datetime.min)) # 确保按时间排序
        for i, action in enumerate(actions):
            window_start_time = action.get('timestamp', datetime.min)
            actions_in_window = [action]
            # 查看后续动作是否在时间窗口内
            for next_action in actions[i+1:]:
                next_timestamp = next_action.get('timestamp', datetime.min)
                if next_timestamp <= window_start_time + timedelta(seconds=time_window_seconds):
                    actions_in_window.append(next_action)
                else:
                    break
            if len(actions_in_window) > rate_threshold:
                return actions_in_window
        return []

class PlayerBehaviorSimulator:
    def __init__(self):
        # 基础游戏行为场景
        self.basic_scenarios = ["玩家登陆游戏", "玩家打开副本", "玩家迁城", "玩家攻城", "玩家被玩家攻击", "玩家攻占土地", "玩家加入家族", "玩家加入国家", "玩家讨伐蛮族", "玩家打开招募英雄", "玩家跳转充值页面", "玩家打开世界频道"]
        
        # 积极情绪相关场景
        self.positive_scenarios = [
            "玩家成功通关困难副本", "玩家获得稀有装备", "玩家升级成功", "玩家完成成就", 
            "玩家在PVP中获胜", "玩家成功招募传说英雄", "玩家家族排名上升", "玩家获得每日奖励",
            "玩家参与活动获得大奖", "玩家解锁新地图", "玩家技能升级成功", "玩家建筑升级完成",
            "玩家在世界频道收到赞美", "玩家被邀请加入高级家族", "玩家充值获得额外奖励"
        ]
        
        # 消极情绪相关场景
        self.negative_scenarios = [
            "发布消极评论", "突然不充了", "不买月卡了", "抽卡频率变低", "玩家分解装备", 
            "玩家退出家族", "玩家退出登录", "玩家点击退出游戏", "玩家连续副本失败", 
            "玩家被其他玩家击败多次", "玩家抽卡连续未中", "玩家装备强化失败", 
            "玩家在世界频道发泄不满", "玩家长时间未登录", "玩家删除好友", 
            "玩家取消自动续费", "玩家投诉客服", "玩家评分游戏1星"
        ]
        
        # 流失风险相关场景
        self.churn_risk_scenarios = [
            "玩家连续3天未登录", "玩家游戏时长急剧下降", "玩家停止充值行为", 
            "玩家卸载游戏客户端", "玩家清空背包物品", "玩家转让账号询价",
            "玩家在论坛发布退游帖", "玩家关注竞品游戏", "玩家修改昵称为告别语",
            "玩家大量出售游戏道具", "玩家退出所有社交群组"
        ]
        
        # 机器人行为相关场景
        self.bot_scenarios = [
            "玩家操作频率异常高", "玩家24小时在线", "玩家行为模式过于规律", 
            "玩家响应时间异常快", "玩家重复执行相同操作", "玩家移动路径过于精确",
            "玩家从不参与社交互动", "玩家操作无人类特征", "玩家同时多开账号"
        ]
        
        # 合并所有场景
        self.player_scenarios = (self.basic_scenarios + self.positive_scenarios + 
                               self.negative_scenarios + self.churn_risk_scenarios + 
                               self.bot_scenarios)
    
    def generate_behavior(self, player_id: str) -> PlayerBehavior:
        action = random.choice(self.player_scenarios)
        return PlayerBehavior(player_id=player_id, timestamp=datetime.now(), action=action)
    
    def generate_targeted_behavior(self, player_id: str, behavior_type: str) -> PlayerBehavior:
        """生成特定类型的行为"""
        if behavior_type == "positive":
            action = random.choice(self.positive_scenarios)
        elif behavior_type == "negative":
            action = random.choice(self.negative_scenarios)
        elif behavior_type == "churn_risk":
            action = random.choice(self.churn_risk_scenarios)
        elif behavior_type == "bot":
            action = random.choice(self.bot_scenarios)
        else:
            action = random.choice(self.basic_scenarios)
        
        return PlayerBehavior(player_id=player_id, timestamp=datetime.now(), action=action)
    
    def generate_behavior_sequence(self, player_id: str, sequence_type: str) -> List[PlayerBehavior]:
        """生成反映真实玩家变化的行为序列"""
        behaviors = []
        
        if sequence_type == "frustrated_player":
            # 沮丧玩家：连续失败 -> 消极情绪 -> 退出
            behaviors = [
                PlayerBehavior(player_id, datetime.now(), "玩家连续副本失败"),
                PlayerBehavior(player_id, datetime.now(), "玩家装备强化失败"),
                PlayerBehavior(player_id, datetime.now(), "发布消极评论"),
                PlayerBehavior(player_id, datetime.now(), "玩家在世界频道发泄不满"),
                PlayerBehavior(player_id, datetime.now(), "玩家点击退出游戏")
            ]
        
        elif sequence_type == "churn_risk_player":
            # 流失风险玩家：停止充值 -> 减少活动 -> 退出社交 -> 长期离线
            behaviors = [
                PlayerBehavior(player_id, datetime.now(), "突然不充了"),
                PlayerBehavior(player_id, datetime.now(), "不买月卡了"),
                PlayerBehavior(player_id, datetime.now(), "玩家游戏时长急剧下降"),
                PlayerBehavior(player_id, datetime.now(), "玩家退出家族"),
                PlayerBehavior(player_id, datetime.now(), "玩家连续3天未登录")
            ]
        
        elif sequence_type == "excited_player":
            # 兴奋玩家：获得成就 -> 积极参与 -> 增加投入
            behaviors = [
                PlayerBehavior(player_id, datetime.now(), "玩家获得稀有装备"),
                PlayerBehavior(player_id, datetime.now(), "玩家成功通关困难副本"),
                PlayerBehavior(player_id, datetime.now(), "玩家在世界频道收到赞美"),
                PlayerBehavior(player_id, datetime.now(), "玩家跳转充值页面"),
                PlayerBehavior(player_id, datetime.now(), "玩家充值获得额外奖励")
            ]
        
        elif sequence_type == "bot_pattern":
            # 机器人模式：规律性操作
            behaviors = [
                PlayerBehavior(player_id, datetime.now(), "玩家24小时在线"),
                PlayerBehavior(player_id, datetime.now(), "玩家操作频率异常高"),
                PlayerBehavior(player_id, datetime.now(), "玩家重复执行相同操作"),
                PlayerBehavior(player_id, datetime.now(), "玩家从不参与社交互动"),
                PlayerBehavior(player_id, datetime.now(), "玩家行为模式过于规律")
            ]
        
        elif sequence_type == "returning_player":
            # 回归玩家：长期离线 -> 重新登录 -> 探索变化
            behaviors = [
                PlayerBehavior(player_id, datetime.now(), "玩家长时间未登录"),
                PlayerBehavior(player_id, datetime.now(), "玩家登陆游戏"),
                PlayerBehavior(player_id, datetime.now(), "玩家开始点击游戏攻略"),
                PlayerBehavior(player_id, datetime.now(), "玩家解锁新地图"),
                PlayerBehavior(player_id, datetime.now(), "玩家参与活动获得大奖")
            ]
        
        return behaviors
    
    def generate_mock_dataset(self, dataset_type: str, num_players: int = 10) -> Dict[str, List[PlayerBehavior]]:
        """生成完整的mock数据集"""
        dataset = {}
        
        if dataset_type == "mixed_emotions":
            # 混合情绪数据集
            for i in range(num_players):
                player_id = f"player_{i+1}"
                emotion_type = random.choice(["frustrated_player", "excited_player", "churn_risk_player"])
                dataset[player_id] = self.generate_behavior_sequence(player_id, emotion_type)
        
        elif dataset_type == "churn_analysis":
            # 流失分析数据集
            for i in range(num_players):
                player_id = f"churn_player_{i+1}"
                dataset[player_id] = self.generate_behavior_sequence(player_id, "churn_risk_player")
        
        elif dataset_type == "bot_detection":
            # 机器人检测数据集
            for i in range(num_players):
                player_id = f"bot_player_{i+1}"
                dataset[player_id] = self.generate_behavior_sequence(player_id, "bot_pattern")
        
        elif dataset_type == "engagement_boost":
            # 参与度提升数据集
            for i in range(num_players):
                player_id = f"engage_player_{i+1}"
                # 混合沮丧和兴奋玩家，用于测试干预效果
                if i % 2 == 0:
                    dataset[player_id] = self.generate_behavior_sequence(player_id, "frustrated_player")
                else:
                    dataset[player_id] = self.generate_behavior_sequence(player_id, "excited_player")
        
        return dataset
    
    def load_mock_data_to_monitor(self, dataset: Dict[str, List[PlayerBehavior]], monitor_instance):
        """将mock数据加载到监控器中"""
        for player_id, behaviors in dataset.items():
            for behavior in behaviors:
                monitor_instance.add_behavior(behavior)
                time.sleep(0.1)  # 模拟时间间隔
        print(f"✅ 已加载 {len(dataset)} 个玩家的mock数据到监控系统")