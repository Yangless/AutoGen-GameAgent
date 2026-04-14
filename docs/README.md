# 游戏Agent监控系统重构文档

本文档集合了游戏玩家行为监控系统的完整重构计划，涵盖四个核心架构方向的改进。

---

## 📚 文档导航

| 文档 | 说明 | 优先级 |
|------|------|--------|
| [refactoring-plan.md](./refactoring-plan.md) | 重构总体规划与架构设计 | **必读** |
| [iteration-1-dependency-injection.md](./iteration-1-dependency-injection.md) | 迭代1: 依赖注入实施指南 | P0 |
| [iteration-2-rules-engine.md](./iteration-2-rules-engine.md) | 迭代2: 规则引擎插件化 | P1 |
| [iteration-3-ui-separated.md](./iteration-3-ui-separated.md) | 迭代3: UI与业务分离 | P1 |

---

## 🎯 重构概览

### 重构目标

将现有的紧耦合系统重构为以下架构：

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Streamlit  │  │   Console   │  │    Future APIs      │ │
│  │      UI     │  │      UI     │  │   (REST, CLI...)    │ │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘ │
└─────────┼────────────────┼─────────────────────┼────────────┘
          │                │                     │
          └────────────────┴─────────────────────┘
                           │
                   ┌───────▼────────┐
                   │   Application  │
                   │   Services     │
                   └───────┬────────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
    ┌──────▼─────┐  ┌──────▼─────┐  ┌─────▼──────┐
    │   Domain   │  │   Rules    │  │Monitoring  │
    │   Models   │  │   Engine   │  │   & State   │
    └──────┬─────┘  └──────┬─────┘  └──────┬─────┘
           │               │               │
           └───────────────┼───────────────┘
                           │
                   ┌───────▼────────┐
                   │ Infrastructure  │
                   │ (Containers, IO) │
                   └──────────────────┘
```

### 四大重构方向

#### 1. 解耦全局依赖 → 领域上下文
**当前问题**
```python
# 全局变量存在耦合和测试问题
global _monitor, _player_state_manager
def analyze(player_id):
    monitor = get_global_monitor()  # 隐式依赖
```

**目标架构**
```python
# 显式传递上下文
class AnalysisTool:
    def __init__(self, context: GameContext):  # 显式依赖
        self.context = context
```

#### 2. 依赖注入 → DI容器
**当前问题**
- 直接实例化依赖
- 调用链中层层传递

**目标架构**
```python
container = DIContainer()
container.register_class(BehaviorMonitor)

monitor = container.resolve(BehaviorMonitor)  # 自动注入
```

#### 3. 规则引擎插件化
**当前问题**
- 11条规则硬编码
- 无法动态扩展

**目标架构**
```python
@register_rule
def consecutive_failures(actions):
    if actions.count_consecutive('fail') >= 2:
        return TriggeredScenario(...)
