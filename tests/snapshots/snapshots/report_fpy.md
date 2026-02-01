# Impact Report
- Metric: FPY
- Version A: FPY_v1_standard
- Version B: FPY_v2_rework
- Risk: L3

## Impact Scope
- Metrics: [1, 4]
- Mappings: []
- Entities: []
- Dimensions: []
- Attributes: []

## Recommended Actions
- Business owner approval required
- Prepare rollback plan
- Run shadow queries for validation

## Evidence
- Audit query: `SELECT audit_id, question, version_name, status, executed_at FROM execution_audit WHERE semantic_object_name = :metric_name ORDER BY executed_at DESC LIMIT 10;`