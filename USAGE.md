# 游戏玩家行为分析系统 - 使用指南

## Streamlit 应用
python -m streamlit run streamlit_dashboard.py --server.port=8502 

## mlflow ui 使用
mlflow ui

## 数据生成模式

系统支持两种数据生成模式，可以通过参数控制启动方式：

### 1. 随机生成模式 (Random Mode)

**特点：**
- 实时随机生成玩家行为数据
- 模拟真实的游戏环境
- 适合长时间监控测试

**使用方法：**
```bash
# 默认随机模式，持续60秒
python main.py

# 指定随机模式，持续30秒
python main.py random mixed 30
```

### 2. 预设序列模式 (Preset Mode)

**特点：**
- 使用预先生成的行为数据集
- 可控制数据类型和场景
- 适合特定场景测试和演示

**数据集类型：**
- `negative`: 负面行为为主的数据集（流失风险、情绪低落等）
- `positive`: 正面行为为主的数据集（活跃参与、情绪积极等）
- `mixed`: 混合数据集（包含各种行为类型）

**使用方法：**
```bash
# 预设模式，负面数据集，持续30秒
python main.py preset negative 30

# 预设模式，正面数据集，持续45秒
python main.py preset positive 45

# 预设模式，混合数据集，持续60秒
python main.py preset mixed 60
```

## 命令行参数说明

```bash
python main.py [mode] [dataset_type] [duration]
```

**参数说明：**
- `mode`: 数据生成模式
  - `random`: 随机生成模式
  - `preset`: 预设序列模式
- `dataset_type`: 数据集类型（仅在preset模式下有效）
  - `negative`: 负面行为数据集
  - `positive`: 正面行为数据集
  - `mixed`: 混合数据集
- `duration`: 会话持续时间（秒）

## 使用示例

### 场景1：测试系统基本功能
```bash
# 使用随机模式，快速测试10秒
python main.py random mixed 10
```

### 场景2：测试负面情绪检测和干预
```bash
# 使用负面数据集，观察系统如何处理问题玩家
python main.py preset negative 30
```

### 场景3：测试正面行为识别
```bash
# 使用正面数据集，观察系统对活跃玩家的分析
python main.py preset positive 20
```

### 场景4：综合测试
```bash
# 使用混合数据集，测试系统的全面分析能力
python main.py preset mixed 60
```

## 测试脚本

系统还提供了专门的测试脚本 `test_modes.py`，可以自动测试两种模式：

```bash
python test_modes.py
```

该脚本会依次测试：
1. 随机生成模式（10秒）
2. 预设序列模式的三种数据集类型（每种5秒）

## 输出说明

系统运行时会显示：
- 📋 运行参数信息
- 📝 实时玩家行为数据
- 🤖 AI分析结果
- 📧 个性化干预邮件
- 🔄 系统状态更新

## 注意事项

1. **模式选择**：
   - 开发测试建议使用 `preset` 模式，数据可控
   - 演示展示建议使用 `random` 模式，更真实

2. **时间设置**：
   - 测试时建议使用较短时间（10-30秒）
   - 演示时可以使用较长时间（60秒以上）

3. **数据集选择**：
   - `negative` 数据集会触发更多干预行为
   - `positive` 数据集主要用于验证正面行为识别
   - `mixed` 数据集提供最全面的测试场景