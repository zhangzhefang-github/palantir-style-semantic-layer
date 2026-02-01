# 试点验收报告（样例）

## 结果摘要
- 用例总数：3
- 通过数：3
- 失败数：0
- 风险分布：{'L3': 1, 'L1': 2}

## 证据链接示例
- Audit query: `SELECT audit_id, question, version_name, status, executed_at FROM execution_audit WHERE semantic_object_name = :metric_name ORDER BY executed_at DESC LIMIT 10;`
