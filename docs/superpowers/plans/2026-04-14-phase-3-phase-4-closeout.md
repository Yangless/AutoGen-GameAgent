# Phase 3 Tail And Phase 4 Closeout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish the runtime migration by moving the Streamlit dashboard onto application services and removing the remaining runtime-facing legacy global context and legacy team branches.

**Architecture:** Keep the existing user-facing dashboard features, but route all runtime state through `bootstrap_application()` and application services instead of `game_monitoring.context` and `GamePlayerMonitoringSystem`. Move persistence-sensitive counters into monitor/context-backed objects, then delete runtime uses of legacy `GameMonitoringTeam` and top-level global monitor/state helpers.

**Tech Stack:** Python, Streamlit, pytest, lightweight DI container, AutoGen Core runtime

---

### Task 1: Stabilize Service-Layer Runtime State

**Files:**
- Modify: `game_monitoring/monitoring/behavior_monitor.py`
- Modify: `game_monitoring/application/services/action_service.py`
- Modify: `game_monitoring/application/services/agent_service.py`
- Modify: `game_monitoring/core/context.py`
- Modify: `game_monitoring/core/bootstrap.py`
- Test: `tests/unit/monitoring/test_behavior_monitor.py`
- Test: `tests/unit/application/test_agent_service.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_behavior_monitor_negative_count_api_persists_per_player():
    monitor = BehaviorMonitor(threshold=2)
    monitor.increment_negative_count("player_1")
    current = monitor.increment_negative_count("player_1")
    assert current == 2
    assert monitor.get_negative_count("player_1") == 2


def test_agent_service_returns_structured_payload_from_v2_team():
    context = GameContext(monitor=object(), player_state_manager=object())

    class FakeTeam:
        async def trigger_analysis_and_intervention(self, player_id, monitor):
            return {"player_id": player_id, "final_actions": [{"action_type": "grant_reward"}]}

    service = AgentService(context, team_factory=lambda: FakeTeam())
    result = asyncio.run(service.trigger_intervention("player_1"))
    assert result.success is True
    assert result.payload["player_id"] == "player_1"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.\.venv\Scripts\python.exe -m pytest tests\unit\monitoring\test_behavior_monitor.py tests\unit\application\test_agent_service.py -q`
Expected: FAIL because `BehaviorMonitor` lacks the persistent negative count API and `InterventionResult` lacks a structured payload field.

- [ ] **Step 3: Write the minimal implementation**

```python
class BehaviorMonitor:
    def get_negative_count(self, player_id: str) -> int:
        return self._negative_counts.get(player_id, 0)

    def increment_negative_count(self, player_id: str) -> int:
        current = self.get_negative_count(player_id) + 1
        self._negative_counts[player_id] = current
        return current

    def reset_negative_count(self, player_id: str) -> None:
        self._negative_counts[player_id] = 0


@dataclass
class InterventionResult:
    player_id: str
    success: bool
    message: str
    payload: Any | None = None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.\.venv\Scripts\python.exe -m pytest tests\unit\monitoring\test_behavior_monitor.py tests\unit\application\test_agent_service.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add game_monitoring/monitoring/behavior_monitor.py game_monitoring/application/services/action_service.py game_monitoring/application/services/agent_service.py game_monitoring/core/context.py game_monitoring/core/bootstrap.py tests/unit/monitoring/test_behavior_monitor.py tests/unit/application/test_agent_service.py
git commit -m "refactor: persist runtime state in monitor and agent service"
```

### Task 2: Move Streamlit Runtime Onto Container And Services

**Files:**
- Modify: `streamlit_dashboard.py`
- Modify: `game_monitoring/ui/pages/main_dashboard.py`
- Modify: `game_monitoring/ui/dashboard_state.py`
- Test: `tests/unit/ui/test_dashboard_state.py`
- Test: `tests/unit/ui/test_main_dashboard.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_dashboard_runtime_uses_bootstrap_container_not_legacy_global_context(monkeypatch):
    dashboard = importlib.import_module("streamlit_dashboard")
    source = inspect.getsource(dashboard.initialize_system)
    assert "bootstrap_application" in source


def test_clear_action_sequence_keeps_monitor_and_ui_in_sync():
    session_state = {"action_sequence": [{"action": "sell_item"}]}
    monitor = BehaviorMonitor()
    monitor.add_atomic_action("player_1", "sell_item")
    clear_action_sequence(session_state, monitor, "player_1")
    assert session_state["action_sequence"] == []
    assert monitor.get_player_action_sequence("player_1") == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.\.venv\Scripts\python.exe -m pytest tests\unit\ui\test_dashboard_state.py tests\unit\ui\test_main_dashboard.py -q`
Expected: FAIL because the dashboard still imports `game_monitoring.context` and the new page/runtime split is incomplete.

- [ ] **Step 3: Write the minimal implementation**

