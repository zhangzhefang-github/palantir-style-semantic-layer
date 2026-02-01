# 📋 测试验证指南

本指南帮助你快速验证 Palantir-Style Semantic Control Plane 的企业级增强功能，并提供一份可重复执行的测试计划。

---

## ✅ 测试计划（Test Plan）

### 目标
- 确保重构后核心行为一致
- 覆盖端到端主链路（解析 → 版本 → 策略 → SQL → 执行 → 审计/回放）
- 保证测试结果可重复、可回归

### 范围与分层
1. **单元测试（Unit）**
   - 解析器：关键词/歧义/版本选择
   - 策略引擎：allow/deny/条件判断
   - 执行引擎：SQL 渲染、参数校验、执行结果
   - 场景匹配：优先级/冲突/全量匹配
2. **集成测试（Integration）**
   - `SemanticOrchestrator` 全链路成功/预览/拒绝/错误场景
3. **端到端测试（E2E）**
   - 自然语言 → SQL → 数据 → 审计 → replay
4. **回归测试（Regression）**
   - 每次结构调整或接口变更后运行全量 `pytest`

### 运行前提（稳定性保障）
- 使用 `schema.sql` + `seed_data.sql`
- 固定日期：
  - `2026-01-27`（Yesterday）
  - `2026-01-28`（Today）
- Python 3.10+，SQLite 3

### 执行清单
```bash
# 安装依赖（pip）
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 或使用 uv
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

# 全量测试
pytest

# 仅单元测试
pytest tests/test_models.py tests/test_semantic_resolver.py tests/test_policy_engine.py tests/test_execution_engine.py -q

# 仅集成 + E2E
pytest tests/test_integration.py tests/test_e2e.py -q
```

### 验收标准
- `pytest` 全部通过（允许 1 个明确 skip）
- 端到端查询 `status=success`
- 审计可回放，决策链完整

---

## 🚀 快速开始（3 分钟验证）

### 方法 1：一键运行所有测试

```bash
# 删除旧数据库（可选，确保干净环境）
rm -rf data/

# 运行完整测试套件
python3 -m pytest tests/ -v

# 预期输出：134 passed, 1 skipped
```

---

### 方法 2：手动验证测试（推荐）

```bash
# 运行手动验证脚本
python3 manual_test.py
```

**测试内容**：
- ✅ Scenario 驱动版本选择（无场景 → FPY_v1，有场景 → FPY_v2）
- ✅ 决策链完全可解释（14 个步骤，每个都有 reason）
- ✅ Replay 模式正确标记（replay_mode=True + replay_source_audit_id）
- ✅ 审计历史可查询

---

## 🧪 分项验证测试

### ✅ 测试 1：Priority 冲突解决

**目的**：证明当多个版本具有相同 scenario 时，系统会选择高 priority 版本

```bash
python3 -m pytest tests/test_enterprise_challenges.py::TestPriorityConflictResolution::test_higher_priority_wins_with_same_scenario -v -s
```

**验证点**：
- 创建两个版本：priority=5 和 priority=10
- 相同 scenario `{"region": "US"}`
- **系统应该选择 priority=10 的版本**
- 返回值应该是 0.99（不是 0.95）

---

### ✅ 测试 2：Ambiguity 检测

**目的**：证明系统拒绝猜测，当真正冲突时会抛出错误

```bash
python3 -m pytest tests/test_enterprise_challenges.py::TestAmbiguityDetection::test_ambiguous_versions_raise_error -v -s
```

**验证点**：
- 创建两个版本：相同的 scenario，相同的 priority
- **系统应该抛出 AmbiguityError**
- 返回 `status='error'`，`error_type='AmbiguityError'`
- 错误信息包含 2 个 candidates

**日志输出**：
```
WARNING  Multiple versions with score=0: ['FPY_v1_ambiguous_a', 'FPY_v2_ambiguous_b']
WARNING  RESOLUTION ERROR: Multiple versions have score=0 and priority=5
```

---

### ✅ 测试 3：Scenario 全量匹配

**目的**：证明系统拒绝 partial match，只接受全量匹配

```bash
python3 -m pytest tests/test_enterprise_challenges.py::TestScenarioFullMatch::test_partial_scenario_match_fails -v -s
```

**验证点**：
- 版本 A 的 scenario：`{"region": "US", "plant": "NY"}`
- 查询只提供部分参数：`{"region": "US"}`
- **系统不应该匹配版本 A**
- 应该回退到 default version（FPY_default）

**企业保障**：防止生产环境因"部分参数缺失"导致错误口径

---

### ✅ 测试 4：Physical Mapping 切换

**目的**：证明数仓迁移不需要修改代码

```bash
python3 -m pytest tests/test_enterprise_challenges.py::TestPhysicalMappingPortability::test_higher_priority_mapping_is_selected -v -s
```

