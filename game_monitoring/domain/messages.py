"""
消息协议定义

定义Orchestrator和Workers之间的通信消息格式
"""

from dataclasses import dataclass
from typing import List, Dict, Any
try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal


@dataclass
class PlayerEvent:
    """玩家事件：Orchestrator接收的触发事件"""
    player_id: str
    triggered_scenarios: List[Dict[str, Any]]
    behavior_history: List[Dict[str, Any]]
    session_id: str


@dataclass
class InterventionTask:
    """干预任务：Orchestrator广播到Worker的任务包"""
    task_id: str
    player_id: str
    session_id: str
    task_type: Literal["emotion", "churn", "behavior"]
    context: Dict[str, Any]
    timestamp: str


@dataclass
class WorkerResponse:
    """Worker响应：Worker返回的干预结果"""
    task_id: str
    worker_type: str
    intervention_actions: List[Dict[str, Any]]
    confidence: float
    metadata: Dict[str, Any]
