# Palantir-Style Semantic Control Plane

**A Reference Architecture POC for Semantic Layer as a Runtime Control Plane**  
**语义层运行时控制面参考架构 POC**

> This README is bilingual (EN/中文).  
> 本文档为中英双语（EN/中文）。

---

## 🎯 Project Vision / 项目愿景

This POC validates a fundamental proposition:  
本 POC 验证一个关键命题：

> **Can enterprise semantics become a structural, runtime capability rather than relying on human collaboration for every decision?**  
> **企业语义能否成为“结构化的运行时能力”，而不是依赖人工协作做每次决策？**

### Core Validation Goals / 核心验证目标

This project demonstrates whether the following capabilities can exist as **system structures** rather than **LLM improvisations**:  
该项目验证以下能力是否能作为**系统结构**而非**LLM 临时推理**存在：

1. **Metric Definition** → What is "FPY" (First Pass Yield)?
2. **Version Management** → Which calculation version applies to this scenario?
3. **Logical Definition** → How is it calculated (business logic)?
4. **Physical Mapping** → Where is the data (SQL implementation)?
5. **Access Control** → Who is allowed to query this metric?
6. **Audit & Replay** → Why was this result produced? Can we replay it?

### What This POC Validates / 本 POC 已验证内容

✅ **Semantic layer can become a runtime control plane** - System makes executable decisions
✅ **Agents can "stop asking humans"** - All governance is structural, not conversational
✅ **Data warehouse changes are isolated** - Only update `physical_mapping`, not business logic
✅ **Full audit trail** - Every decision is traceable and replayable

### What This POC Does NOT Address / 本 POC 不覆盖的内容

❌ Data quality issues
❌ Master data governance
❌ Metric business rationality (garbage in, garbage out still applies)
❌ NLP perfection (we use simple keyword matching)

---

## 🏗️ Architecture Overview / 架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER / AGENT                                 │
│  "昨天产线A的一次合格率是多少？"                                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              SEMANTIC ORCHESTRATOR                               │
│  - Coordinates all resolution steps                              │
│  - Enforces decision structure                                   │
│  - Records complete audit trail                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│            SEMANTIC CONTROL PLANE (6 Core Tables)                │
│                                                                  │
│  1. semantic_object      → What business concepts exist         │
│  2. semantic_version     → Which version applies when           │
│  3. logical_definition   → How to calculate (business logic)    │
│  4. physical_mapping     → Where data lives (SQL templates)     │
│  5. access_policy        → Who can do what                      │
│  6. execution_audit      → Why this decision was made           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│           PHYSICAL EXECUTION ENGINE                               │
│  - Render SQL templates with parameters                          │
│  - Execute against data sources                                  │
│  - Return structured results                                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              EXECUTION AUDIT & REPLAY                            │
│  - Every decision recorded                                       │
│  - Complete reproducibility                                      │
│  - Governance & accountability                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📦 Core Design Principles / 核心设计原则

### 1. **Semantic Layer Decoupled from Physical Data / 语义层与物理层解耦**

Business logic (`logical_definition`) contains **NO table names or SQL**. Physical implementation (`physical_mapping`) can change without affecting business definitions.

**Example:**
- **Logical:** `good_qty / total_qty` (pure business formula)
- **Physical:** `SELECT SUM(good_qty)/SUM(total_qty) FROM fact_production_records WHERE ...`

### 2. **Metadata-Driven Decisions / 元数据驱动决策**

All executable decisions come from database tables, **NOT hardcoded logic**:
- Version selection based on `semantic_version.effective_from` and `scenario_condition`
- Access control based on `access_policy` rules
- SQL generation from `physical_mapping.sql_template`

### 3. **Orchestrator is Stateless / 编排器无状态**

The `SemanticOrchestrator` only orchestrates flow. All business rules are in metadata. This means:
- No business logic in Python code
- Easy to extend by adding database records
- Testable and deterministic

### 4. **No Guessing on Ambiguity / 歧义不猜测**

When multiple semantic objects match a query, the system **does NOT guess**. It returns a structured ambiguity error requiring clarification.

### 5. **Complete Audit Trail / 完整审计链路**

Every execution records complete decision trace, enabling **replayability** for debugging and compliance.

---

## 🗄️ Database Schema / 数据库模式

### The 6 Core Tables

#### 1. `semantic_object` - Business Concepts
Defines **WHAT** business concepts exist.

#### 2. `semantic_version` - Version Management
Handles **WHICH** version applies based on time/scenario.

#### 3. `logical_definition` - Business Logic
Pure business formulas **NO physical details**.

#### 4. `physical_mapping` - Physical Implementation
Maps logic to actual SQL templates.

#### 5. `access_policy` - Authorization Control
Defines **WHO** can do **WHAT**.

#### 6. `execution_audit` - Complete Decision Trail
Records **WHY** and **HOW** every decision was made.

