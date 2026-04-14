# Orchestrator-Worker架构部署指南

> 当前文档覆盖 Orchestrator-Worker 模块的依赖准备、Redis 配置和 v2 runtime 验证方式。仓库默认的 Streamlit / `GamePlayerMonitoringSystem` 入口现在已经切换为 `GameMonitoringTeamV2`。

## 环境要求

- Python 3.10+
- Redis 6.0+
- AutoGen Core 0.4+
- Pydantic 2.x

## 安装依赖

```bash
uv sync
```

如果需要显式安装关键依赖：

```bash
pip install autogen-core pydantic redis
```

## 配置Redis

```bash
redis-server
redis-cli ping
```

预期返回：

```text
PONG
```

## 启动应用

```python
from game_monitoring.core.bootstrap import bootstrap_application
from game_monitoring.domain.messages import PlayerEvent

container = bootstrap_application(setup_global_context=False)
orchestrator = container.resolve("OrchestratorAgent")

event = PlayerEvent(
    player_id="player_1",
    triggered_scenarios=[{"scenario": "negative_behavior"}],
    behavior_history=[{"action": "click_exit"}],
    session_id="session_123",
)

tasks = orchestrator._generate_tasks(event)
```

以上示例验证的是模块装配和任务生成，不包含 `SingleThreadedAgentRuntime` 的完整注册、订阅和消息广播生命周期。

## 运行验证

```bash
uv run python -m pytest tests -v
```

## 性能指标

- 处理能力：≥3000条/日
- 输出错误率：≤11%
- Token消耗降低：≥55%

## 说明

- `MemoryService` 当前支持注入式 client 和延迟 Redis 连接，便于本地测试与生产部署共存。
- `GameMonitoringTeamV2` 使用 `AgentId("orchestrator", "default")` 作为新版入口。
- `GamePlayerMonitoringSystem` 和 Streamlit Dashboard 都固定走 v2 runtime，不再提供 legacy runtime 切换开关。
