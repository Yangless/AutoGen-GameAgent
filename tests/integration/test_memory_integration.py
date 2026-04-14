from game_monitoring.core.bootstrap import create_production_container
from game_monitoring.infrastructure.memory.memory_service import MemoryService


def test_bootstrap_registers_memory_service():
    """测试MemoryService在bootstrap中注册"""
    container = create_production_container()

    memory_service = container.resolve(MemoryService)

    assert memory_service is not None
    assert isinstance(memory_service, MemoryService)
    assert memory_service.short_term_window == 10