---

## 🚀 Quick Start / 快速开始

### Prerequisites / 先决条件

- Python 3.10+
- SQLite 3
- OS: Linux/macOS/Windows (WSL supported)

### Installation / 安装

```bash
# Option A: pip + venv
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run the demo
python demo_queries.py
```

```bash
# Option B: uv (recommended for speed)
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

# Run the demo
python demo_queries.py
```

```bash
# Option C: Docker (optional, for reproducible env)
docker build -t semantic-layer .
docker run --rm -it semantic-layer bash
# then inside container:
# python demo_queries.py
```

---

## ✅ Validation & Acceptance / 验证与验收

- `VALIDATION_PLAN.md` - 变更场景测试集  
- `REPORT_REVIEW_CHECKLIST.md` - 报告可读性评审清单  
- `PILOT_ACCEPTANCE_REPORT_TEMPLATE.md` - 试点验收报告模板  
- `docs/validation/sample_filled.md` - 试点验收样例（自动生成）

---

## 🗂️ Repository Layout / 项目结构

- `src/semantic_layer/` - 核心语义控制面模块  
- `src/governance/` - 审批与治理产物工具  
- `tests/` - 单元/集成/E2E/快照/规模/一致性测试  
- `docs/validation/` - 验证与验收产物  
- `schema.sql` / `seed_data.sql` - 数据库结构与种子数据

---

## 📖 Usage Examples / 使用示例

### Basic Query

```python
from semantic_layer.orchestrator import SemanticOrchestrator
from semantic_layer.models import ExecutionContext
from datetime import datetime

# Initialize
orchestrator = SemanticOrchestrator('data/semantic_layer.db')

# Set up execution context
context = ExecutionContext(
    user_id=1,
    role='operator',
    timestamp=datetime.now()
)

# Execute query
result = orchestrator.query(
    question="昨天产线A的一次合格率是多少？",
    parameters={
        'line': 'A',
        'start_date': '2026-01-27',
        'end_date': '2026-01-27'
    },
    context=context
)

print(f"Result: {result['data']}")
print(f"Audit ID: {result['audit_id']}")
```

---

## 🎯 Key Innovations / 关键创新点

### 1. **Semantic Versioning**

Supports temporal and scenario-based versioning of metric definitions.

### 2. **Logical vs Physical Separation**

Business logic is database-agnostic; physical schema changes only require updating `physical_mapping`.

### 3. **No Guessing on Ambiguity**

Returns structured ambiguity errors requiring explicit clarification.

### 4. **Complete Audit Trail**

Every execution is fully reproducible with complete decision trace.

### 5. **Agent-Ready Architecture**

All governance is in system structure, not conversation.

### 6. **Ontology Modeling**

Entity/Dimension/Attribute/Relationship tables provide an ontology backbone for semantic governance.  
See `MODELING_GUIDE.md` for naming, hierarchy, and change rules.

### 7. **Impact Analysis (DAG)**

Metric dependencies and entity mappings enable impact analysis (change risk and blast radius).  
Use `impact()` and `diff_versions()` for DAG-based governance.

---

## 🛡️ Why This POC Survives Enterprise Challenges / 企业挑战应对

This POC has been hardened against common enterprise architecture concerns through explicit design choices and testable guarantees.

### 1. Why Won't the System Pick the Wrong Metric Version?

**Problem**: Multiple versions exist for the same metric. How do we ensure the correct one is selected?

**Solution**: Deterministic conflict resolution with explicit rules

```python
# Version selection rules (enforced in code):
# 1. Score higher → better match (scenario+time > time-only > no-match)
# 2. If scores equal → priority higher wins
# 3. If still tied → AmbiguityError (system refuses to guess)
```

**Testable Evidence**:
- [tests/test_enterprise_challenges.py::TestPriorityConflictResolution](tests/test_enterprise_challenges.py) - Proves higher priority wins
- [tests/test_enterprise_challenges.py::TestAmbiguityDetection](tests/test_enterprise_challenges.py) - Proves system refuses to guess on true ambiguity

**Validated by tests**: The system will not silently pick a random version. It either selects deterministically or fails loudly.

---

### 2. Why Don't Process Changes Break the Agent?

**Problem**: Manufacturing processes change frequently. Does the agent need code updates?

**Solution**: Scenario-driven version selection isolates agent from business logic

```sql
-- Agent never knows about these versions:
INSERT INTO semantic_version (version_name, scenario_condition, priority)
VALUES
  ('FPY_v1_standard', NULL, 0),                    -- Default
  ('FPY_v2_rework', '{"rework_enabled": true}', 10); -- Rework scenario

-- Agent just calls:
orchestrator.query("FPY for line A", scenario={"rework_enabled": true})
```

