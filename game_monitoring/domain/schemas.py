"""
Pydantic Schema定义

定义Orchestrator和Workers的输出格式验证Schema。
"""

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


def _validate_action_type(
    actions: list[dict[str, Any]],
    allowed_actions: set[str] | None = None,
) -> list[dict[str, Any]]:
    """校验动作列表包含 action_type，并在需要时限制允许值。"""
    for action in actions:
        action_type = action.get("action_type")
        if not isinstance(action_type, str) or not action_type:
            raise ValueError("Each action must include a non-empty action_type")

        if allowed_actions is not None and action_type not in allowed_actions:
            raise ValueError(f"Invalid action: {action_type}")

    return actions


class EmotionWorkerOutput(BaseModel):
    """情绪Worker输出Schema"""

    emotion_type: Literal["愤怒", "沮丧", "焦虑", "正常"]
    confidence: float = Field(ge=0.0, le=1.0)
    intervention_actions: list[dict[str, Any]]
    reason: str = Field(max_length=200)

    @field_validator("intervention_actions")
    @classmethod
    def validate_actions(cls, actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        allowed_actions = {"send_email", "grant_reward", "assign_support"}
        return _validate_action_type(actions, allowed_actions)


class ChurnWorkerOutput(BaseModel):
    """流失Worker输出Schema"""

    risk_level: Literal["高风险", "中风险", "低风险"]
    risk_score: float = Field(ge=0.0, le=1.0)
    retention_plan: list[dict[str, Any]]
    expected_effectiveness: float = Field(ge=0.0, le=1.0)

    @field_validator("retention_plan")
    @classmethod
    def validate_retention_plan(
        cls, actions: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        return _validate_action_type(actions)


class BehaviorWorkerOutput(BaseModel):
    """行为Worker输出Schema"""

    is_bot: bool
    bot_confidence: float = Field(ge=0.0, le=1.0)
    control_measures: list[dict[str, Any]]
    risk_tags: list[str]

    @field_validator("control_measures")
    @classmethod
    def validate_control_measures(
        cls, actions: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        return _validate_action_type(actions)
