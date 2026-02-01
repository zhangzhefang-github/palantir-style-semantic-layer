# 详细日志演示指南 (Detailed Logs Demo Guide)

## 概述

`demo_detailed_logs.py` 是一个完整的调用链日志演示脚本，展示了 Palantir-Style Semantic Control Plane 的完整执行流程。

**核心目标**：无需看代码，只看日志就能理解系统运行

## 运行方式

```bash
python3 demo_detailed_logs.py
```

## 日志输出说明

### 1. 数据库初始状态

在执行查询前，脚本会显示所有相关数据表的内容：

- **semantic_object 表**：可用的语义对象（FPY, OutputQty, DefectRate）
- **semantic_version 表**：每个语义对象的版本列表
- **logical_definition 表**：业务公式（如：good_qty / total_qty）
- **physical_mapping 表**：SQL 实现（模板）
- **access_policy 表**：权限规则
- **fact_production_records 表**：实际生产数据

### 2. INFO 级别日志

完整的函数调用链，每一步都有明确标注：

```
[INFO] semantic_resolver:54] === STEP 1: RESOLVE SEMANTIC OBJECT ===
[INFO] semantic_resolver:55] Question: 昨天产线A的一次合格率是多少？
[INFO] semantic_resolver:59] Extracted keywords: ['一次合格率', 'FPY', '合格率']
[INFO] semantic_resolver:63] Found 1 candidate(s)
[INFO] semantic_resolver:78] ✓ Matched semantic object: FPY (ID: 1)
```

每个阶段包含：
- **输入**：参数、查询条件
- **过程**：数据库查询、算法评估
- **输出**：选择结果、原因

### 3. 决策链摘要 (Decision Trace Summary)

14 个决策步骤的完整记录，每个步骤包含关键信息：

```
4. resolve_version_complete
   ----------------------------------------------------------------------
   → Version ID: 2
   → Version Name: FPY_v2_rework
   → Scenario Condition: {'rework_enabled': True}
   → Priority: N/A
   → Reason: Selected version "FPY_v2_rework" - scenario_match=True
```

### 4. 总结

7 个阶段的清晰说明：

1️⃣ **语义解析阶段**：关键词匹配 → 语义对象
2️⃣ **版本选择阶段**：Scenario 评估 → 版本选择
3️⃣ **物理映射阶段**：SQL 模板选择
4️⃣ **SQL 渲染阶段**：Jinja2 参数替换
5️⃣ **策略检查阶段**：权限验证
6️⃣ **执行阶段**：SQL 执行 → 结果返回
7️⃣ **审计阶段**：完整决策链存储

## 日志中的关键信息

### Scenario 驱动的版本选择

日志清晰显示为什么选择了 FPY_v2_rework：

```
[INFO] scenario_matcher:216] ✓ FPY_v2_rework: score=2 reason=scenario_match: {'rework_enabled': True}
[INFO] scenario_matcher:216] ✗ FPY_v1_standard: score=1 reason=default_version_no_scenario
```

### SQL 生成过程

```
[INFO] execution_engine:148] Parameters: {'line': 'A', 'start_date': '2026-01-27', 'end_date': '2026-01-27', 'scenario': {'rework_enabled': True}}
[INFO] execution_engine:171] SELECT SUM(CAST(good_qty + rework_qty AS REAL)) / SUM(CAST(total_qty AS REAL)) AS fpy FROM fact_production_records WHERE line = 'A' AND record_date BETWEEN '2026-01-27' AND '2026-01-27'
```

### 权限检查

```
[INFO] policy_engine:79] Decision: ALLOW
[INFO] policy_engine:80] Reason: Allowed by 1 policy(ies)
```

## 完整示例输出

```
================================================================================
🔍 Palantir-Style Semantic Control Plane - 完整调用链日志演示
================================================================================

📝 场景：查询昨天产线A的一次合格率（FPY）
   - 有 scenario 参数：触发 FPY_v2_rework 版本
   - 包含返工数量的计算

🗄️  数据库初始状态（执行查询前）
--------------------------------------------------------------------------------
1. semantic_object 表（可用的语义对象）
2. semantic_version 表（FPY 的版本列表）
3. logical_definition 表（业务公式）
4. physical_mapping 表（SQL 实现）
5. access_policy 表（权限规则）
6. fact_production_records 表（实际数据）

[步骤 0] 初始化 SemanticOrchestrator
[步骤 7] 执行语义查询（完整流程）

📊 查询结果
✅ 状态: SUCCESS
✅ Semantic Object: FPY
✅ Version: FPY_v2_rework
✅ Logic: (good_qty + rework_qty) / total_qty
✅ Data: [{'fpy': 0.9866666666666667}]

🔗 决策链摘要（共 14 步）
1. resolve_semantic_object_start
2. resolve_semantic_object_complete
3. resolve_version_start
4. resolve_version_complete
...
```

## 与手动测试的区别

| 脚本 | 用途 | 输出重点 |
|------|------|----------|
| `manual_test.py` | 功能验证 | 测试通过/失败 |
| `demo_detailed_logs.py` | 学习理解 | 完整调用链 + 数据状态 |

## 适用场景

- **新人上手**：理解系统运行机制
- **架构评审**：展示技术决策过程
- **问题排查**：追溯查询执行的每一步
- **审计追溯**：完整的数据访问记录

## 下一步

- 查看 [TESTING_GUIDE.md](TESTING_GUIDE.md) 了解完整测试体系
- 查看 [README.md](README.md) 了解架构设计
- 运行 `manual_test.py` 验证所有功能
