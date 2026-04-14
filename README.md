# 游戏玩家实时行为监控助手

一个基于 AutoGen 多智能体框架的游戏玩家行为监控和自动干预系统。

## 🎯 系统概述

本仓库当前同时维护两条链路：
- **默认运行链路**：`GamePlayerMonitoringSystem` -> `GameMonitoringTeamV2` -> `SingleThreadedAgentRuntime` -> `OrchestratorAgent` / Workers
- **兼容运行链路**：`GamePlayerMonitoringSystem(use_v2_runtime=False)` -> `GameMonitoringTeam` -> `MagenticOneGroupChat`

系统覆盖的核心能力包括：
- **实时监控**：后台模拟并监控玩家行为
- **智能触发**：当负面指标达到预设阈值时自动触发分析
- **多智能体协作**：按不同分析职责拆分处理和响应
- **自动干预**：根据分析结果自动执行相应的干预措施

## 🏗️ 系统架构

### 新架构模块（v2.0）

仓库中已经实现面向高吞吐与可控输出的 Orchestrator-Worker 模块：

- `OrchestratorAgent`：接收玩家事件、生成任务、汇总多个 Worker 结果
- `EmotionWorker`：分析情绪并选择安抚策略
- `ChurnWorker`：评估流失风险并生成挽回方案
- `BehaviorWorker`：识别异常行为并给出管控措施
- `OutputValidator`：执行 JSON 提取、Pydantic 校验和自我修正重试
- `MemoryService`：提供短期窗口记忆和长期摘要压缩能力

### 核心特性

- 并行处理：面向三类 Worker 的任务拆分与结果合并
- 输出可控：Pydantic 校验加自我修正重试机制
- 状态隔离：基于 `session_id` 的事件和记忆隔离
- 记忆优化：短期窗口加长期摘要，降低上下文消耗

### 性能指标

| 指标 | 目标 | 当前验证 |
|------|------|----------|
| 处理能力 | ≥3000条/日 | 已添加验证测试 |
| 输出错误率 | ≤11% | 已添加验证测试 |
| Token消耗降低 | ≥55% | 已添加验证测试 |

说明：[`game_monitoring/system/game_system.py`](game_monitoring/system/game_system.py) 和 [`streamlit_dashboard.py`](streamlit_dashboard.py) 现在默认走 v2 runtime；新架构的验证通过 `tests/` 下的单元、集成和性能测试完成。部署与模块验证说明见 [docs/deployment/orchestrator-worker-deployment.md](docs/deployment/orchestrator-worker-deployment.md)。

### 默认运行时组件（v2）

1. **玩家行为模拟器** (`PlayerBehaviorSimulator`)
   - 模拟真实的玩家行为数据
   - 包含21种不同的玩家场景
   - 识别7种负面行为模式

2. **行为监控器** (`BehaviorMonitor`)
   - 实时监控玩家行为
   - 阈值触发机制（默认3次负面行为）
   - 维护玩家行为历史记录

3. **多智能体团队**
   - 默认入口使用 `GameMonitoringTeamV2`
   - 通过 `SingleThreadedAgentRuntime` 注册 orchestrator 和 3 个 workers
   - legacy `GameMonitoringTeam` 仍保留，可通过 `use_v2_runtime=False` 回退

### Legacy 兼容链路说明

#### 分析类智能体

1. **情绪识别智能体** (`EmotionRecognitionAgent`)
   - **功能**：分析玩家情绪状态
   - **输入**：玩家ID和行为历史
   - **输出**：情绪标签、置信度、触发关键词

2. **流失风险评估智能体** (`ChurnRiskAgent`)
   - **功能**：预测玩家流失风险
   - **输入**：玩家ID和行为历史
   - **输出**：风险等级、风险分数、关键影响因素

3. **机器人检测智能体** (`BotDetectionAgent`)
   - **功能**：识别异常的机器人行为
   - **输入**：玩家ID和行为历史
   - **输出**：是否为机器人、置信度、检测模式

4. **玩家状态聚合智能体** (`PlayerStateAgent`)
   - **功能**：整合各种分析结果
   - **输入**：玩家ID和各项分析数据
   - **输出**：玩家核心档案快照

5. **体力值耗尽引导智能体** (`StaminaGuideAgent`)
   - **功能**：当玩家体力值耗尽时，触发体力恢复引导
   - **支持操作**：提示玩家当前体力值、推荐使用的体力恢复道具、提示玩家如何使用道具恢复体力
   - **输出**：操作状态和事务ID

6. **军令个性化分发智能体** (`StaminaGuideAgent`)
   - **功能**：当玩家的体力值低于某个阈值时，触发军令个性化分发
   - **支持操作**：提示玩家当前体力值、推荐使用的军令道具、提示玩家如何使用道具恢复体力
   - **输出**：操作状态和事务ID

#### 干预类智能体

5. **参与度提升智能体** (`EngagementAgent`)
   - **功能**：执行激励和奖励操作
   - **支持操作**：发放道具、邮件奖励等
   - **输出**：操作状态和事务ID

6. **玩家引导智能体** (`GuidanceAgent`)
   - **功能**：提供引导和帮助
   - **支持操作**：弹窗提示、专属客服、攻略推送
   - **输出**：操作状态和事务ID

## 🎮 玩家场景库

系统包含丰富的玩家行为场景：

