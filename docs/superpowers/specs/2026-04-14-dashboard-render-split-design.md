# Dashboard Render Split Design

## Goal

将 `streamlit_dashboard.py` 的渲染层进一步拆分到 tab / section 级别，同时保持当前页面功能、状态流和交互行为不变。

本次工作只处理渲染组织方式，不再改业务规则、服务层接口或运行时数据结构。

## Current Problem

经过前一轮优化后，`streamlit_dashboard.py` 的业务热点已经被抽到 helper，但主文件仍然承载了过多渲染职责：

- 左侧玩家状态与属性编辑整块 UI
- 中央四个 tab 的所有渲染逻辑
- 右侧动作面板与体力特殊处理
- 底部状态栏

这带来三个具体问题：

1. `main()` 仍然过长，阅读成本高。
2. 页面局部修改容易影响其它区域，因为所有渲染代码仍在一个函数里。
3. 渲染层单元测试不好切片，因为没有清晰的 section / tab 边界。

## Design Options

### Option 1: 单文件内拆成多个函数

在 `streamlit_dashboard.py` 内部定义 `render_left_panel()`、`render_tab_orders()` 等函数，但仍留在同一文件。

优点：

- 风险低
- 文件导入关系简单

缺点：

- 文件体积仍然大
- 模块边界不够清晰

### Option 2: 两级模块拆分

将渲染层拆成两个模块：

- `game_monitoring/ui/dashboard_sections.py`
- `game_monitoring/ui/dashboard_tabs.py`

其中 section 模块负责三栏和底部状态栏，tab 模块负责中央四个 tab 的内容。

优点：

- 颗粒度和复杂度匹配
- 文件数量适中
- 主入口会明显收缩

缺点：

- 需要一个共享的渲染上下文对象，避免参数爆炸

### Option 3: 每个 tab / section 独立文件

例如：

- `left_panel.py`
- `right_panel.py`
- `tab_logs.py`
- `tab_orders.py`

优点：

- 结构最细
- 单文件职责最纯

缺点：

- 当前代码体量下会过度拆分
- 导航成本和样板代码会上升

## Recommendation

采用 Option 2。

当前页面复杂度足够支撑“两级模块拆分”，但还没有复杂到每个 tab 单独一个文件。两级模块能把 `main()` 收缩到只负责：

- 初始化 session 与 runtime
- 组装渲染上下文
- 调用 `render_left_panel()`、`render_center_panel()`、`render_right_panel()`、`render_status_bar()`

同时中央 tab 的复杂度也会被完整隔离出去。

## Target Architecture

### 1. Shared Render Context

新增 `DashboardRenderContext` 数据对象，用于承载渲染层真正共享的数据和回调。

建议包含：

- `session_state`
- `runtime`
- `monitor`
- `player_state_manager`
- `add_agent_log`
- `add_behavior_log`
- `add_stamina_guide_log`
- `store_team_analysis_result`
- `run_async`
- `add_script_run_ctx`

设计原则：

- 渲染函数只依赖这个上下文对象和必要的直接输入
- 避免把几十个独立参数在 section / tab 之间传来传去
- 不把新的业务逻辑塞回上下文对象，它只是渲染层依赖载体

### 2. Section Module

新增 `game_monitoring/ui/dashboard_sections.py`，负责：

- `render_left_panel(ctx)`
- `render_center_panel(ctx)`
- `render_right_panel(ctx)`
- `render_status_bar(ctx)`

职责边界：

- 只做布局与区域级调度
- section 内可以创建列、expander、tabs
- 具体 tab 内容交给 `dashboard_tabs.py`

### 3. Tab Module

新增 `game_monitoring/ui/dashboard_tabs.py`，负责：

- `render_basic_logs_tab(ctx)`
- `render_team_analysis_tab(ctx)`
- `render_stamina_tab(ctx)`
- `render_orders_tab(ctx)`

职责边界：

- 只负责中央区域 tab 的具体展示和交互控件
- 批量生成、动作处理等业务执行继续调用已有 helper
- 不在 tab 模块里创建新的服务或重新组装 runtime

### 4. Streamlit Entry Point

`streamlit_dashboard.py` 在完成拆分后保留：

- 页面配置
- CSS
- `run_async()`
- `initialize_system()`
- 基础日志 helper 封装
- `main()` 顶层流程

`main()` 目标收缩为：

1. `ensure_dashboard_state(st.session_state)`
2. 初始化 runtime
3. 构造 `DashboardRenderContext`
4. 创建三栏布局
5. 调用各个 section render 函数

## Data Flow

渲染层数据流保持现状，不改变来源：

- Session 默认值来自 `dashboard_session.py`
- 动作处理来自 `dashboard_actions.py`
- 批量军令来自 `dashboard_orders.py`
- runtime 服务与仓储来自 `dashboard_runtime.py`

本次只是改变“谁来渲染”，不改变“数据从哪来”。

## Testing Strategy

本次拆分后新增测试应覆盖两类内容：

### 1. 纯渲染调度测试

验证：

- `streamlit_dashboard.main()` 不再直接内联 tab 逻辑
- `dashboard_sections.py` 会调用正确的 tab render 函数

### 2. 轻量交互测试

针对 section / tab 层保留最小必要测试，例如：

- orders tab 在批量生成按钮路径上仍会启动线程并写入进度状态
- right panel 仍会在动作按钮路径上调用 `process_atomic_action`

不追求把所有 Streamlit 细节都做成深度 UI mock；目标是保护结构边界和关键调用链。

## Non-Goals

本次不做：

- 页面视觉重设计
- 中央 tab 内容功能删改
- 业务 helper 再次重构
- 再次修改 runtime 注入结构
- 引入新的前端框架或组件系统

## Expected Outcome

拆分完成后，预期状态是：

- `streamlit_dashboard.py` 明显缩短并只保留入口职责
- tab / section 有独立模块和明确边界
- 后续修改单个区域时，不必再在单个超长函数里定位
- 渲染层结构具备继续拆 presenter 的自然演进路径，但当前不过度设计
