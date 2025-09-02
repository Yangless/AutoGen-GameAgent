# 🎮 游戏监控系统 Streamlit Dashboard

这是一个基于 Streamlit 的交互式前端界面，用于演示和调试游戏玩家行为监控系统。

## 📋 功能特性

### 🏗️ 三栏布局设计

| 区域 | 功能 | 描述 |
|------|------|------|
| **左侧面板** | 👤 玩家状态展示 | 显示玩家的实时状态，包括情绪、流失风险、机器人检测结果等 |
| **中央面板** | 🤖 Agent 决策流程 | 实时显示多智能体系统的分析日志和决策过程 |
| **右侧面板** | 🎯 行为模拟器 | 提供各种类型的行为模拟按钮，触发系统分析 |

### 🎯 核心功能

- **实时状态监控**: 显示玩家的情绪状态、流失风险等级、机器人检测结果
- **行为历史追踪**: 展示玩家最近的行为记录
- **智能体协作**: 实时查看多智能体团队的分析和决策过程
- **交互式模拟**: 通过按钮点击模拟各种玩家行为场景
- **日志管理**: 自动记录和显示系统运行日志

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装 Streamlit Dashboard 所需依赖
pip install -r requirements_streamlit.txt
```

### 2. 启动应用

**方法一：使用启动脚本（推荐）**
```bash
python run_dashboard.py
```

**方法二：直接运行 Streamlit**
```bash
streamlit run streamlit_dashboard.py
```

### 3. 访问界面

启动成功后，在浏览器中访问：
```
http://localhost:8501
```

## 🎮 使用指南

### 基本操作

1. **设置玩家ID**: 在左侧边栏输入要监控的玩家ID
2. **模拟行为**: 在右侧面板点击不同类型的行为按钮
3. **查看分析**: 在中央面板观察Agent系统的实时分析过程
4. **监控状态**: 在左侧面板查看玩家状态的实时更新

### 行为类型说明

#### 😊 积极情绪场景
- 玩家成功通关困难副本
- 玩家获得稀有装备
- 玩家升级成功
- 玩家完成成就

#### 😞 消极情绪场景
- 发布消极评论
- 突然不充了
- 不买月卡了
- 玩家点击退出游戏

#### ⚠️ 流失风险场景
- 玩家连续3天未登录
- 玩家游戏时长急剧下降
- 玩家停止充值行为
- 玩家卸载游戏客户端

#### 🤖 机器人行为场景
- 玩家操作频率异常高
- 玩家24小时在线
- 玩家行为模式过于规律
- 玩家响应时间异常快

## 🔧 系统架构

### 核心组件

- **GamePlayerMonitoringSystem**: 主系统协调器
- **BehaviorMonitor**: 行为监控器，管理阈值触发
- **PlayerStateManager**: 玩家状态管理器
- **PlayerBehaviorSimulator**: 行为模拟器
- **GameMonitoringTeam**: 多智能体团队

### 工作流程

1. **行为生成**: 用户点击按钮 → 生成 PlayerBehavior 对象
2. **阈值检测**: BehaviorMonitor 检查是否达到分析阈值
3. **智能体分析**: 触发 MagenticOneGroupChat 多智能体协作
4. **状态更新**: 更新 PlayerState 中的各项指标
5. **界面刷新**: Streamlit 自动更新显示最新状态

## 📊 监控指标

### 玩家状态指标

- **情绪状态**: 当前情绪类型及置信度
- **流失风险**: 风险等级和风险分数
- **机器人检测**: 是否为机器人及置信度
- **行为历史**: 最近5条行为记录

### 系统状态指标

- **总行为记录数**: 系统记录的所有行为数量
- **监控阈值**: 触发分析的负面行为阈值
- **玩家负面计数**: 各玩家的当前负面行为计数

## 🛠️ 自定义配置

### 修改监控阈值

在 `BehaviorMonitor` 初始化时可以设置阈值：
```python
monitor = BehaviorMonitor(threshold=3)  # 设置阈值为3
```

### 添加新的行为场景

在 `PlayerBehaviorSimulator` 中添加新的场景：
```python
self.custom_scenarios = [
    "自定义行为1",
    "自定义行为2",
    # ...
]
```

### 自定义样式

修改 `streamlit_dashboard.py` 中的 CSS 样式部分来自定义界面外观。

## 🐛 故障排除

### 常见问题

1. **依赖包缺失**
   ```bash
   pip install -r requirements_streamlit.txt
   ```

2. **端口被占用**
   ```bash
   streamlit run streamlit_dashboard.py --server.port=8502
   ```

3. **异步函数问题**
   - 确保使用了 `run_async()` 包装器
   - 检查 `nest_asyncio` 是否正确安装

4. **系统初始化失败**
   - 检查 `config.py` 中的模型配置
   - 确保所有必要的环境变量已设置

### 调试模式

启用 Streamlit 调试模式：
```bash
streamlit run streamlit_dashboard.py --logger.level=debug
```

## 📝 开发说明

### 文件结构

```
├── streamlit_dashboard.py      # 主 Dashboard 文件
├── run_dashboard.py           # 启动脚本
├── requirements_streamlit.txt # Streamlit 依赖
└── STREAMLIT_README.md       # 本文档
```

### 扩展开发

1. **添加新的可视化组件**: 在相应的列中添加 Streamlit 组件
2. **集成新的分析功能**: 扩展 Agent 系统并在界面中展示
3. **优化用户体验**: 改进布局、样式和交互逻辑

## 📄 许可证

本项目遵循与主项目相同的许可证。

---

🎮 **享受游戏监控系统的强大功能！**