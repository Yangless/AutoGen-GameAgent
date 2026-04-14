# Orchestrator-Worker架构实施 - 剩余待办事项

**创建时间**: 2026-04-14
**实施计划**: `docs/superpowers/plans/2026-04-13-orchestrator-worker-architecture.md`
**当前进度**: Task 1 已完成，Task 2-19 待执行

---

## 执行状态

### ✅ 已完成任务

#### Task 1: Implement Message Protocols
- **状态**: 已完成
- **提交哈希**: be63c56
- **创建文件**:
  - `game_monitoring/domain/messages.py` - 消息协议定义
  - `tests/unit/domain/test_messages.py` - 单元测试
  - `tests/conftest.py` - 测试配置
- **验证**: 3个测试全部通过

---

### 🔄 待执行任务（按顺序）

#### Task 2: Implement Pydantic Schemas for Output Validation
**文件**:
- 创建: `game_monitoring/domain/schemas.py`
- 创建: `tests/unit/domain/test_schemas.py`

**步骤**:
1. 编写测试用例（验证EmotionWorkerOutput、ChurnWorkerOutput、BehaviorWorkerOutput）
2. 运行测试验证失败
3. 实现Pydantic Schema（包含字段验证、值范围检查）
4. 验证测试通过
5. 提交代码

**关键代码**: 参见计划文档 Task 2

---

#### Task 3: Implement OutputValidator Base Class
**文件**:
- 创建: `game_monitoring/infrastructure/validation/output_validator.py`
- 创建: `tests/unit/validation/test_output_validator.py`

**步骤**:
1. 编写测试（JSON提取、混合文本解析、无效输入处理）
2. 实现OutputValidator类（_extract_json方法）
3. 验证并提交

**关键功能**:
- 从纯JSON提取
- 从混合文本提取JSON
- 无效输入抛出异常

---

#### Task 4: Implement OrchestratorAgent
**文件**:
- 创建: `game_monitoring/agents/orchestrator.py`
- 创建: `tests/unit/agents/test_orchestrator.py`

**步骤**:
1. 测试任务生成逻辑（_generate_tasks）
2. 测试结果合并逻辑（_merge_results）
3. 实现OrchestratorAgent类
4. 验证并提交

**核心方法**:
- `_generate_tasks()` - 生成emotion/churn/behavior三类任务
- `_merge_results()` - 按优先级合并Worker响应

---

#### Task 5: Implement EmotionWorker
**文件**:
- 创建: `game_monitoring/agents/emotion_worker.py`
- 创建: `tests/unit/agents/test_emotion_worker.py`

**步骤**:
1. 测试情绪安抚策略决策（_decide_strategy）
2. 实现EmotionWorker类
3. 验证并提交

**策略映射**:
- 愤怒 → 高优先级（专属客服、补偿道具）
- 沮丧 → 中优先级（关怀邮件、小额奖励）
- 焦虑 → 低优先级（引导提示）

---

#### Task 6: Implement ChurnWorker and BehaviorWorker
**文件**:
- 创建: `game_monitoring/agents/churn_worker.py`
- 创建: `game_monitoring/agents/behavior_worker.py`
- 创建: `tests/unit/agents/test_churn_worker.py`
- 创建: `tests/unit/agents/test_behavior_worker.py`

**步骤**:
1. 编写两个Worker的测试
2. 实现流失挽回逻辑（风险评估 → 挽回计划）
3. 实现行为管控逻辑（机器人检测 → 管控措施）
4. 验证并提交

---

#### Task 7: Register Components in Bootstrap
**文件**:
- 修改: `game_monitoring/core/bootstrap.py:85-300`

**步骤**:
1. 编写集成测试（验证组件注册）
2. 在bootstrap中注册:
   - SingleThreadedAgentRuntime
   - OrchestratorAgent工厂
   - OutputValidator工厂
3. 验证并提交

**关键注册**:
```python
container.register_factory('OrchestratorAgent', ...)
container.register_factory('OutputValidator', ...)
```

---

#### Task 8: Replace MagenticOneGroupChat in Team Manager
**文件**:
- 修改: `game_monitoring/team/team_manager.py:25-80`
- 创建: `tests/integration/test_team_manager_integration.py`

**步骤**:
1. 编写集成测试（验证新架构使用）
2. 实现GameMonitoringTeamV2类
3. 替换旧的MagenticOneGroupChat
4. 验证并提交

**核心改动**:
- 使用AgentId("orchestrator", "default")
- trigger_analysis_and_intervention发送PlayerEvent

---

## Phase 2: Output Controllability Engineering

#### Task 9: Add Self-Correction Retry Mechanism
**文件**:
- 修改: `game_monitoring/infrastructure/validation/output_validator.py:1-85`
- 创建: `tests/unit/validation/test_output_validator_retry.py`

**步骤**:
1. 测试重试成功场景
2. 测试超过最大重试次数
3. 实现validate_output和_self_correction方法
4. 验证并提交

**关键功能**:
- 最多3次重试
- 动态调整temperature（每次降低0.1）
- 返回Pydantic验证对象

---

#### Task 10: Implement Output Metrics Monitoring
**文件**:
- 创建: `game_monitoring/infrastructure/monitoring/output_metrics.py`
- 创建: `tests/unit/monitoring/test_output_metrics.py`

**步骤**:
1. 测试记录成功/失败验证
2. 测试错误率计算
3. 测试平均重试次数
4. 实现OutputMetrics类
5. 验证并提交

