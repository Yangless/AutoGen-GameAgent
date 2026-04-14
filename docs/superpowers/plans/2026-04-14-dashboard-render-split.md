# Dashboard Render Split Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split the remaining Streamlit dashboard rendering layer into section-level and tab-level modules while preserving current page behavior and runtime wiring.

**Architecture:** Introduce a shared render-context dataclass plus two rendering modules: one for top-level sections and one for the center-panel tabs. Keep `streamlit_dashboard.py` as the page entrypoint that initializes session/runtime, builds the render context, and delegates rendering to the extracted section functions.

**Tech Stack:** Python, Streamlit, pytest, dataclasses, existing dashboard helper modules

---

### Task 1: Add Shared Render Context And Section/Tab Dispatch Tests

**Files:**
- Create: `game_monitoring/ui/dashboard_render_context.py`
- Create: `tests/unit/ui/test_dashboard_sections.py`
- Create: `tests/unit/ui/test_dashboard_tabs.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_render_center_panel_calls_all_tab_renderers(monkeypatch):
    calls = []

    monkeypatch.setattr(section_module, "render_basic_logs_tab", lambda ctx: calls.append("logs"))
    monkeypatch.setattr(section_module, "render_team_analysis_tab", lambda ctx: calls.append("analysis"))
    monkeypatch.setattr(section_module, "render_stamina_tab", lambda ctx: calls.append("stamina"))
    monkeypatch.setattr(section_module, "render_orders_tab", lambda ctx: calls.append("orders"))

    section_module.render_center_panel(ctx)

    assert calls == ["logs", "analysis", "stamina", "orders"]


def test_render_status_bar_uses_session_state_values():
    render_status_bar(ctx)
    assert fake_streamlit.writes[-1] == "⚙️ 系统状态: 🟢 运行中"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.\.venv\Scripts\python.exe -m pytest tests\unit\ui\test_dashboard_sections.py tests\unit\ui\test_dashboard_tabs.py -q`
Expected: FAIL because the render-context and render split modules do not exist yet.

- [ ] **Step 3: Write the minimal implementation**

```python
@dataclass
class DashboardRenderContext:
    session_state: Any
    runtime: Mapping[str, Any]
    monitor: Any
    player_state_manager: Any
    run_async: Callable[[Any], Any]
    add_agent_log: Callable[[str], None]
    add_behavior_log: Callable[[str, str], None]
    add_stamina_guide_log: Callable[[str], None]
    store_team_analysis_result: Callable[[dict[str, Any]], None]
    add_script_run_ctx: Callable[[Any], None] | None = None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.\.venv\Scripts\python.exe -m pytest tests\unit\ui\test_dashboard_sections.py tests\unit\ui\test_dashboard_tabs.py -q`
Expected: PASS

### Task 2: Extract Center Tabs Into `dashboard_tabs.py`

**Files:**
- Create: `game_monitoring/ui/dashboard_tabs.py`
- Modify: `streamlit_dashboard.py`
- Test: `tests/unit/ui/test_dashboard_tabs.py`

- [ ] **Step 1: Expand the failing tab tests**

```python
def test_render_basic_logs_tab_shows_info_when_logs_missing():
    render_basic_logs_tab(ctx)
    assert fake_streamlit.infos == ["等待系统活动..."]


def test_render_team_analysis_tab_renders_results_and_logs():
    render_team_analysis_tab(ctx)
    assert fake_streamlit.expanders
    assert fake_streamlit.markdowns
```

- [ ] **Step 2: Run the focused tab tests and verify they fail**

Run: `.\.venv\Scripts\python.exe -m pytest tests\unit\ui\test_dashboard_tabs.py -q`
Expected: FAIL because the extracted tab renderers are not implemented yet.

- [ ] **Step 3: Implement the tab renderers**

```python
def render_basic_logs_tab(ctx: DashboardRenderContext) -> None:
    if ctx.session_state.agent_logs:
        for log in reversed(ctx.session_state.agent_logs):
            st.markdown(f"<div class='agent-log'>{log}</div>", unsafe_allow_html=True)
    else:
        st.info("等待系统活动...")
```

- [ ] **Step 4: Re-run the focused tab tests and verify they pass**

Run: `.\.venv\Scripts\python.exe -m pytest tests\unit\ui\test_dashboard_tabs.py -q`
Expected: PASS

### Task 3: Extract Left/Center/Right/Status Sections Into `dashboard_sections.py`

**Files:**
- Create: `game_monitoring/ui/dashboard_sections.py`
- Modify: `streamlit_dashboard.py`
- Test: `tests/unit\ui\test_dashboard_sections.py`

- [ ] **Step 1: Expand the failing section tests**

