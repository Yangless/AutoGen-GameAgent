# Dashboard Optimization Design

## Goal

在不改变现有 Dashboard 用户能力的前提下，继续优化 `streamlit_dashboard.py` 的可维护性、可测试性和运行时清晰度。

## Current Problem

当前主入口文件仍然承担了过多职责：

- Session state 默认值初始化
- 团队分析日志捕获
- 原子动作处理与干预触发编排
- 批量军令生成线程逻辑
- 大量直接的 `st.session_state` 读写
- 已无调用点的兼容性函数和未使用状态

这导致两个直接问题：

1. 关键行为难以单元测试，只能通过整页运行来间接验证。
2. 文件过大且职责混杂，后续改动容易引入回归。

## Approaches

### Option 1: 仅做静态清理

- 删除未使用导入、死代码和重复状态键
- 不新增模块

优点：

- 风险最低
- 改动最少

缺点：

- 主文件仍然过大
- 核心行为仍然难测

### Option 2: 保守结构优化

- 提取 Dashboard session/log helper
- 提取动作处理与干预编排 helper
- 提取批量军令生成 helper
- 保持现有页面布局和交互不变

优点：

- 在不重写 UI 的前提下获得明显的结构收益
- 可以为关键流程补纯单元测试
- 风险可控

缺点：

- `streamlit_dashboard.py` 仍会保留主要渲染逻辑

### Option 3: 激进页面拆分

- 将左/中/右三栏和各 tab 全部拆到多个 presenter / page section 模块
- 同时调整大段渲染逻辑

优点：

- 长期结构最干净

缺点：

- 变更面过大
- 当前阶段回归风险高
- 与“保留现有行为并快速收口”不匹配

## Recommendation

采用 Option 2。

这是当前性价比最高的路径：优先提取状态、动作编排和批处理这三类高复杂、低可测的逻辑，把它们变成纯 Python helper；页面本身保留现有布局与控件树，避免把本轮优化升级成整页重写。

## Target Design

### 1. Session And Logging

新增 `game_monitoring/ui/dashboard_session.py`，负责：

- 初始化 Dashboard 需要的 session state 默认键
- 管理基础日志追加与截断
- 管理团队分析日志捕获器

这里的 API 只接收 `MutableMapping`，避免依赖真实 Streamlit 环境，便于单元测试。

### 2. Action And Intervention Orchestration

新增 `game_monitoring/ui/dashboard_actions.py`，负责：

- 记录动作序列
- 规范化规则触发结果
- 计算动作处理后的日志输出
- 统一触发干预并保存结构化结果

`streamlit_dashboard.py` 只负责把 `runtime`、`session_state` 和 UI 回调传入 helper，不再直接承载完整业务流程。

### 3. Batch Military Order Generation

新增 `game_monitoring/ui/dashboard_orders.py`，负责：

- 对玩家列表逐个生成军令
- 累加处理进度
- 统一封装成功与失败结果
- 收口线程目标函数中的状态更新

这样可以把批量处理逻辑从页面渲染函数中剥离出来，并补可预测的单元测试。

### 4. Streamlit Dashboard Closeout

`streamlit_dashboard.py` 将保留：

- 页面配置
- CSS
- 页面布局与控件渲染
- 对 helper 的调用

同时删除：

- 未使用的 `StreamlitLogCapture`
- 未使用的 `agent_analysis_logs`
- 无调用点的 `trigger_behavior_and_analysis`
- 仅为旧实现留下的冗余导入和状态占位

## Testing Strategy

新增或扩展单元测试覆盖：

- session 默认值和日志截断
- 团队分析日志捕获同步
- 原子动作处理与干预触发
- 批量军令生成的成功/失败/进度更新

另外保留现有全量 `pytest` 回归和 `py_compile` 语法校验作为完成门槛。

## Scope Boundary

本轮不做：

- Streamlit 页面视觉重设计
- 全量 presenter 化
- 新增业务功能
- Redis / 模型客户端层面的新部署能力