**Testable Evidence**:
- [tests/test_e2e.py::test_e2e_scenario_driven_version_selection](tests/test_e2e.py) - Proves scenario triggers correct version
- Scenario changes are pure metadata operations (no code deployment)

**Validated by tests**: Process engineers can add/modify versions without touching agent code.

---

### 3. Why Can We Replace the Data Warehouse?

**Problem**: Legacy data warehouse schemas are fragile. Can we migrate without breaking business logic?

**Solution**: Logical-physical separation allows zero-downtime migration

```sql
-- Old physical mapping (priority=1):
INSERT INTO physical_mapping (logical_definition_id, engine_type, connection_ref, priority)
VALUES (1, 'sqlite', 'legacy_db', 1);

-- New physical mapping (priority=10, automatically selected):
INSERT INTO physical_mapping (logical_definition_id, engine_type, connection_ref, priority)
VALUES (1, 'snowflake', 'new_wh', 10);
```

**Testable Evidence**:
- [tests/test_enterprise_challenges.py::TestPhysicalMappingPortability](tests/test_enterprise_challenges.py) - Proves higher priority mapping is selected
- Same business logic, different physical implementation

**Validated by tests**: Data warehouse schema changes can be isolated to `physical_mapping`.

---

### 4. Why Does the System Dare to Calculate?

**Problem**: Audit teams ask "How do we know this number is correct?"

**Solution**: Complete reproducibility with decision trace

```python
# Every query returns:
{
    'data': [{'fpy': 0.95}],
    'decision_trace': [
        {'step': 'resolve_semantic_object_complete', 'data': {'semantic_object_reason': '...'}},
        {'step': 'resolve_version_complete', 'data': {'version_selection_reason': '...'}},
        {'step': 'resolve_logic_complete', 'data': {'logic_expression': 'good_qty / total_qty'}},
        {'step': 'resolve_physical_mapping_complete', 'data': {'physical_mapping_reason': '...'}},
        {'step': 'render_sql_complete', 'data': {'sql_preview': 'SELECT ...'}},
        {'step': 'execution_complete', 'data': {'row_count': 1}}
    ],
    'audit_id': '20260128_163122_428e7cce'
}
```

**Testable Evidence**:
- All decision traces include explicit `reason` fields
- Replay uses `original.final_sql` without re-resolution (proves reproducibility)
- 134 tests passed, 1 skipped (see `pytest` output)

**Validated by tests**: Every calculation is explainable, reproducible, and auditable.

---

### 5. What Complexity is INTENTIONALLY Not Supported?

This POC makes explicit engineering trade-offs. We DO NOT support:

| Feature | Why Not Supported | Reasonable Because |
|---------|------------------|-------------------|
| **Partial scenario matching** | `{"a":1}` does NOT match `{"a":1, "b":2}` | Prevents accidental mis-selection |
| **Fuzzy NLP** | Simple keyword matching only | Enterprise wants explicit governance, not AI guessing |
| **Multi-condition expressions** | No DSL like `{"$or": [...]}` | Keeps metadata simple and queryable |
| **Auto-version conflict resolution** | System fails on ambiguity | "Fail loud" is safer than "silent wrong" |
| **Parameter inference** | All parameters must be explicit | Prevents "it worked by accident" bugs |

**Philosophy**: "Make the correct behavior obvious, make incorrect behavior impossible."

---

### Enterprise Readiness Checklist

- ✅ **No silent failures** - Ambiguity → Error
- ✅ **No guessing** - Partial match = mismatch
- ✅ **No hardcode** - All decisions from metadata
- ✅ **Full audit** - Every step traceable
- ✅ **Replay-safe** - Same SQL, explainable differences
- ✅ **Migration-proof** - Physical changes isolated
- ✅ **Test-covered** - 134 tests passed, 1 skipped
- ✅ **Conflict-proof** - Priority-based deterministic resolution

**Bottom Line**: This architecture survives enterprise scrutiny because every decision is explicit, testable, and auditable.

---

## 📊 Project Status / 项目状态

This is a **Reference Architecture POC**, not a production-ready system.

### ✅ What Works / 已实现能力

- End-to-end semantic query execution
- Policy enforcement
- Audit and replay
- Preview mode
- Ambiguity detection
- Version selection
- SQL template rendering

### ⚠️ Limitations / 已知限制

- Simple keyword-based NLP
- SQLite-only
- Basic policy conditions
- No caching layer
- No multi-source queries

---

## 📄 License / 许可证

This is a reference architecture POC provided for educational purposes.  
该项目为参考架构 POC，仅用于教育和演示目的。

---

## 🤝 Contributing / 贡献指南

PRs and issues are welcome. Please keep changes minimal, well-tested, and aligned with the POC scope.  
欢迎提交 PR 或 Issue。请保持改动最小、可测试，并符合 POC 范围。

---

**Remember: This POC validates that semantics can be a structural, runtime capability.**