```

#### 4. UI业务分离
**当前问题**
- `streamlit_dashboard.py` 720+行，混杂逻辑
- 测试困难

**目标架构**
```
application/services/    # 业务逻辑
ui/components/          # 展示逻辑
ui/adapters/          # Streamlit适配
```

---

## 📅 重构路线图

### 阶段1: 基础设施 (Week 1-2)
**里程碑**: DI容器可工作

- [x] 设计文档
- [ ] 实现 `core/container.py`
- [ ] 实现 `core/context.py`
- [ ] 创建 `repositories/` 抽象
- [ ] 编写启动脚本
- [ ] 集成测试

### 阶段2: 规则引擎 (Week 3-4)
**里程碑**: 新规则引擎替代旧版

- [ ] 创建 `rules/` 架构
- [ ] 实现规则基类
- [ ] 迁移11条规则
- [ ] 自动加载器
- [ ] 性能对比测试

### 阶段3: UI重构 (Week 5-7)
**里程碑**: Dashboard代码减半

- [ ] 创建应用服务
- [ ] 组件分离
- [ ] 迁移 Streamlit 代码
- [ ] 添加 Presenter 层
- [ ] 端到端测试

### 阶段4: 清理迁移 (Week 8)
**里程碑**: 删除兼容层

- [ ] 移除全局变量
- [ ] 删除废弃代码
- [ ] 性能基准测试
- [ ] 文档更新

---

## 📊 验收标准

### 功能完整性
- [ ] 原有功能100%保留
- [ ] 多玩家支持
- [ ] 规则触发正常
- [ ] Agent干预正常

### 代码质量
- [ ] 单元测试覆盖率80%+
- [ ] 代码行数减少30%
- [ ] 函数复杂度降低
- [ ] 类型注解覆盖率100%

### 性能指标
- [ ] 规则执行时间 ≤ 旧版
- [ ] 内存使用 ≤ 旧版
- [ ] 启动时间 ≤ 旧版

### 维护性
- [ ] 新增规则 < 5分钟
- [ ] 定位bug < 10分钟
- [ ] 理解代码 < 30分钟

---

## 🔧 快速开始

### 按迭代开发

```bash
# 1. 准备开发目录
mkdir -p core application/ui/repositories

# 2. 从迭代开始
# 参考 iteration-1-dependency-injection.md 开始第1天任务

# 3. 验证测试
pytest tests/core/test_container.py -v

# 4. 继续下一迭代
```

### 代码规范

```python
# ✅ 依赖注入风格
class MyService:
    def __init__(self, monitor: BehaviorMonitor):
        self.monitor = monitor

# ❌ 避免全局依赖
class MyService:
    def __init__(self):
        self.monitor = get_global_monitor()  # 不要


# ✅ 组件纯函数风格
def PlayerCard(props: PlayerProps) -> Component:
    return html.div([
        html.h1(props.name),
        html.p(f"等级: {props.level}")
    ])

# ❌ 避免业务逻辑与UI混合
def render_player():
    player = query_database()  # 不要
    st.write(player.name)
```

---

## 📖 设计决策

### 为何不使用成熟框架？

| 考虑因素 | 自研轻量DI | 使用框架(如 injector) |
|---------|-----------|-------------------|
| 学习成本 | 低（团队已知） | 中高 |
| 定制性 | 完全可控 | 受限 |
| 代码依赖 | 0 | +1 |
| 实现时间 | 2天 | 半天 |
| 维护风险 | 低（简单） | 低（成熟） |

**决策**: 使用自研轻量DI，200行以内搞定

### 为何使用 Protocol 而非 ABC？

```python
# Protocol - 鸭子类型
class PlayerView(Protocol):
    def get_name(self) -> str: ...

# 任何实现get_name的对象都可以
# 无需显式继承
```

**决策**: View层使用Protocol，更灵活；核心 domain 使用ABC显式约束

---

## 📂 文件结构

```
docs/
├── README.md                          # 本文档
├── refactoring-plan.md                # 总体规划
├── iteration-1-dependency-injection.md # DI迭代
├── iteration-2-rules-engine.md        # 规则引擎迭代
└── iteration-3-ui-separated.md        # UI分离迭代
```

---

## 🤝 贡献指南

### 提交规范

```
[重构] 添加DI容器
[规则] 迁移连续失败规则
[UI] 分离PlayerStatusPanel
[文档] 更新迭代指南
```

### 代码审查检查清单

1. ✅ 是否使用依赖注入？
2. ✅ 是否有单元测试？
3. ✅ 是否更新了文档？
4. ✅ 是否保持了向后兼容？

---

## 📞 支持

### 迁移问题

常见问题见各迭代文档 "FAQ" 章节

### 设计问题

- 架构讨论: 创建 Issue，标记 `architecture`
- 技术选型: 创建 Issue，标记 `technical-debt`

---

## 📜 协议

MIT License

---

**最后更新**: 2026-04-13