```python
@st.cache_resource
def initialize_runtime():
    container = bootstrap_application()
    return {
        "container": container,
        "context": container.resolve(GameContext),
        "action_service": container.resolve(ActionProcessingService),
        "agent_service": container.resolve(AgentService),
    }


async def process_atomic_action(player_id: str, action_name: str):
    runtime = st.session_state.runtime
    result = await runtime["action_service"].process_action(player_id, action_name)
    if result.should_intervene:
        intervention = await runtime["agent_service"].trigger_intervention(player_id)
        if intervention.payload:
            store_team_analysis_result(intervention.payload)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.\.venv\Scripts\python.exe -m pytest tests\unit\ui\test_dashboard_state.py tests\unit\ui\test_main_dashboard.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add streamlit_dashboard.py game_monitoring/ui/pages/main_dashboard.py game_monitoring/ui/dashboard_state.py tests/unit/ui/test_dashboard_state.py tests/unit/ui/test_main_dashboard.py
git commit -m "refactor: route dashboard runtime through container services"
```

### Task 3: Remove Runtime-Facing Legacy Context And Legacy Team Branches

**Files:**
- Modify: `game_monitoring/system/game_system.py`
- Modify: `game_monitoring/system/__init__.py`
- Modify: `game_monitoring/team/team_manager.py`
- Modify: `game_monitoring/team/__init__.py`
- Modify: `game_monitoring/tools/emotion_tool.py`
- Modify: `game_monitoring/tools/churn_tool.py`
- Modify: `game_monitoring/tools/bot_tool.py`
- Modify: `game_monitoring/tools/baseline_tool.py`
- Modify: `game_monitoring/tools/military_order_tool.py`
- Modify: `game_monitoring/tools/stamina_guide_tool.py`
- Test: `tests/unit/system/test_game_system.py`
- Test: `tests/integration/test_team_manager_integration.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_game_player_monitoring_system_only_builds_v2_runtime(monkeypatch):
    system = GamePlayerMonitoringSystem(model_client=None)
    assert isinstance(system.team, GameMonitoringTeamV2)


def test_team_package_exports_only_v2_runtime_manager():
    import game_monitoring.team as team_module
    assert "GameMonitoringTeamV2" in team_module.__all__
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.\.venv\Scripts\python.exe -m pytest tests\unit\system\test_game_system.py tests\integration\test_team_manager_integration.py -q`
Expected: FAIL because the system and package still expose legacy team/runtime branches.

- [ ] **Step 3: Write the minimal implementation**

```python
class GamePlayerMonitoringSystem:
    def __init__(self, model_client=None):
        self.team = GameMonitoringTeamV2(
            model_client=model_client,
            runtime=SingleThreadedAgentRuntime(),
        )


__all__ = ["GameMonitoringTeamV2"]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.\.venv\Scripts\python.exe -m pytest tests\unit\system\test_game_system.py tests\integration\test_team_manager_integration.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add game_monitoring/system/game_system.py game_monitoring/system/__init__.py game_monitoring/team/team_manager.py game_monitoring/team/__init__.py game_monitoring/tools/emotion_tool.py game_monitoring/tools/churn_tool.py game_monitoring/tools/bot_tool.py game_monitoring/tools/baseline_tool.py game_monitoring/tools/military_order_tool.py game_monitoring/tools/stamina_guide_tool.py tests/unit/system/test_game_system.py tests/integration/test_team_manager_integration.py
git commit -m "refactor: remove runtime legacy context and team branches"
```

### Task 4: Verify Closeout End To End

**Files:**
- Modify: `docs/REFACTORING_COMPLETE.md`
- Test: `tests/`

- [ ] **Step 1: Update completion notes**

```md
- Streamlit runtime now boots from `bootstrap_application()`
- Runtime path no longer depends on `game_monitoring.context` for monitor/state access
- Legacy `GameMonitoringTeam` runtime branch removed
```

- [ ] **Step 2: Run the focused regression suite**

Run: `.\.venv\Scripts\python.exe -m pytest tests game_monitoring\tests\test_container.py -q`
Expected: PASS with 0 failures

- [ ] **Step 3: Run syntax verification**

Run: `.\.venv\Scripts\python.exe -m py_compile streamlit_dashboard.py game_monitoring\system\game_system.py game_monitoring\team\team_manager.py game_monitoring\tools\emotion_tool.py game_monitoring\tools\churn_tool.py game_monitoring\tools\bot_tool.py game_monitoring\tools\baseline_tool.py game_monitoring\tools\military_order_tool.py game_monitoring\tools\stamina_guide_tool.py`
Expected: exit code 0

- [ ] **Step 4: Inspect remaining legacy references**

Run: `rg -n "game_monitoring\\.context|get_global_monitor|get_global_player_state_manager|GameMonitoringTeam\\b|use_v2_runtime" game_monitoring streamlit_dashboard.py tests -S`
Expected: no runtime-path hits beyond explicitly retained non-runtime compatibility shims

- [ ] **Step 5: Commit**

```bash
git add docs/REFACTORING_COMPLETE.md
git commit -m "docs: record phase 3 and phase 4 runtime closeout"
```