### 正常游戏行为
- 玩家登陆游戏
- 玩家打开副本
- 玩家迁城
- 玩家攻城/攻占土地
- 玩家加入家族/国家
- 玩家讨伐蛮族
- 玩家打开招募英雄
- 玩家跳转充值页面

### 负面行为指标
- 发布消极评论
- 突然不充了
- 不买月卡了
- 抽卡频率变低
- 玩家分解装备
- 玩家退出家族
- 玩家点击退出游戏

## 🛠️ 游戏功能库

系统支持的干预功能：
- 发邮件奖励
- 弹出加专属客服
- 弹幕安慰玩家
- 弹出攻略
- 推送活动通知
- 发放补偿道具
- 触发新手引导

## 🚀 快速开始

### 环境要求
- Python 3.10+
- UV 包管理器
- AutoGen 相关依赖
- Redis（用于记忆服务和相关验证）

### 安装和运行

```bash
# 克隆项目
git clone <repository-url>
cd AutoGen-GameAgent

# 安装依赖（如果需要）
uv sync

# 启动现有 Dashboard 入口
streamlit run streamlit_dashboard.py

# 运行自动化验证
uv run python -m pytest tests game_monitoring/tests/test_container.py -v
```

### 配置说明

在实际部署时，需要配置以下组件：

1. **OpenAI 客户端**：
```python
from autogen_ext.models.openai import OpenAIChatCompletionClient

model_client = OpenAIChatCompletionClient(
    model="gpt-4",
    api_key="your-api-key"
)
```

2. **新架构模块引导**：
```python
from game_monitoring.core.bootstrap import bootstrap_application

container = bootstrap_application(
    custom_model_client=model_client,
    setup_global_context=False,
)
orchestrator = container.resolve("OrchestratorAgent")
```

3. **兼容模式说明**：
   - 默认系统入口已经切到 `GameMonitoringTeamV2`
   - 如果需要回退旧链路，可在 `GamePlayerMonitoringSystem(use_v2_runtime=False)` 下使用 `GameMonitoringTeam`
   - 使用 legacy 团队时仍需要 `autogen_agentchat` 相关依赖

## 📊 默认运行流程（v2）

1. **行为生成**：系统持续模拟玩家行为
2. **实时监控**：监控器检查每个行为是否为负面行为
3. **阈值触发**：当玩家负面行为达到阈值（默认3次）时构造 `PlayerEvent`
4. **Orchestrator 编排**：`GameMonitoringTeamV2` 通过 runtime 将事件发送到 `OrchestratorAgent`
5. **Worker 执行**：
   - `EmotionWorker` 生成情绪安抚建议
   - `ChurnWorker` 生成流失挽回方案
   - `BehaviorWorker` 生成行为管控措施
6. **结果合并**：Orchestrator 聚合去重后的干预动作并返回最终决策

补充：legacy `MagenticOneGroupChat` 链路仍保留，但不再是默认执行路径。

## 🔧 自定义配置

### 调整监控阈值
```python
monitor = BehaviorMonitor(threshold=5)  # 设置为5次负面行为触发
```

### 添加新的玩家场景
```python
simulator.player_scenarios.append("新的玩家行为")
simulator.negative_behaviors.append("新的负面行为")
```

### 扩展游戏功能
```python
simulator.game_functions.append("新的游戏功能")
```

## 📈 监控输出示例

```
🎮 游戏Agent助手监控助手
==================================================
🎮 游戏Agent助手系统已初始化

🚀 开始模拟监控会话 (持续 60 秒)...

📝 玩家行为: player_3 - 玩家登陆游戏
📝 玩家行为: player_1 - 发布消极评论
📝 玩家行为: player_2 - 突然不充了
📝 玩家行为: player_1 - 不买月卡了
📝 玩家行为: player_1 - 玩家点击退出游戏
⚠️ 触发监控阈值: 玩家 player_1 负面行为达到 3 次

🔍 开始分析玩家 player_1...
📊 玩家 player_1 分析完成:
   情绪状态: 沮丧 (置信度: 0.85)
   流失风险: 高风险 (风险分数: 0.95)
   机器人嫌疑: 否 (置信度: 0.00)

🎯 为玩家 player_1 执行干预措施...
   ✅ 已为玩家发放补偿道具: success
   ✅ 已触发专属客服弹窗: success
🔄 已重置玩家 player_1 的负面行为计数
```

## 🎯 系统特点

- ✅ **实时响应**：毫秒级行为监控和分析
- ✅ **智能分析**：多维度玩家状态评估
- ✅ **自动干预**：基于分析结果的智能响应
- ✅ **可扩展性**：易于添加新的智能体和功能
- ✅ **模块化设计**：各组件独立，便于维护和测试
- ✅ **异步处理**：高效的并发处理能力

## 📝 注意事项

1. 当前版本使用模拟数据，实际部署时需要连接真实的游戏数据源
2. OpenAI API 密钥需要在生产环境中正确配置
3. 建议根据实际游戏类型调整行为场景和阈值设置
4. 系统设计支持水平扩展，可以根据玩家规模调整部署架构

## 🔮 未来扩展

- 集成真实游戏数据库
- 添加更多分析维度（社交网络分析、消费行为分析等）
- 实现更复杂的干预策略
- 添加 A/B 测试功能
- 集成机器学习模型进行预测优化
- 使用强化学习算法优化玩家行为和系统响应
