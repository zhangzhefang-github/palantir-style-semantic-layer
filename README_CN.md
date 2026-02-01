# Palantir 风格语义控制面

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=flat-square&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-158%20passed-success?style=flat-square)](tests/)
[![演示文稿](https://img.shields.io/badge/📊_在线演示-查看幻灯片-00d4ff?style=flat-square)](https://zhangzhefang-github.github.io/palantir-style-semantic-layer/presentation.html)

**语义层运行时控制面参考架构 POC**

[English](README.md) | [中文](README_CN.md)

<br>

<a href="https://zhangzhefang-github.github.io/palantir-style-semantic-layer/presentation.html">
  <img src="https://img.shields.io/badge/🎬_交互式演示文稿-点击查看-1a1a2e?style=for-the-badge&labelColor=0f3460" alt="查看演示"/>
</a>

<sub>14 页幻灯片 · 使用 ← → 键翻页 · 支持移动端</sub>

</div>

---

## 🔥 30 秒了解这个项目

> **把企业语义变成运行时可校验能力：能选版本、能追溯、能拒答。**

### 解决什么痛点？

- 😤 **口径冲突**：财务说毛利率 23.5%，销售说 28.2%，老板问"到底是多少？" → 系统自动选版本 + 完整审计链
- 🚫 **AI 乱说**：Agent 给出"广告无效"的因果结论 → Fail-Closed 机制拒绝回答弱关联推断
- 🔄 **数仓迁移恐惧**：改一张表要改几十个报表 → 只改 `physical_mapping`，逻辑层零改动

### 和"指标平台/语义层/Agent SQL 生成器"区别？

| 工具类型 | 核心能力 | 本项目差异 |
|---------|---------|----------|
| 指标平台 | 定义 + 展示 | ✅ 本项目：**运行时版本选择 + 场景匹配** |
| 语义层 | 逻辑/物理分离 | ✅ 本项目：**Fail-Closed + 归因约束** |
| Agent SQL | 自然语言转 SQL | ✅ 本项目：**15 步决策链完全可审计** |

### 适合谁？

`数据平台负责人` · `BI/治理团队` · `AI 落地负责人` · `对 Palantir 架构感兴趣的工程师`

### ⚡ 一键体验（3 分钟跑通）

```bash
git clone https://github.com/zhangzhefang-github/palantir-style-semantic-layer.git && cd palantir-style-semantic-layer && pip install -r requirements.txt && python3 demo_detailed_logs.py
```

<details>
<summary>📸 点击查看示例输出</summary>

```
✅ 状态: SUCCESS
✅ Semantic Object: FPY
✅ Version: FPY_v2_rework
✅ Logic: (good_qty + rework_qty) / total_qty
✅ Data: [{'fpy': 0.9866666666666667}]
✅ Audit ID: 20260201_074628_9378a39e
✅ 决策链: 15 步完整记录
```

</details>

---

## 📋 目录

- [项目概述](#-项目概述)
- [核心特性](#-核心特性)
- [系统架构](#-系统架构)
- [快速开始](#-快速开始)
- [使用指南](#-使用指南)
- [数据库模式](#-数据库模式)
- [核心模块](#-核心模块)
- [设计原则](#-设计原则)
- [企业级能力](#-企业级能力)
- [项目状态](#-项目状态)
- [文档索引](#-文档索引)
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
指标依赖和实体映射支持影响分析，包含：
- `build_dependency_graph()` - 构建 DAG 依赖图
- `impact()` - 分析变更影响范围
- `diff()` - 对比两个版本差异
- `generate_report()` - 生成影响分析报告（含风险评估）

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
│            语义控制面 (13 张业务表)                               │
│                                                                 │
│  ┌─ 核心执行表 (6 张) ─────────────────────────────────────┐     │
│  │ semantic_object    │ semantic_version │ logical_definition│   │
│  │ physical_mapping   │ access_policy    │ execution_audit   │   │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─ 本体论 & 治理表 (7 张) ────────────────────────────────┐     │
│  │ ontology_entity    │ ontology_dimension│ ontology_attribute│  │
│  │ ontology_relationship │ metric_entity_map │ metric_dependency│ │
│  │ term_dictionary    │                   │                    │  │
│  └─────────────────────────────────────────────────────────┘    │
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

### 真实场景：跨部门口径冲突

**问题**：财务总监问"上月华东区毛利率是多少？"
- 财务部计算：`(收入 - 总成本) / 收入 = 23.5%`
- 销售部计算：`(收入 - 直接成本) / 收入 = 28.2%`
- 老板：**"到底是多少？为什么有两个数？"**

**解决方案**：语义控制面根据场景上下文自动识别使用哪个版本。

### 基础查询

```python
from semantic_layer.orchestrator import SemanticOrchestrator
from semantic_layer.models import ExecutionContext
from datetime import datetime

# 初始化
orchestrator = SemanticOrchestrator('data/semantic_layer.db')

# 设置执行上下文（财务部门）
context = ExecutionContext(
    user_id=1,
    role='finance_manager',
    timestamp=datetime.now()
)

# 执行带部门上下文的查询
result = orchestrator.query(
    question="上月华东区毛利率是多少？",
    parameters={
        'region': '华东',
        'period': '2026-01',
        'scenario': {'department': 'finance'}  # 指定使用哪个版本
    },
    context=context
)

print(f"结果: {result['data']}")  # {'gross_margin': 0.235}
print(f"版本: {result['version']}")  # GrossMargin_v1_finance
print(f"审计ID: {result['audit_id']}")
```

### 查询响应结构

```json
{
    "data": [{"gross_margin": 0.235}],
    "decision_trace": [
        {"step": "resolve_semantic_object_complete", "data": {"semantic_object_reason": "匹配到毛利率"}},
        {"step": "resolve_version_complete", "data": {"version_selection_reason": "选择财务口径版本"}},
        {"step": "resolve_logic_complete", "data": {"logic_expression": "(revenue - total_cost) / revenue"}},
        {"step": "resolve_physical_mapping_complete", "data": {"physical_mapping_reason": "..."}},
        {"step": "render_sql_complete", "data": {"sql_preview": "SELECT ..."}},
        {"step": "execution_complete", "data": {"row_count": 1}}
    ],
    "audit_id": "20260128_163122_428e7cce"
}
```

**关键点**：系统准确记录了使用哪个版本、为什么选择它、以及完整的计算逻辑——实现完全可审计。

---

## 🗄️ 数据库模式

### 概览：13 张业务表 + 1 张 Mock 数据表

语义控制面采用**双层表架构**：

| 层级 | 数量 | 用途 |
|------|------|------|
| 核心执行层 | 6 张 | 查询执行管道 |
| 本体论 & 治理层 | 7 张 | 语义建模 & 影响分析 |
| Mock 数据 | 1 张 | 演示用物理数据 |

### 第一层：核心执行表 (6 张)

| 表名 | 用途 | 关键字段 |
|------|------|----------|
| `semantic_object` | 存在**什么**业务概念 | `name`, `aliases`, `description` |
| `semantic_version` | **哪个**版本适用 | `effective_from`, `scenario_condition`, `priority` |
| `logical_definition` | **如何**计算 | `expression`, `unit`, `aggregation_type` |
| `physical_mapping` | 数据在**哪里** | `sql_template`, `engine_type`, `connection_ref` |
| `access_policy` | **谁**可以做什么 | `role`, `action`, `conditions` |
| `execution_audit` | **为何**做出决策 | `decision_trace`, `final_sql`, `parameters` |

### 第二层：本体论 & 治理表 (7 张)

| 表名 | 用途 | 关键字段 |
|------|------|----------|
| `ontology_entity` | 核心业务实体 | `name`, `domain`, `description` |
| `ontology_dimension` | 实体维度（切分轴） | `entity_id`, `name`, `data_type` |
| `ontology_attribute` | 实体属性 | `entity_id`, `name`, `is_key` |
| `ontology_relationship` | 实体关系 | `from_entity_id`, `to_entity_id`, `cardinality` |
| `metric_entity_map` | 指标-实体映射 | `metric_id`, `entity_id`, `grain_level` |
| `metric_dependency` | 指标 DAG 边 | `upstream_metric_id`, `downstream_metric_id` |
| `term_dictionary` | 术语标准化 | `term`, `normalized_term`, `language` |

### Mock 数据表 (1 张)

| 表名 | 用途 |
|------|------|
| `fact_production_records` | 演示用生产数据 |

---

## 🧩 核心模块

### 语义层 (`src/semantic_layer/`)

| 模块 | 用途 |
|------|------|
| `orchestrator.py` | 核心编排器 - 协调所有解析步骤 |
| `semantic_resolver.py` | 语义对象 & 版本解析 |
| `policy_engine.py` | RBAC + ABAC 策略执行 |
| `execution_engine.py` | SQL 渲染 & 执行 |
| `models.py` | 数据模型 (6 个核心类 + 异常) |
| `impact_analysis.py` | **基于 DAG 的影响分析 & 版本对比** |
| `scenario_matcher.py` | 场景条件匹配 |
| `grain_validator.py` | 指标粒度验证 |
| `dependency_builder.py` | 依赖图构建 |
| `interfaces.py` | 抽象接口 |
| `sqlite_stores.py` | SQLite 元数据存储实现 |
| `config.py` | 配置管理 |

### 治理 (`src/governance/`)

| 模块 | 用途 |
|------|------|
| `approval_package.py` | 变更治理的审批包生成 |

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
| 测试覆盖 | ✅ 158 个测试通过，0 个跳过 |
| 冲突安全 | ✅ 基于优先级的确定性解决 |

---

## 📊 项目状态

> **注意**: 这是一个**参考架构 POC**，不是生产就绪系统。

### ✅ 已实现

- 端到端语义查询执行
- 策略强制执行 (RBAC + ABAC)
- 审计和重放
- 预览模式
- 歧义检测
- 版本选择（场景 + 优先级）
- SQL 模板渲染
- **本体建模（实体/维度/属性/关系）**
- **影响分析（基于 DAG）**
- **术语字典标准化**

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
│   ├── semantic_layer/           # 核心语义控制面
│   │   ├── orchestrator.py       # 核心编排器
│   │   ├── semantic_resolver.py  # 语义解析
│   │   ├── policy_engine.py      # 策略执行
│   │   ├── execution_engine.py   # SQL 执行
│   │   ├── models.py             # 数据模型
│   │   ├── impact_analysis.py    # 影响分析 (DAG)
│   │   ├── scenario_matcher.py   # 场景匹配
│   │   ├── grain_validator.py    # 粒度验证
│   │   ├── dependency_builder.py # 依赖构建
│   │   ├── interfaces.py         # 接口定义
│   │   ├── sqlite_stores.py      # SQLite 存储
│   │   └── config.py             # 配置
│   └── governance/
│       └── approval_package.py   # 审批包生成
├── tests/
│   ├── e2e/                      # 端到端测试
│   ├── approval/                 # 审批测试
│   ├── consistency/              # 一致性测试
│   ├── performance/              # 性能测试
│   ├── snapshots/                # 快照测试
│   ├── test_enterprise_challenges.py
│   ├── test_impact_analysis.py
│   └── ...
├── docs/
│   └── validation/               # 验证产物
├── data/                         # SQLite 数据库
├── schema.sql                    # 数据库结构 (13 张表)
├── seed_data.sql                 # 种子数据
├── demo_queries.py               # 交互式演示
├── demo_detailed_logs.py         # 详细日志演示
└── manual_test.py                # 手动验证脚本
```

---

## 📚 文档索引

| 文档 | 说明 |
|------|------|
| [`QUICKSTART.md`](QUICKSTART.md) | 5 分钟快速启动指南 |
| [`MODELING_GUIDE.md`](MODELING_GUIDE.md) | 语义建模规范 |
| [`TESTING_GUIDE.md`](TESTING_GUIDE.md) | 测试验证指南 |
| [`DETAILED_LOGS_GUIDE.md`](DETAILED_LOGS_GUIDE.md) | 详细日志演示指南 |
| [`PROJECT_SUMMARY.md`](PROJECT_SUMMARY.md) | 项目完成报告 |
| [`VALIDATION_PLAN.md`](VALIDATION_PLAN.md) | 变更场景测试集 |
| [`REPORT_REVIEW_CHECKLIST.md`](REPORT_REVIEW_CHECKLIST.md) | 报告评审清单 |
| [`PILOT_ACCEPTANCE_REPORT_TEMPLATE.md`](PILOT_ACCEPTANCE_REPORT_TEMPLATE.md) | 试点验收报告模板 |
| [`tests/README.md`](tests/README.md) | 测试套件文档 |
| [`tests/TEST_REPORT.md`](tests/TEST_REPORT.md) | 测试报告 |

---

## 🤝 参与贡献

欢迎贡献！请确保你的改动：

1. **最小化** - 保持改动聚焦
2. **充分测试** - 为新功能添加测试
3. **符合范围** - 保持在 POC 范围内

### 开发命令

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试类别
pytest tests/test_enterprise_challenges.py -v  # 企业挑战测试
pytest tests/test_impact_analysis.py -v        # 影响分析测试
pytest tests/test_e2e.py -v                    # 端到端测试

# 运行手动验证
python manual_test.py

# 运行详细日志演示
python demo_detailed_logs.py
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
