"""
情绪相关规则

从原有的 PlayerBehaviorRuleEngine 迁移
"""

from ..engine import Rule, RuleResult, RuleExecutionContext, RuleCategory, RulePriority


class ConsecutiveFailuresRule(Rule):
    """连续失败触发消极情绪"""

    FAILURE_ACTIONS = ['complete_dungeon', 'recruit_hero', 'lose_pvp']
    THRESHOLD = 2

    @property
    def rule_id(self) -> str:
        return "consecutive_failures"

    @property
    def scenario_name(self) -> str:
        return "连续失败触发消极情绪"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.EMOTION

    @property
    def priority(self) -> RulePriority:
        return RulePriority.HIGH

    def evaluate(self, context: RuleExecutionContext) -> RuleResult:
        failures = []
        count = 0

        for action in reversed(context.recent_actions):
            name = action.get('action', '')
            params = action.get('params', {})

            if name == 'lose_pvp':
                count += 1
                failures.insert(0, name)
            elif name in self.FAILURE_ACTIONS and params.get('status') == 'fail':
                count += 1
                failures.insert(0, name)
            else:
                break

        triggered = count >= self.THRESHOLD

        return RuleResult(
            rule_id=self.rule_id,
            triggered=triggered,
            scenario_name=self.scenario_name,
            description=f"连续失败{count}次" if triggered else "未检测到连续失败",
            category=self.category,
            confidence=min(count / 3.0, 1.0),
            priority=self.priority,
            triggered_actions=failures
        )


class SocialWithdrawalRule(Rule):
    """社交退出行为风险"""

    WITHDRAWAL_ACTIONS = {'leave_family', 'remove_friend', 'clear_backpack'}
    THRESHOLD = 2

    @property
    def rule_id(self) -> str:
        return "social_withdrawal"

    @property
    def scenario_name(self) -> str:
        return "社交退出行为风险"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.EMOTION

    @property
    def priority(self) -> RulePriority:
        return RulePriority.HIGH

    def evaluate(self, context: RuleExecutionContext) -> RuleResult:
        found = set()
        for action in context.recent_actions:
            name = action.get('action', '')
            if name in self.WITHDRAWAL_ACTIONS:
                found.add(name)

        triggered = len(found) >= self.THRESHOLD

        return RuleResult(
            rule_id=self.rule_id,
            triggered=triggered,
            scenario_name=self.scenario_name,
            description=f"社交退出行为: {', '.join(found)}" if triggered else "未检测到社交风险",
            category=self.category,
            confidence=len(found) / 3.0,
            priority=self.priority,
            triggered_actions=list(found)
        )
