# Palantir-Style Semantic Control Plane

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=flat-square&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-134%20passed-success?style=flat-square)](tests/)

**A Reference Architecture POC for Semantic Layer as a Runtime Control Plane**

[English](README.md) | [中文](README_CN.md)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [Usage](#-usage)
- [Database Schema](#-database-schema)
- [Design Principles](#-design-principles)
- [Enterprise Readiness](#-enterprise-readiness)
- [Project Status](#-project-status)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Overview

This POC validates a fundamental proposition:

> **Can enterprise semantics become a structural, runtime capability rather than relying on human collaboration for every decision?**

### What This POC Validates

| Capability | Description |
|------------|-------------|
| ✅ Semantic layer as runtime control plane | System makes executable decisions |
| ✅ Agents can "stop asking humans" | All governance is structural, not conversational |
| ✅ Data warehouse changes are isolated | Only update `physical_mapping`, not business logic |
| ✅ Full audit trail | Every decision is traceable and replayable |

### What This POC Does NOT Address

| Out of Scope | Reason |
|--------------|--------|
| ❌ Data quality issues | Focus is on semantic governance, not data cleansing |
| ❌ Master data governance | Separate concern from semantic layer |
| ❌ Metric business rationality | Garbage in, garbage out still applies |
| ❌ NLP perfection | Uses simple keyword matching by design |

---

## ✨ Key Features

### 1. Semantic Versioning
Supports temporal and scenario-based versioning of metric definitions.

### 2. Logical vs Physical Separation
Business logic is database-agnostic; physical schema changes only require updating `physical_mapping`.

### 3. No Guessing on Ambiguity
Returns structured ambiguity errors requiring explicit clarification.

### 4. Complete Audit Trail
Every execution is fully reproducible with complete decision trace.

### 5. Agent-Ready Architecture
All governance is in system structure, not conversation.

### 6. Ontology Modeling
Entity/Dimension/Attribute/Relationship tables provide an ontology backbone.
See [`MODELING_GUIDE.md`](MODELING_GUIDE.md) for naming, hierarchy, and change rules.

### 7. Impact Analysis (DAG)
Metric dependencies and entity mappings enable impact analysis.
Use `impact()` and `diff_versions()` for DAG-based governance.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER / AGENT                                │
│  "What is the First Pass Yield for Line A yesterday?"           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              SEMANTIC ORCHESTRATOR                              │
│  • Coordinates all resolution steps                             │
│  • Enforces decision structure                                  │
│  • Records complete audit trail                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│            SEMANTIC CONTROL PLANE (6 Core Tables)               │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ semantic_object │  │ semantic_version│  │logical_definition│ │
│  │   WHAT exists   │  │  WHICH applies  │  │   HOW to calc   │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ physical_mapping│  │  access_policy  │  │ execution_audit │  │
│  │   WHERE data    │  │   WHO can do    │  │   WHY decided   │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│           PHYSICAL EXECUTION ENGINE                             │
│  • Render SQL templates with parameters                         │
│  • Execute against data sources                                 │
│  • Return structured results                                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- SQLite 3
- OS: Linux / macOS / Windows (WSL supported)

### Installation

<details>
<summary><b>Option A: pip + venv</b></summary>

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run the demo
python demo_queries.py
```

</details>

<details>
<summary><b>Option B: uv (recommended for speed)</b></summary>

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

# Run the demo
python demo_queries.py
```

</details>

<details>
<summary><b>Option C: Docker</b></summary>

```bash
docker build -t semantic-layer .
docker run --rm -it semantic-layer bash
# Inside container:
python demo_queries.py
```

</details>

---

## 📖 Usage

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
    question="What is the First Pass Yield for Line A yesterday?",
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

### Query Response Structure

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

## 🗄️ Database Schema

### The 6 Core Tables

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `semantic_object` | **WHAT** business concepts exist | `name`, `aliases`, `description` |
| `semantic_version` | **WHICH** version applies | `effective_from`, `scenario_condition`, `priority` |
| `logical_definition` | **HOW** to calculate | `expression`, `unit`, `aggregation_type` |
| `physical_mapping` | **WHERE** data lives | `sql_template`, `engine_type`, `connection_ref` |
| `access_policy` | **WHO** can do what | `role`, `action`, `conditions` |
| `execution_audit` | **WHY** decisions were made | `decision_trace`, `final_sql`, `parameters` |

---

## 📦 Design Principles

### 1. Semantic Layer Decoupled from Physical Data

Business logic (`logical_definition`) contains **NO table names or SQL**.

| Layer | Example |
|-------|---------|
| **Logical** | `good_qty / total_qty` (pure business formula) |
| **Physical** | `SELECT SUM(good_qty)/SUM(total_qty) FROM fact_production_records WHERE ...` |

### 2. Metadata-Driven Decisions

All executable decisions come from database tables, **NOT hardcoded logic**:
- Version selection based on `semantic_version.effective_from` and `scenario_condition`
- Access control based on `access_policy` rules
- SQL generation from `physical_mapping.sql_template`

### 3. Orchestrator is Stateless

The `SemanticOrchestrator` only orchestrates flow. All business rules are in metadata.
- No business logic in Python code
- Easy to extend by adding database records
- Testable and deterministic

### 4. No Guessing on Ambiguity

When multiple semantic objects match a query, the system **does NOT guess**.
It returns a structured ambiguity error requiring clarification.

### 5. Complete Audit Trail

Every execution records complete decision trace, enabling **replayability** for debugging and compliance.

---

## 🛡️ Enterprise Readiness

This POC has been hardened against common enterprise architecture concerns.

### Version Conflict Resolution

```python
# Version selection rules (enforced in code):
# 1. Score higher → better match (scenario+time > time-only > no-match)
# 2. If scores equal → priority higher wins
# 3. If still tied → AmbiguityError (system refuses to guess)
```

### Process Change Isolation

```sql
-- Scenario-driven version selection:
INSERT INTO semantic_version (version_name, scenario_condition, priority)
VALUES
  ('FPY_v1_standard', NULL, 0),                    -- Default
  ('FPY_v2_rework', '{"rework_enabled": true}', 10); -- Rework scenario
```

### Data Warehouse Migration

```sql
-- Priority-based physical mapping selection:
INSERT INTO physical_mapping (logical_definition_id, engine_type, connection_ref, priority)
VALUES 
  (1, 'sqlite', 'legacy_db', 1),      -- Old (low priority)
  (1, 'snowflake', 'new_wh', 10);     -- New (high priority, auto-selected)
```

### Readiness Checklist

| Requirement | Status |
|-------------|--------|
| No silent failures | ✅ Ambiguity → Error |
| No guessing | ✅ Partial match = mismatch |
| No hardcode | ✅ All decisions from metadata |
| Full audit | ✅ Every step traceable |
| Replay-safe | ✅ Same SQL, explainable differences |
| Migration-proof | ✅ Physical changes isolated |
| Test-covered | ✅ 134 tests passed, 1 skipped |
| Conflict-proof | ✅ Priority-based deterministic resolution |

---

## 📊 Project Status

> **Note**: This is a **Reference Architecture POC**, not a production-ready system.

### ✅ Implemented

- End-to-end semantic query execution
- Policy enforcement
- Audit and replay
- Preview mode
- Ambiguity detection
- Version selection
- SQL template rendering

### ⚠️ Limitations

- Simple keyword-based NLP
- SQLite-only
- Basic policy conditions
- No caching layer
- No multi-source queries

---

## 🗂️ Repository Structure

```
palantir-style-semantic-layer/
├── src/
│   ├── semantic_layer/       # Core semantic control plane modules
│   └── governance/           # Approval and governance artifact tools
├── tests/                    # Unit/Integration/E2E/Snapshot tests
├── docs/
│   └── validation/           # Validation and acceptance artifacts
├── data/                     # SQLite database
├── schema.sql                # Database schema
├── seed_data.sql             # Seed data
├── VALIDATION_PLAN.md        # Change scenario test set
├── REPORT_REVIEW_CHECKLIST.md
└── MODELING_GUIDE.md         # Ontology modeling guide
```

---

## 🤝 Contributing

Contributions are welcome! Please ensure your changes are:

1. **Minimal** - Keep changes focused
2. **Well-tested** - Add tests for new functionality
3. **Aligned** - Stay within POC scope

### Development

```bash
# Run tests
pytest tests/ -v

# Run specific test file
pytest tests/test_enterprise_challenges.py -v
```

---

## 📄 License

This project is provided as a reference architecture POC for educational purposes.

MIT License - See [LICENSE](LICENSE) for details.

---

<div align="center">

**Remember: This POC validates that semantics can be a structural, runtime capability.**

Made with ❤️ for enterprise semantic governance

</div>
