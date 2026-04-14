# Dashboard Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract the remaining Dashboard runtime hotspots into focused, testable helpers without changing the existing Streamlit user-facing behavior.

**Architecture:** Keep `streamlit_dashboard.py` as the rendering entrypoint, but move session/log state, action/intervention orchestration, and batch military-order generation into UI helper modules that operate on plain mappings and injected callables. Preserve current layout and runtime wiring.

**Tech Stack:** Python, Streamlit, pytest, application services, lightweight DI container

---

### Task 1: Extract Dashboard Session Helpers

**Files:**
- Create: `game_monitoring/ui/dashboard_session.py`
- Modify: `streamlit_dashboard.py`
- Test: `tests/unit/ui/test_dashboard_session.py`

- [ ] **Step 1: Write the failing tests**
- [ ] **Step 2: Run `.\.venv\Scripts\python.exe -m pytest tests\unit\ui\test_dashboard_session.py -q` and verify they fail**
- [ ] **Step 3: Implement `ensure_dashboard_state()` and `append_dashboard_log()` plus `TeamAnalysisLogCapture`**
- [ ] **Step 4: Re-run the focused test and verify it passes**

### Task 2: Extract Atomic Action And Intervention Flow

**Files:**
- Create: `game_monitoring/ui/dashboard_actions.py`
- Modify: `streamlit_dashboard.py`
- Test: `tests/unit/ui/test_dashboard_actions.py`

- [ ] **Step 1: Write the failing tests**
- [ ] **Step 2: Run `.\.venv\Scripts\python.exe -m pytest tests\unit\ui\test_dashboard_actions.py -q` and verify they fail**
- [ ] **Step 3: Implement action sequence recording, rule normalization, and intervention orchestration helpers**
- [ ] **Step 4: Re-run the focused test and verify it passes**

### Task 3: Extract Batch Military Order Generation

**Files:**
- Create: `game_monitoring/ui/dashboard_orders.py`
- Modify: `streamlit_dashboard.py`
- Test: `tests/unit/ui/test_dashboard_orders.py`

- [ ] **Step 1: Write the failing tests**
- [ ] **Step 2: Run `.\.venv\Scripts\python.exe -m pytest tests\unit\ui\test_dashboard_orders.py -q` and verify they fail**
- [ ] **Step 3: Implement the batch generation helper with injected generator callable and progress tracking**
- [ ] **Step 4: Re-run the focused test and verify it passes**

### Task 4: Close Out The Streamlit Entry Point

**Files:**
- Modify: `streamlit_dashboard.py`
- Modify: `game_monitoring/ui/dashboard_runtime.py`
- Test: `tests/unit/ui/test_dashboard_runtime.py`

- [ ] **Step 1: Remove dead compatibility helpers and unused session keys**
- [ ] **Step 2: Route the page through the extracted helpers**
- [ ] **Step 3: Drop unused runtime fields if they no longer serve callers**
- [ ] **Step 4: Run focused UI tests to verify behavior remains intact**

### Task 5: Verify End To End

**Files:**
- Test: `tests/`

- [ ] **Step 1: Run `.\.venv\Scripts\python.exe -m pytest tests game_monitoring\tests\test_container.py -q`**
- [ ] **Step 2: Run `.\.venv\Scripts\python.exe -m py_compile streamlit_dashboard.py game_monitoring\ui\dashboard_session.py game_monitoring\ui\dashboard_actions.py game_monitoring\ui\dashboard_orders.py game_monitoring\ui\dashboard_runtime.py`**
- [ ] **Step 3: Inspect the remaining Streamlit/dashboard legacy markers with `rg -n "trigger_behavior_and_analysis|agent_analysis_logs|StreamlitLogCapture|log_capture" streamlit_dashboard.py game_monitoring tests -S`**
