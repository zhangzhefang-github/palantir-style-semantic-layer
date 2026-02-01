# 🚀 快速启动指南

5 分钟上手 Palantir-Style Semantic Control Layer

---

## ⚡ 快速开始

### 1. 安装依赖
```bash
# 使用 uv (推荐)
source .venv/bin/activate
uv pip install -r requirements.txt

# 或使用 pip
pip install -r requirements.txt
```

### 2. 初始化数据库
```bash
# 自动初始化（首次运行时自动执行）
python test_basic.py
```

### 3. 运行测试
```bash
# 快速测试
python test_basic.py

# 完整测试套件
pytest tests/ -v
```

---

## 📺 演示场景

### 场景 1: 基本查询

```python
from semantic_layer.orchestrator import SemanticOrchestrator
from semantic_layer.models import ExecutionContext
from datetime import datetime

# 初始化
orchestrator = SemanticOrchestrator('data/semantic_layer.db')

# 设置上下文
context = ExecutionContext(
    user_id=1,
    role='operator',
    parameters={},
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
# 输出: 结果: [{'fpy': 0.963}]
```

### 场景 2: 列出可用指标

```python
# 查看所有语义对象
objects = orchestrator.list_semantic_objects()

for obj in objects:
    print(f"{obj['name']}: {obj['description']}")
    print(f"  别名: {obj['aliases']}")

# 输出:
# FPY: First Pass Yield - 一次合格率，衡量产品质量的关键指标
#   别名: ['一次合格率', 'First Pass Yield', '直通率', 'FPY', '良率']
# OutputQty: Output Quantity - 产量，完成的产品数量
#   别名: ['产量', 'Output Qty', 'Output Quantity', '生产量']
# DefectRate: Defect Rate - 不良率，缺陷产品占比
#   别名: ['不良率', 'Defect Rate', '次品率', '缺陷率']
```

### 场景 3: 查看审计历史

```python
# 获取最近的查询记录
history = orchestrator.get_audit_history(limit=5)

for record in history:
    print(f"{record['audit_id']}: {record['question']}")
    print(f"  → {record['semantic_object_name']} ({record['status']})")

# 输出:
# 20260128_153246_xxxxx: 昨天产线A的一次合格率是多少？
#   → FPY (success)
```

---

## 🔍 核心概念

### 6 张核心表

```
┌─────────────────────────────────────────────────┐
│ 1. semantic_object    → 业务概念是什么          │
│ 2. semantic_version   → 哪个版本适用            │
│ 3. logical_definition → 怎么算 (业务公式)      │
│ 4. physical_mapping   → 在哪算 (SQL实现)       │
│ 5. access_policy      → 能不能算 (权限)         │
│ 6. execution_audit    → 为什么敢算 (审计)       │
└─────────────────────────────────────────────────┘
```

### 查询流程

```
自然语言问题
  ↓
[1] 解析语义对象 → FPY
  ↓
[2] 选择版本 → FPY_v1_standard
  ↓
[3] 解析逻辑 → good_qty / total_qty
  ↓
[4] 物理映射 → SELECT ... FROM fact_production_records
  ↓
[5] 权限检查 → operator → ALLOW
  ↓
[6] 渲染 SQL → SELECT SUM(good_qty)/SUM(total_qty)...
  ↓
[7] 执行查询 → {'fpy': 0.963}
  ↓
[8] 审计记录 → 完整决策链路
```

---

## 🧪 测试命令

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_models.py -v
pytest tests/test_integration.py -v
pytest tests/test_error_scenarios.py -v

# 生成覆盖率报告
pytest tests/ --cov=. --cov-report=html

# 运行特定测试
pytest tests/test_integration.py::TestSemanticOrchestratorIntegration::test_successful_query_fpy -v
```

---

## 📊 数据库查询

```bash
sqlite3 data/semantic_layer.db

# 查看语义对象
SELECT id, name, description, domain FROM semantic_object;

# 查看版本
SELECT sv.version_name, so.name as semantic_name, sv.is_active
FROM semantic_version sv
JOIN semantic_object so ON sv.semantic_object_id = so.id;

# 查看业务逻辑
SELECT ld.expression, ld.grain, so.name as semantic_name
FROM logical_definition ld
JOIN semantic_version sv ON ld.semantic_version_id = sv.id
JOIN semantic_object so ON sv.semantic_object_id = so.id;

# 查看执行历史
SELECT audit_id, question, semantic_object_name, status, executed_at
FROM execution_audit
ORDER BY executed_at DESC
LIMIT 10;

# 查看生产数据
SELECT record_date, line, good_qty, total_qty,
    ROUND(CAST(good_qty AS REAL) / total_qty, 3) as fpy
