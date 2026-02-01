# Palantir 风格语义控制面

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=flat-square&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-134%20passed-success?style=flat-square)](tests/)

**语义层运行时控制面参考架构 POC**

[English](README.md) | [中文](README_CN.md)

</div>

---

## 📋 目录

- [项目概述](#-项目概述)
- [核心特性](#-核心特性)
- [系统架构](#-系统架构)
- [快速开始](#-快速开始)
- [使用指南](#-使用指南)
- [数据库模式](#-数据库模式)
- [设计原则](#-设计原则)
- [企业级能力](#-企业级能力)
- [项目状态](#-项目状态)
- [参与贡献](#-参与贡献)
- [开源许可](#-开源许可)

---

## 🎯 项目概述

本 POC 验证一个核心命题：

> **企业语义能否成为"结构化的运行时能力"，而不是依赖人工协作做每次决策？**

### 本 POC 已验证能力

| 能力 | 说明 |
|------|------|
| ✅ 语义层成为运行时控制面 | 系统做出可执行决策 |
| ✅ Agent 可以"不再询问人类" | 所有治理都是结构化的，而非对话式的 |
| ✅ 数据仓库变更隔离 | 仅需更新 `physical_mapping`，不影响业务逻辑 |
| ✅ 完整审计链路 | 每个决策可追溯、可重放 |

### 本 POC 不覆盖的范围

| 不包含 | 原因 |
|--------|------|
| ❌ 数据质量问题 | 聚焦语义治理，而非数据清洗 |
| ❌ 主数据治理 | 与语义层是独立关注点 |
| ❌ 指标业务合理性 | Garbage in, garbage out 依然适用 |
| ❌ NLP 完美性 | 设计上使用简单关键词匹配 |

---

## ✨ 核心特性

### 1. 语义版本管理
支持基于时间和场景的指标定义版本化。

### 2. 逻辑与物理分离
业务逻辑与数据库无关；物理 schema 变更仅需更新 `physical_mapping`。

### 3. 歧义不猜测
返回结构化的歧义错误，要求明确澄清。

### 4. 完整审计链路
每次执行都完全可重现，包含完整决策轨迹。

### 5. Agent 就绪架构
所有治理都在系统结构中，而非对话中。

### 6. 本体建模
实体/维度/属性/关系表提供本体骨架。
详见 [`MODELING_GUIDE.md`](MODELING_GUIDE.md)。

### 7. 影响分析 (DAG)
指标依赖和实体映射支持影响分析。
使用 `impact()` 和 `diff_versions()` 进行基于 DAG 的治理。

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                     用户 / AGENT                                │
│  "昨天产线A的一次合格率是多少？"                                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              语义编排器 (SEMANTIC ORCHESTRATOR)                  │
│  • 协调所有解析步骤                                               │
│  • 强制执行决策结构                                               │
│  • 记录完整审计轨迹                                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│            语义控制面 (6 张核心表)                                │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ semantic_object │  │ semantic_version│  │logical_definition│ │
│  │   存在什么概念   │  │   哪个版本适用   │  │   如何计算      │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ physical_mapping│  │  access_policy  │  │ execution_audit │  │
│  │   数据在哪里     │  │   谁可以做什么   │  │   为何这样决策   │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│           物理执行引擎                                           │
│  • 用参数渲染 SQL 模板                                           │
│  • 对数据源执行查询                                               │
│  • 返回结构化结果                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 快速开始

### 先决条件

- Python 3.10+
- SQLite 3
- 操作系统: Linux / macOS / Windows (支持 WSL)

### 安装方式

<details>
<summary><b>方式 A: pip + venv</b></summary>

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 运行演示
python demo_queries.py
```

</details>

<details>
<summary><b>方式 B: uv (推荐，速度更快)</b></summary>

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

# 运行演示
python demo_queries.py
```

</details>

<details>
<summary><b>方式 C: Docker</b></summary>

```bash
docker build -t semantic-layer .
docker run --rm -it semantic-layer bash
# 在容器内:
python demo_queries.py
```

</details>

---

## 📖 使用指南

### 基础查询

```python
from semantic_layer.orchestrator import SemanticOrchestrator
from semantic_layer.models import ExecutionContext
from datetime import datetime

# 初始化
orchestrator = SemanticOrchestrator('data/semantic_layer.db')

# 设置执行上下文
context = ExecutionContext(
    user_id=1,
    role='operator',
    timestamp=datetime.now()
)

# 执行查询
result = orchestrator.query(
    question="昨天产线A的一次合格率是多少？",
    parameters={
        'line': 'A',
        'start_date': '2026-01-27',
        'end_date': '2026-01-27'
    },
    context=context
)

print(f"结果: {result['data']}")
print(f"审计ID: {result['audit_id']}")
```

### 查询响应结构

```json
{
    "data": [{"fpy": 0.95}],
    "decision_trace": [
        {"step": "resolve_semantic_object_complete", "data": {"semantic_object_reason": "..."}},
        {"step": "resolve_version_complete", "data": {"version_selection_reason": "..."}},
        {"step": "resolve_logic_complete", "data": {"logic_expression": "good_qty / total_qty"}},
        {"step": "resolve_physical_mapping_complete", "data": {"physical_mapping_reason": "..."}},
        {"step": "render_sql_complete", "data": {"sql_preview": "SELECT ..."}},
        {"step": "execution_complete", "data": {"row_count": 1}}
    ],
    "audit_id": "20260128_163122_428e7cce"
}
```

---

## 🗄️ 数据库模式

### 6 张核心表

| 表名 | 用途 | 关键字段 |
|------|------|----------|
| `semantic_object` | 存在**什么**业务概念 | `name`, `aliases`, `description` |
| `semantic_version` | **哪个**版本适用 | `effective_from`, `scenario_condition`, `priority` |
| `logical_definition` | **如何**计算 | `expression`, `unit`, `aggregation_type` |
| `physical_mapping` | 数据在**哪里** | `sql_template`, `engine_type`, `connection_ref` |
| `access_policy` | **谁**可以做什么 | `role`, `action`, `conditions` |
| `execution_audit` | **为何**做出决策 | `decision_trace`, `final_sql`, `parameters` |

---

## 📦 设计原则

### 1. 语义层与物理数据解耦

业务逻辑 (`logical_definition`) **不包含任何表名或 SQL**。

| 层级 | 示例 |
|------|------|
| **逻辑层** | `good_qty / total_qty` (纯业务公式) |
| **物理层** | `SELECT SUM(good_qty)/SUM(total_qty) FROM fact_production_records WHERE ...` |

### 2. 元数据驱动决策

所有可执行决策来自数据库表，**而非硬编码逻辑**：
- 版本选择基于 `semantic_version.effective_from` 和 `scenario_condition`
- 访问控制基于 `access_policy` 规则
- SQL 生成来自 `physical_mapping.sql_template`

### 3. 编排器无状态

`SemanticOrchestrator` 只负责编排流程，所有业务规则都在元数据中。
- Python 代码中无业务逻辑
- 通过添加数据库记录即可扩展
- 可测试且确定性

### 4. 歧义不猜测

当多个语义对象匹配查询时，系统**不会猜测**。
它返回结构化的歧义错误，要求明确澄清。

### 5. 完整审计链路

每次执行都记录完整决策轨迹，支持**可重放性**，用于调试和合规。

---

## 🛡️ 企业级能力

本 POC 已针对常见企业架构挑战进行加固。

### 版本冲突解决

```python
# 版本选择规则 (代码中强制执行):
# 1. 分数越高 → 匹配越好 (场景+时间 > 仅时间 > 无匹配)
# 2. 分数相等 → 优先级高者胜出
# 3. 仍然相等 → AmbiguityError (系统拒绝猜测)
```

### 流程变更隔离

```sql
-- 场景驱动的版本选择:
INSERT INTO semantic_version (version_name, scenario_condition, priority)
VALUES
  ('FPY_v1_standard', NULL, 0),                    -- 默认
  ('FPY_v2_rework', '{"rework_enabled": true}', 10); -- 返工场景
```

### 数据仓库迁移

```sql
-- 基于优先级的物理映射选择:
INSERT INTO physical_mapping (logical_definition_id, engine_type, connection_ref, priority)
VALUES 
  (1, 'sqlite', 'legacy_db', 1),      -- 旧的 (低优先级)
  (1, 'snowflake', 'new_wh', 10);     -- 新的 (高优先级, 自动选择)
```

### 就绪性检查清单

| 要求 | 状态 |
|------|------|
| 无静默失败 | ✅ 歧义 → 错误 |
| 不猜测 | ✅ 部分匹配 = 不匹配 |
| 无硬编码 | ✅ 所有决策来自元数据 |
| 完整审计 | ✅ 每一步可追溯 |
| 重放安全 | ✅ 相同 SQL，差异可解释 |
| 迁移无忧 | ✅ 物理变更隔离 |
| 测试覆盖 | ✅ 134 个测试通过，1 个跳过 |
| 冲突安全 | ✅ 基于优先级的确定性解决 |

---

## 📊 项目状态

> **注意**: 这是一个**参考架构 POC**，不是生产就绪系统。

### ✅ 已实现

- 端到端语义查询执行
- 策略强制执行
- 审计和重放
- 预览模式
- 歧义检测
- 版本选择
- SQL 模板渲染

### ⚠️ 已知限制

- 简单的基于关键词的 NLP
- 仅支持 SQLite
- 基础策略条件
- 无缓存层
- 无多数据源查询

---

## 🗂️ 项目结构

```
palantir-style-semantic-layer/
├── src/
│   ├── semantic_layer/       # 核心语义控制面模块
│   └── governance/           # 审批与治理产物工具
├── tests/                    # 单元/集成/E2E/快照测试
├── docs/
│   └── validation/           # 验证与验收产物
├── data/                     # SQLite 数据库
├── schema.sql                # 数据库结构
├── seed_data.sql             # 种子数据
├── VALIDATION_PLAN.md        # 变更场景测试集
├── REPORT_REVIEW_CHECKLIST.md
└── MODELING_GUIDE.md         # 本体建模指南
```

---

## 🤝 参与贡献

欢迎贡献！请确保你的改动：

1. **最小化** - 保持改动聚焦
2. **充分测试** - 为新功能添加测试
3. **符合范围** - 保持在 POC 范围内

### 开发命令

```bash
# 运行测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_enterprise_challenges.py -v
```

---

## 📄 开源许可

本项目作为参考架构 POC 提供，仅用于教育目的。

MIT 许可证 - 详见 [LICENSE](LICENSE)

---

<div align="center">

**记住: 本 POC 验证了语义可以成为结构化的运行时能力。**

用 ❤️ 为企业语义治理而作

</div>