**监控指标**:
- total_outputs
- validation_errors
- retry_counts
- get_error_rate()
- get_avg_retries()

---

## Phase 3: Long-term Memory Implementation

#### Task 11: Implement MemoryService Base
**文件**:
- 创建: `game_monitoring/infrastructure/memory/memory_service.py`
- 创建: `tests/unit/memory/test_memory_service.py`

**步骤**:
1. 测试追加短期记忆
2. 测试获取短期记忆
3. 实现ShortTermMemory、MemoryService类
4. 验证并提交

**关键功能**:
- append_short_term() - 追加到Redis Sorted Set
- get_short_term() - 获取滑动窗口记忆

---

#### Task 12: Implement Long-term Memory and Compression
**文件**:
- 修改: `game_monitoring/infrastructure/memory/memory_service.py:85-200`
- 创建: `tests/unit/memory/test_memory_compression.py`

**步骤**:
1. 测试更新长期记忆
2. 测试递归摘要压缩
3. 实现update_long_term、compress_history方法
4. 验证并提交

**压缩流程**:
- 获取短期记忆（最近5条）
- 获取现有长期摘要
- LLM生成新摘要（≤200字）
- 提取关键事件

---

#### Task 13: Integrate MemoryService into Bootstrap
**文件**:
- 修改: `game_monitoring/core/bootstrap.py:182-190`
- 创建: `tests/integration/test_memory_integration.py`

**步骤**:
1. 测试MemoryService在bootstrap注册
2. 注册MemoryService工厂
3. 验证并提交

---

## Performance Benchmarking and Validation

#### Task 14: Throughput Benchmark Test
**文件**:
- 创建: `tests/performance/test_throughput_benchmark.py`

**验证标准**: ≥3000条/日

**步骤**:
1. 编写吞吐量基准测试
2. 并发处理100个任务
3. 计算吞吐量
4. 验证达标并提交

---

#### Task 15: Error Rate Validation Test
**文件**:
- 创建: `tests/performance/test_error_rate_validation.py`

**验证标准**: ≤11%

**步骤**:
1. 模拟500条样本数据
2. 计算错误率
3. 验证达标并提交

---

#### Task 16: Token Reduction Validation Test
**文件**:
- 创建: `tests/performance/test_token_reduction.py`

**验证标准**: ≥55%

**步骤**:
1. 估算原始Token消耗（100条历史）
2. 估算优化后Token消耗（10条+摘要）
3. 计算降低比例
4. 验证达标并提交

---

## Final Integration and Deployment

#### Task 17: Update Documentation
**文件**:
- 创建: `docs/deployment/orchestrator-worker-deployment.md`

**内容**:
- 环境要求
- 安装依赖
- 配置Redis
- 启动应用示例
- 性能指标

---

#### Task 18: Final End-to-End Test
**文件**:
- 创建: `tests/integration/test_e2e_orchestrator_worker.py`

**步骤**:
1. 引导系统（bootstrap_application）
2. 构造玩家事件
3. 触发干预流程
4. 验证完整流程

---

#### Task 19: Update Project README
**文件**:
- 修改: `README.md`

**新增内容**:
- 架构改进说明（Orchestrator-Worker）
- 核心特性列表
- 性能对比表格
- 部署指南链接

---

## 执行方法

### 方式1: Subagent-Driven Development（推荐）

每个Task启动独立子代理执行，主会话在Task之间审查：

```python
# 使用Agent工具，subagent_type="general-purpose"
Agent(
    description="Execute Task N: [Task Name]",
    prompt="执行计划文档中的Task N，严格遵循TDD步骤..."
)
```

### 方式2: Inline Execution

在本会话中逐个执行，使用TaskCreate/TaskUpdate跟踪进度。

---

## 依赖关系

```
Task 1 (✅) → Task 2 → Task 3 → Task 4 → Task 5 → Task 6
                                        ↓
                                     Task 7 → Task 8

Task 3 → Task 9 → Task 10

Task 7 → Task 11 → Task 12 → Task 13

所有Phase完成后 → Task 14-16（性能验证）→ Task 17-19（文档）
```

---

## 关键验证标准

### 单元测试覆盖率
- 目标: ≥80%
- 工具: `pytest --cov=game_monitoring tests/`

### 性能指标
| 指标 | 目标 | 验证方法 |
|------|------|----------|
| 处理能力 | ≥3000条/日 | Task 14 |
| 错误率 | ≤11% | Task 15 |
| Token消耗 | ↓55% | Task 16 |

---

## 技术栈

- **AutoGen Core**: 0.4+
- **Redis**: 4.5+
- **Pydantic**: 2.0+
- **Python**: 3.10+

---

## 注意事项

1. **严格TDD**: 先写测试 → 运行验证失败 → 实现 → 验证通过 → 提交
2. **精确代码**: 使用计划文档中的完整代码，避免占位符
3. **提交规范**: 包含`Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>`
4. **Redis依赖**: Task 11-13需要Redis服务运行
5. **测试环境**: 确保Python路径正确（tests/conftest.py已配置）

---

## 后续执行指令

当您准备好继续时，使用以下指令：

```
请继续执行剩余任务，从Task 2开始，使用subagent-driven-development方式。
```

或指定具体任务：

```
执行Task 2: Implement Pydantic Schemas for Output Validation
```

---

**文档结束**

下次执行时，我会从这个文档恢复工作状态，确保所有19个任务按计划完成。
