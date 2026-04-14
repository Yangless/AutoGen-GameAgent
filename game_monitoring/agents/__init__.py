"""Agents module for game monitoring system."""

__all__ = []


try:
    from .analysis_agents import (
        create_behavioral_analyst_agent,
        create_bot_detection_agent,
        create_churn_risk_agent,
        create_emotion_recognition_agent,
    )

    __all__.extend(
        [
            "create_emotion_recognition_agent",
            "create_churn_risk_agent",
            "create_bot_detection_agent",
            "create_behavioral_analyst_agent",
        ]
    )
except ModuleNotFoundError:
    pass

try:
    from .intervention_agents import (
        create_engagement_agent,
        create_guidance_agent,
    )

    __all__.extend(["create_engagement_agent", "create_guidance_agent"])
except ModuleNotFoundError:
    pass

try:
    from .military_order_agent import create_military_order_agent

    __all__.append("create_military_order_agent")
except ModuleNotFoundError:
    pass

from .orchestrator import OrchestratorAgent
from .emotion_worker import EmotionWorker
from .churn_worker import ChurnWorker
from .behavior_worker import BehaviorWorker

__all__.append("OrchestratorAgent")
__all__.extend(["EmotionWorker", "ChurnWorker", "BehaviorWorker"])
