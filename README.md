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
- [Core Modules](#-core-modules)
- [Design Principles](#-design-principles)
- [Enterprise Readiness](#-enterprise-readiness)
- [Project Status](#-project-status)
- [Documentation](#-documentation)
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
Metric dependencies and entity mappings enable impact analysis with:
- `build_dependency_graph()` - Build DAG dependency graph
- `impact()` - Analyze change blast radius
- `diff()` - Compare two version differences
- `generate_report()` - Generate impact analysis report with risk assessment

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
│         SEMANTIC CONTROL PLANE (13 Business Tables)             │
│                                                                 │
│  ┌─ Core Execution Tables (6) ─────────────────────────────┐    │
│  │ semantic_object    │ semantic_version │ logical_definition│   │
│  │ physical_mapping   │ access_policy    │ execution_audit   │   │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─ Ontology & Governance Tables (7) ──────────────────────┐    │
│  │ ontology_entity    │ ontology_dimension│ ontology_attribute│  │
│  │ ontology_relationship │ metric_entity_map │ metric_dependency│ │
│  │ term_dictionary    │                   │                    │  │
│  └─────────────────────────────────────────────────────────┘    │
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

### Real-World Scenario: Cross-Department Metric Conflict

**Problem**: CFO asks "What's the Gross Margin for East Region last month?"
- Finance team calculates: `(Revenue - Total Cost) / Revenue = 23.5%`
- Sales team calculates: `(Revenue - Direct Cost) / Revenue = 28.2%`
- Boss: "Which one is correct? Why are there two numbers?"

**Solution**: The semantic control plane automatically identifies which version to use based on scenario context.

### Basic Query

```python
from semantic_layer.orchestrator import SemanticOrchestrator
from semantic_layer.models import ExecutionContext
from datetime import datetime

# Initialize
orchestrator = SemanticOrchestrator('data/semantic_layer.db')

# Set up execution context (Finance department)
context = ExecutionContext(
    user_id=1,
    role='finance_manager',
    timestamp=datetime.now()
)

# Execute query with department context
result = orchestrator.query(
    question="What is the Gross Margin for East Region last month?",
    parameters={
        'region': 'East',
        'period': '2026-01',
        'scenario': {'department': 'finance'}  # Specifies which version to use
    },
    context=context
)

print(f"Result: {result['data']}")  # {'gross_margin': 0.235}
print(f"Version: {result['version']}")  # GrossMargin_v1_finance
print(f"Audit ID: {result['audit_id']}")
```

### Query Response Structure

```json
{
    "data": [{"gross_margin": 0.235}],
    "decision_trace": [
        {"step": "resolve_semantic_object_complete", "data": {"semantic_object_reason": "Matched GrossMargin"}},
        {"step": "resolve_version_complete", "data": {"version_selection_reason": "Selected finance version"}},
        {"step": "resolve_logic_complete", "data": {"logic_expression": "(revenue - total_cost) / revenue"}},
        {"step": "resolve_physical_mapping_complete", "data": {"physical_mapping_reason": "..."}},
        {"step": "render_sql_complete", "data": {"sql_preview": "SELECT ..."}},
        {"step": "execution_complete", "data": {"row_count": 1}}
    ],
    "audit_id": "20260128_163122_428e7cce"
}
```

**Key Point**: The system records exactly which version was used, why it was selected, and the complete calculation logic - enabling full auditability.

---

## 🗄️ Database Schema

### Overview: 13 Business Tables + 1 Mock Data Table

The semantic control plane uses a **two-layer table architecture**:

| Layer | Count | Purpose |
|-------|-------|---------|
| Core Execution | 6 tables | Query execution pipeline |
| Ontology & Governance | 7 tables | Semantic modeling & impact analysis |
| Mock Data | 1 table | Demo physical data |

### Layer 1: Core Execution Tables (6)

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `semantic_object` | **WHAT** business concepts exist | `name`, `aliases`, `description` |
| `semantic_version` | **WHICH** version applies | `effective_from`, `scenario_condition`, `priority` |
| `logical_definition` | **HOW** to calculate | `expression`, `unit`, `aggregation_type` |
| `physical_mapping` | **WHERE** data lives | `sql_template`, `engine_type`, `connection_ref` |
| `access_policy` | **WHO** can do what | `role`, `action`, `conditions` |
| `execution_audit` | **WHY** decisions were made | `decision_trace`, `final_sql`, `parameters` |

### Layer 2: Ontology & Governance Tables (7)

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `ontology_entity` | Core business entities | `name`, `domain`, `description` |
| `ontology_dimension` | Entity dimensions (slicing axes) | `entity_id`, `name`, `data_type` |
| `ontology_attribute` | Entity attributes | `entity_id`, `name`, `is_key` |
| `ontology_relationship` | Entity relationships | `from_entity_id`, `to_entity_id`, `cardinality` |
| `metric_entity_map` | Metric-entity mapping | `metric_id`, `entity_id`, `grain_level` |
| `metric_dependency` | Metric DAG edges | `upstream_metric_id`, `downstream_metric_id` |
| `term_dictionary` | Term normalization | `term`, `normalized_term`, `language` |

### Mock Data Table (1)

| Table | Purpose |
|-------|---------|
| `fact_production_records` | Demo production data for testing |

---

## 🧩 Core Modules

### Semantic Layer (`src/semantic_layer/`)

| Module | Purpose |
|--------|---------|
| `orchestrator.py` | Core orchestrator - coordinates all resolution steps |
| `semantic_resolver.py` | Semantic object & version resolution |
| `policy_engine.py` | RBAC + ABAC policy enforcement |
| `execution_engine.py` | SQL rendering & execution |
| `models.py` | Data models (6 core classes + exceptions) |
| `impact_analysis.py` | **DAG-based impact analysis & version diff** |
| `scenario_matcher.py` | Scenario condition matching |
| `grain_validator.py` | Metric grain validation |
| `dependency_builder.py` | Dependency graph construction |
| `interfaces.py` | Abstract interfaces |
| `sqlite_stores.py` | SQLite metadata store implementation |
| `config.py` | Configuration management |

### Governance (`src/governance/`)

| Module | Purpose |
|--------|---------|
| `approval_package.py` | Approval package generation for change governance |

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
- Policy enforcement (RBAC + ABAC)
- Audit and replay
- Preview mode
- Ambiguity detection
- Version selection (scenario + priority)
- SQL template rendering
- **Ontology modeling (Entity/Dimension/Attribute/Relationship)**
- **Impact analysis (DAG-based)**
- **Term dictionary normalization**

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
│   ├── semantic_layer/           # Core semantic control plane
│   │   ├── orchestrator.py       # Core orchestrator
│   │   ├── semantic_resolver.py  # Semantic resolution
│   │   ├── policy_engine.py      # Policy enforcement
│   │   ├── execution_engine.py   # SQL execution
│   │   ├── models.py             # Data models
│   │   ├── impact_analysis.py    # Impact analysis (DAG)
│   │   ├── scenario_matcher.py   # Scenario matching
│   │   ├── grain_validator.py    # Grain validation
│   │   ├── dependency_builder.py # Dependency builder
│   │   ├── interfaces.py         # Interfaces
│   │   ├── sqlite_stores.py      # SQLite stores
│   │   └── config.py             # Configuration
│   └── governance/
│       └── approval_package.py   # Approval package generator
├── tests/
│   ├── e2e/                      # End-to-end tests
│   ├── approval/                 # Approval tests
│   ├── consistency/              # Consistency tests
│   ├── performance/              # Performance tests
│   ├── snapshots/                # Snapshot tests
│   ├── test_enterprise_challenges.py
│   ├── test_impact_analysis.py
│   └── ...
├── docs/
│   └── validation/               # Validation artifacts
├── data/                         # SQLite database
├── schema.sql                    # Database schema (13 tables)
├── seed_data.sql                 # Seed data
├── demo_queries.py               # Interactive demo
├── demo_detailed_logs.py         # Detailed logs demo
└── manual_test.py                # Manual verification
```

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [`QUICKSTART.md`](QUICKSTART.md) | 5-minute quick start guide |
| [`MODELING_GUIDE.md`](MODELING_GUIDE.md) | Semantic modeling conventions |
| [`TESTING_GUIDE.md`](TESTING_GUIDE.md) | Test verification guide |
| [`DETAILED_LOGS_GUIDE.md`](DETAILED_LOGS_GUIDE.md) | Detailed logs demo guide |
| [`PROJECT_SUMMARY.md`](PROJECT_SUMMARY.md) | Project completion report |
| [`VALIDATION_PLAN.md`](VALIDATION_PLAN.md) | Change scenario test set |
| [`REPORT_REVIEW_CHECKLIST.md`](REPORT_REVIEW_CHECKLIST.md) | Report review checklist |
| [`PILOT_ACCEPTANCE_REPORT_TEMPLATE.md`](PILOT_ACCEPTANCE_REPORT_TEMPLATE.md) | Pilot acceptance template |
| [`tests/README.md`](tests/README.md) | Test suite documentation |
| [`tests/TEST_REPORT.md`](tests/TEST_REPORT.md) | Test report |

---

## 🤝 Contributing

Contributions are welcome! Please ensure your changes are:

1. **Minimal** - Keep changes focused
2. **Well-tested** - Add tests for new functionality
3. **Aligned** - Stay within POC scope

### Development

```bash
# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/test_enterprise_challenges.py -v  # Enterprise challenges
pytest tests/test_impact_analysis.py -v        # Impact analysis
pytest tests/test_e2e.py -v                    # End-to-end

# Run manual verification
python manual_test.py

# Run detailed logs demo
python demo_detailed_logs.py
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
