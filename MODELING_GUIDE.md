# Semantic Modeling Guide / 语义建模规范

> Purpose: make ontology modeling consistent, testable, and enterprise-friendly.  
> 目标：确保本体建模一致、可验证、可规模化。

---

## 1) Scope / 范围
- **Entity**: core business objects (e.g., ProductionLine, Order).  
- **Dimension**: slicing axes attached to entities (e.g., line, date).  
- **Attribute**: measurable or descriptive fields (e.g., good_qty).  
- **Metric**: business KPI defined in `semantic_object`.

---

## 2) Naming Conventions / 命名规范
- **Entity**: `PascalCase`, singular noun (e.g., `ProductionLine`).  
- **Dimension/Attribute**: `snake_case` (e.g., `record_date`, `good_qty`).  
- **Metric**: `PascalCase` or common acronym (e.g., `FPY`, `QualityScore`).  
- **Version**: `<Metric>_v<major>_<scenario>` (e.g., `FPY_v2_rework`).

---

## 3) Hierarchy & Ownership / 层级与归属
- `Entity → Dimension/Attribute` must be explicit.  
- Each Metric **must** map to one or more Entities.  
- Metric grain must match entity-level aggregation.

---

## 4) Relationship Rules / 关系规则
- Use `ontology_relationship` for entity relations.  
  - `has_many`, `belongs_to`, `1:N`, `N:1`, `1:1`.
- Relationship changes require version review.

---

## 5) Metric Definition Rules / 指标定义规则
- **Logical Definition**: no physical fields or table names.  
- **Physical Mapping**: SQL template only, parameterized (`:param`).  
- **Scenario**: must be explicit and complete (no partial match).  

---

## 6) Versioning & Governance / 版本与治理
- Version must be deterministic:  
  - Scenario+Time > Default  
  - Priority resolves tie  
  - Ambiguity → fail loud
- All changes require audit record and test case.

---

## 7) Example / 示例

**Entity**
```
ProductionLine
```

**Dimensions**
```
line, record_date
```

**Metric**
```
QualityScore = 0.7*FPY + 0.3*(1-DefectRate)
```

---

## 8) Change Process / 变更流程
1. Propose new entity/dimension/metric  
2. Add ontology rows and semantic_object  
3. Add logical_definition + physical_mapping  
4. Add test + expected decision trace  
5. Run full `pytest`
