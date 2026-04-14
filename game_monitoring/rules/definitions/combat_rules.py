"""
战斗相关规则
"""

from ..engine import Rule, RuleResult, RuleExecutionContext, RuleCategory, RulePriority


class StaminaExhaustionRule(Rule):
    """体力耗尽引导触发"""

    STAMINA_KEYWORDS = ['stamina_exhausted', 'attempt_enter_dungeon_no_stamina']
    THRESHOLD = 3

    @property
    def rule_id(self) -> str:
        return "stamina_exhaustion"

    @property
    def scenario_name(self) -> str:
        return "体力耗尽引导触发"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.COMBAT

    @property
    def priority(self) -> RulePriority:
        return RulePriority.CRITICAL

    def evaluate(self, context: RuleExecutionContext) -> RuleResult:
        count = sum(
            1 for action in context.actions
            if any(kw in action.get('action', '').lower() for kw in self.STAMINA_KEYWORDS)
        )

        triggered = count >= self.THRESHOLD

        return RuleResult(
            rule_id=self.rule_id,
            triggered=triggered,
            scenario_name=self.scenario_name,
            description=f"体力耗尽{count}次，已达引导阈值" if triggered else "未达体力阈值",
            category=self.category,
            confidence=min(count / self.THRESHOLD, 1.0),
            priority=self.priority,
            metadata={'stamina_count': count}
        )