```python
def test_render_right_panel_uses_run_async_for_clicked_action():
    render_right_panel(ctx)
    assert fake_run_async.calls


def test_render_left_panel_keeps_profile_update_path():
    render_left_panel(ctx)
    assert fake_streamlit.text_inputs
```

- [ ] **Step 2: Run the focused section tests and verify they fail**

Run: `.\.venv\Scripts\python.exe -m pytest tests\unit\ui\test_dashboard_sections.py -q`
Expected: FAIL because the extracted section renderers and action-button wrapper do not exist yet.

- [ ] **Step 3: Implement the section renderers and action-button wrapper**

```python
def render_center_panel(ctx: DashboardRenderContext) -> None:
    st.markdown('<h2 class="section-header">🤖 Agent 决策流程</h2>', unsafe_allow_html=True)
    tab1, tab2, tab3, tab4 = st.tabs(["📋 基础日志", "🧠 Agent团队分析", "⚡ 体力引导Agent", "⚔️ 军令操作"])
    with tab1:
        render_basic_logs_tab(ctx)
```

- [ ] **Step 4: Re-run the focused section tests and verify they pass**

Run: `.\.venv\Scripts\python.exe -m pytest tests\unit\ui\test_dashboard_sections.py -q`
Expected: PASS

### Task 4: Collapse `streamlit_dashboard.py` To Entry-Point Responsibilities

**Files:**
- Modify: `streamlit_dashboard.py`
- Modify: `tests/unit/ui/test_main_dashboard.py`

- [ ] **Step 1: Write the failing regression test**

```python
def test_streamlit_dashboard_main_delegates_rendering(monkeypatch):
    calls = []
    monkeypatch.setattr(dashboard_module, "render_left_panel", lambda ctx: calls.append("left"))
    monkeypatch.setattr(dashboard_module, "render_center_panel", lambda ctx: calls.append("center"))
    monkeypatch.setattr(dashboard_module, "render_right_panel", lambda ctx: calls.append("right"))
    monkeypatch.setattr(dashboard_module, "render_status_bar", lambda ctx: calls.append("status"))

    dashboard_module.main()

    assert calls == ["left", "center", "right", "status"]
```

- [ ] **Step 2: Run the focused regression test and verify it fails**

Run: `.\.venv\Scripts\python.exe -m pytest tests\unit\ui\test_main_dashboard.py -q`
Expected: FAIL because `main()` still inlines the render tree.

- [ ] **Step 3: Refactor `main()` to build `DashboardRenderContext` and delegate**

```python
ctx = DashboardRenderContext(
    session_state=st.session_state,
    runtime=st.session_state.system,
    monitor=st.session_state.monitor,
    player_state_manager=st.session_state.player_state_manager,
    run_async=run_async,
    add_agent_log=add_agent_log,
    add_behavior_log=add_behavior_log,
    add_stamina_guide_log=add_stamina_guide_log,
    store_team_analysis_result=store_team_analysis_result,
    add_script_run_ctx=add_script_run_ctx,
)
```

- [ ] **Step 4: Re-run the focused regression test and verify it passes**

Run: `.\.venv\Scripts\python.exe -m pytest tests\unit\ui\test_main_dashboard.py -q`
Expected: PASS

### Task 5: Verify The Full Dashboard Suite

**Files:**
- Test: `tests/unit/ui/`
- Test: `tests/`

- [ ] **Step 1: Run the dashboard-focused suite**

Run: `.\.venv\Scripts\python.exe -m pytest tests\unit\ui\test_dashboard_session.py tests\unit\ui\test_dashboard_actions.py tests\unit\ui\test_dashboard_orders.py tests\unit\ui\test_dashboard_runtime.py tests\unit\ui\test_dashboard_state.py tests\unit\ui\test_dashboard_tabs.py tests\unit\ui\test_dashboard_sections.py tests\unit\ui\test_main_dashboard.py -q`
Expected: PASS

- [ ] **Step 2: Run syntax verification**

Run: `.\.venv\Scripts\python.exe -m py_compile streamlit_dashboard.py game_monitoring\ui\dashboard_render_context.py game_monitoring\ui\dashboard_tabs.py game_monitoring\ui\dashboard_sections.py`
Expected: exit code 0

- [ ] **Step 3: Run the full regression suite**

Run: `.\.venv\Scripts\python.exe -m pytest tests game_monitoring\tests\test_container.py -q`
Expected: PASS with 0 failures

- [ ] **Step 4: Inspect the entrypoint for residual inline tab/section blocks**

Run: `rg -n "with col1:|with col2:|with col3:|with tab1:|with tab2:|with tab3:|with tab4:" streamlit_dashboard.py -S`
Expected: no residual inline section/tab render blocks inside the entrypoint file
