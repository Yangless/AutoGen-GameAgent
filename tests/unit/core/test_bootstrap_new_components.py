from autogen_core import SingleThreadedAgentRuntime

from game_monitoring.agents.orchestrator import OrchestratorAgent
from game_monitoring.core.bootstrap import create_production_container
from game_monitoring.infrastructure.validation.output_validator import (
    OutputValidator,
)


def test_bootstrap_registers_orchestrator():
    """测试Orchestrator在bootstrap中注册"""
    container = create_production_container()

    orchestrator = container.resolve("OrchestratorAgent")

    assert isinstance(orchestrator, OrchestratorAgent)


def test_bootstrap_registers_validator():
    """测试OutputValidator在bootstrap中注册"""
    container = create_production_container()

    validator = container.resolve("OutputValidator")

    assert isinstance(validator, OutputValidator)


def test_bootstrap_registers_runtime():
    """测试AutoGen runtime在bootstrap中注册"""
    container = create_production_container()

    runtime = container.resolve(SingleThreadedAgentRuntime)

    assert isinstance(runtime, SingleThreadedAgentRuntime)