FROM fact_production_records
ORDER BY record_date DESC, line
LIMIT 5;
```

---

## 🎯 常见查询示例

### FPY (一次合格率)
```python
result = orchestrator.query(
    question="昨天产线A的一次合格率是多少？",
    parameters={'line': 'A', 'start_date': '2026-01-27', 'end_date': '2026-01-27'},
    context=context
)
# 结果: [{'fpy': 0.963}]
```

### 产量
```python
result = orchestrator.query(
    question="产线B的产量",
    parameters={'line': 'B', 'start_date': '2026-01-28', 'end_date': '2026-01-28'},
    context=context
)
# 结果: [{'output_qty': 1880}]
```

### 不良率
```python
result = orchestrator.query(
    question="产线A的不良率",
    parameters={'line': 'A', 'start_date': '2026-01-27', 'end_date': '2026-01-27'},
    context=context
)
# 结果: [{'defect_rate': 0.0367}]
```

---

## 🚨 错误处理

### 权限拒绝
```python
# 匿名用户
context = ExecutionContext(user_id=0, role='anonymous', parameters={})

result = orchestrator.query(...)
# result['status'] = 'denied'
# result['error'] = 'Access denied by policy'
```

### 参数缺失
```python
result = orchestrator.query(
    question="昨天产线A的一次合格率是多少？",
    parameters={'line': 'A'},  # 缺少日期
    context=context
)
# result['status'] = 'error'
# result['error'] = 'Missing required parameters: [start_date, end_date]'
```

### 无匹配对象
```python
result = orchestrator.query(
    question="今天的天气怎么样？",  # 无关查询
    parameters={},
    context=context
)
# result['status'] = 'error'
# result['error'] = 'No semantic object found'
```

---

## 📝 代码结构

```
核心模块
├── models.py              # 数据模型 (6个核心类)
├── semantic_resolver.py   # 语义解析
├── policy_engine.py       # 权限控制
├── execution_engine.py    # SQL执行
└── orchestrator.py        # 核心编排器

数据库
├── schema.sql             # 表结构
├── seed_data.sql          # 种子数据
└── data/semantic_layer.db # 数据库文件

测试
├── tests/conftest.py      # 测试配置
├── tests/test_*.py        # 测试文件
└── pytest.ini            # Pytest配置

演示
├── demo_queries.py        # 交互式演示
└── test_basic.py         # 简单测试
```

---

## 🔧 配置和定制

### 添加新的语义对象

```sql
-- 1. 添加语义对象
INSERT INTO semantic_object (name, description, aliases, domain, status)
VALUES (
    'UtilizationRate',
    '设备利用率 - 设备实际运行时间占比',
    '["利用率", "设备利用率", "OEE", "Utilization"]',
    'production',
    'active'
);

-- 2. 添加版本
INSERT INTO semantic_version (semantic_object_id, version_name, effective_from, is_active, description)
VALUES (4, 'UtilizationRate_v1', '2024-01-01', 1, '标准利用率计算');

-- 3. 添加业务逻辑
INSERT INTO logical_definition (semantic_version_id, expression, grain, description, variables)
VALUES (4, 'running_time / total_time', 'line,day', '设备利用率', '["running_time", "total_time"]');

-- 4. 添加物理映射
INSERT INTO physical_mapping (logical_definition_id, engine_type, connection_ref, sql_template, params_schema, priority)
VALUES (4, 'sqlite', 'default',
'SELECT SUM(running_time) / SUM(total_time) as utilization_rate
FROM equipment_status
WHERE line = ''{{ line }}''
  AND record_date BETWEEN ''{{ start_date }}'' AND ''{{ end_date }}''',
'{"line": "string", "start_date": "date", "end_date": "date"}',
1);

-- 5. 添加权限策略
INSERT INTO access_policy (semantic_object_id, role, action, effect, priority)
VALUES (4, 'operator', 'query', 'allow', 1);
```

### 添加新的用户角色

```sql
-- 给 analyst 角色添加更多权限
INSERT INTO access_policy (semantic_object_id, role, action, effect, priority)
VALUES
(1, 'analyst', 'export', 'allow', 1),
(2, 'analyst', 'export', 'allow', 1),
(3, 'analyst', 'export', 'allow', 1);
```

---

## 📚 更多资源

- [完整文档](README.md)
- [测试报告](tests/TEST_REPORT.md)
- [项目总结](PROJECT_SUMMARY.md)
- [测试文档](tests/README.md)

---

## 💡 提示

1. **首次运行** - 数据库会自动创建
2. **日志查看** - 所有决策步骤都有日志输出
3. **审计追踪** - 每次查询都有完整的 decision_trace
4. **SQL 预览** - 使用 preview_only=True 查看 SQL 而不执行
5. **测试覆盖** - 93% 代码覆盖率，79 个测试全部通过

---

**开始探索吧！** 🚀
