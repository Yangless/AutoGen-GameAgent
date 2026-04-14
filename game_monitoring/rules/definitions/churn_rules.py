"""
流失风险规则
"""

from ..engine import Rule, RuleResult, RuleExecutionContext, RuleCategory, RulePriority


class ChurnRiskRule(Rule):
    """流失风险预警"""

    CHURN_ACTIONS = {
        'uninstall_game', 'cancel_auto_renew', 'click_exit_game_button',
        'sell_item', 'post_account_for_sale', 'clear_backpack'
    }

    @property
    def rule_id(self) -> str:
        return "churn_risk"

    @property
    def scenario_name(self) -> str:
        return "流失风险预警"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.CHURN_RISK

    @property
    def priority(self) -> RulePriority:
        return RulePriority.HIGH

    def evaluate(self, context: RuleExecutionContext) -> RuleResult:
        triggered = []
        for action in context.recent_actions:
            name = action.get('action', '')
            if name in self.CHURN_ACTIONS:
                triggered.append(name)

        is_triggered = len(triggered) > 0

        return RuleResult(
            rule_id=self.rule_id,
            triggered=is_triggered,
            scenario_name=self.scenario_name,
            description=f"流失风险行为: {', '.join(triggered)}" if triggered else "无流失风险",
            category=self.category,
            confidence=0.8 if triggered else 0.0,
            priority=self.priority,
            triggered_actions=triggered
        )