**验证点**：
- 创建两个 physical mapping：
  - Mapping v1：priority=1（legacy，返回 0.85）
  - Mapping v2：priority=10（optimized，返回 0.92）
- **系统应该自动选择 priority=10 的 mapping**
- 返回值应该是 0.92（不是 0.85）
- 无需修改 orchestrator 或 logical_definition

**企业保障**："数仓团队可以更改 schema 而无需与业务逻辑所有者协调"

---

### ✅ 测试 5：Replay 决策链增强

**目的**：证明 Replay 使用原始 SQL，不重新解析

```bash
python3 -m pytest tests/test_e2e.py::TestE2EReplay::test_e2e_replay_produces_consistent_results -v -s
```

**验证点**：
- 执行查询并获取 audit_id
- Replay 该查询
- **Replay 的 decision_trace 应该包含**：
  - `replay_mode: True`
  - `replay_source_audit_id: <original_audit_id>`
  - `original_sql: <SQL from original query>`
  - `replay_reason: "Using original SQL without re-executing semantic resolution"`

**日志输出**：
```
INFO  Replay Mode: Using original SQL without re-resolution
```

**企业保障**："在相同数据快照下保证一致。若底层数据变更，结果变化属于预期行为。"

---

## 📊 覆盖率验证

```bash
# 生成覆盖率报告
python3 -m pytest tests/ --cov=orchestrator --cov-report=term-missing

# 预期输出：orchestrator.py - 100% (158/158 statements)
```

---

## 🔍 查看审计记录

```bash
# 运行测试后查看数据库中的审计记录
sqlite3 data/semantic_layer.db "SELECT audit_id, question, semantic_object_name, version_name, status FROM execution_audit ORDER BY executed_at DESC LIMIT 10;"
```

**预期输出**：
```
20260128_180447_bbb30d19|昨天产线A的一次合格率是多少？|FPY|FPY_v1_standard|success
20260128_180447_a83e810e|昨天产线A的一次合格率是多少？|FPY|FPY_v1_standard|success
```

---

## 🎯 企业质疑对照表

| 质疑 | 测试验证 | 状态 |
|------|---------|------|
| **如何保证不会选错版本？** | Priority 冲突解决 + Ambiguity 检测 | ✅ |
| **流程变化需要修改 Agent 代码吗？** | Scenario 驱动版本选择测试 | ✅ |
| **数仓迁移会破坏业务逻辑吗？** | Physical Mapping 切换测试 | ✅ |
| **系统敢算吗（可审计）？** | 决策链可解释性 + Replay 一致性 | ✅ |
| **Partial match 会意外触发吗？** | Scenario 全量匹配测试 | ✅ |

---

## 📝 验证检查清单

运行以下命令完成完整验证：

```bash
# 1. 清理环境
rm -rf data/

# 2. 运行手动测试（最直观）
python3 manual_test.py

# 3. 运行企业质疑测试（新增功能）
python3 -m pytest tests/test_enterprise_challenges.py -v

# 4. 运行 E2E 测试（端到端）
python3 -m pytest tests/test_e2e.py -v

# 5. 检查覆盖率
python3 -m pytest tests/ --cov=orchestrator --cov-report=term-missing

# 6. 查看测试统计
python3 -m pytest tests/ --co -q
```

**预期结果**：
- ✅ manual_test.py：所有 4 个测试通过
- ✅ test_enterprise_challenges.py：5/5 测试通过
- ✅ test_e2e.py：12/12 测试通过
- ✅ 覆盖率：orchestrator.py 100%
- ✅ 总计：134 passed, 1 skipped

---

## 🚨 常见问题

### Q1: 测试失败 "no such table"

**解决**：删除 data/ 目录后重新运行测试
```bash
rm -rf data/
python3 -m pytest tests/ -v
```

### Q2: 导入错误 "No module named 'pytest'"

**解决**：安装 pytest
```bash
pip3 install pytest pytest-cov
```

### Q3: Scenario 不生效

**检查**：确保 scenario 是嵌套对象
```python
# ❌ 错误写法
parameters={'line': 'A', 'rework_enabled': True}

# ✅ 正确写法
parameters={'line': 'A', 'scenario': {'rework_enabled': True}}
```

---

## 📚 相关文档

- [README.md](README.md) - 项目概述和架构
- [README.md#L220-L353](README.md#L220-L353) - "Why this POC survives enterprise challenges"
- [tests/test_enterprise_challenges.py](tests/test_enterprise_challenges.py) - 企业质疑测试代码
- [manual_test.py](manual_test.py) - 手动验证脚本

---

**验证完成！** 🎉

你现在有了一个可运行、可解释、可复盘、可迁移的企业级语义控制面 Reference Architecture。
