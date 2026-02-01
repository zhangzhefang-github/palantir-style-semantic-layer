#!/usr/bin/env python3
"""
详细日志演示 - 显示完整调用链

通过阅读这个日志，你可以理解：
- 每一步调用了哪个函数
- 查询了哪些数据库表
- SQL语句是什么
- 数据如何流转

不需要看代码，只看日志就能理解系统运行。
"""
import sys
import logging
from pathlib import Path
from datetime import datetime
import sqlite3
import os

# 配置详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(levelname)s] %(name)s:%(lineno)d] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

sys.path.insert(0, str(Path(__file__).parent / "src"))

from semantic_layer.orchestrator import SemanticOrchestrator
from semantic_layer.models import ExecutionContext

def ensure_database():
    """确保数据库存在"""
    if not os.path.exists('data/semantic_layer.db'):
        print("\n" + "=" * 80)
        print("初始化数据库...")
        print("=" * 80)
        os.makedirs('data', exist_ok=True)
        conn = sqlite3.connect('data/semantic_layer.db')
        with open('schema.sql', 'r') as f:
            conn.executescript(f.read())
        with open('seed_data.sql', 'r') as f:
            conn.executescript(f.read())
        conn.commit()
        conn.close()
        print("✅ 数据库创建完成\n")
    else:
        print("\n✅ 数据库已存在\n")

def demo_detailed_logs():
    """演示完整调用链日志"""
    print("=" * 80)
    print("🔍 Palantir-Style Semantic Control Layer - 完整调用链日志演示")
    print("=" * 80)
    print("\n📝 场景：查询昨天产线A的一次合格率（FPY）")
    print("   - 有 scenario 参数：触发 FPY_v2_rework 版本")
    print("   - 包含返工数量的计算")
    print("\n" + "=" * 80)

    # 查询数据库以显示初始状态
    print("\n🗄️  数据库初始状态（执行查询前）")
    print("-" * 80)
    conn = sqlite3.connect('data/semantic_layer.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 显示语义对象
    print("\n1. semantic_object 表（可用的语义对象）:")
    cursor.execute("SELECT id, name, description FROM semantic_object")
    for row in cursor.fetchall():
        print(f"   • ID={row['id']}, Name={row['name']}, Desc={row['description'][:30]}...")

    # 显示语义版本
    print("\n2. semantic_version 表（FPY 的版本列表）:")
    cursor.execute("SELECT id, version_name, scenario_condition, priority, is_active FROM semantic_version WHERE semantic_object_id=1")
    for row in cursor.fetchall():
        scenario = row['scenario_condition'] or 'NULL'
        print(f"   • ID={row['id']}, Name={row['version_name']}, Scenario={scenario}, Priority={row['priority']}, Active={row['is_active']}")

    # 显示逻辑定义
    print("\n3. logical_definition 表（业务公式）:")
    cursor.execute("""
        SELECT ld.id, ld.expression, sv.version_name, ld.grain
        FROM logical_definition ld
        JOIN semantic_version sv ON ld.semantic_version_id = sv.id
        WHERE sv.semantic_object_id = 1
    """)
    for row in cursor.fetchall():
        print(f"   • ID={row['id']}, Formula={row['expression']}, Version={row['version_name']}, Grain={row['grain']}")

    # 显示物理映射
    print("\n4. physical_mapping 表（SQL 实现）:")
    cursor.execute("""
        SELECT pm.id, pm.sql_template, pm.priority, pm.engine_type, sv.version_name
        FROM physical_mapping pm
        JOIN logical_definition ld ON pm.logical_definition_id = ld.id
        JOIN semantic_version sv ON ld.semantic_version_id = sv.id
        WHERE sv.semantic_object_id = 1
        ORDER BY pm.priority DESC
    """)
    for row in cursor.fetchall():
        sql_preview = row['sql_template'].replace('\n', ' ')[:80] + "..."
        print(f"   • Mapping ID={row['id']}, Priority={row['priority']}, Version={row['version_name']}")
        print(f"      SQL: {sql_preview}")

    # 显示访问策略
    print("\n5. access_policy 表（权限规则）:")
    cursor.execute("SELECT * FROM access_policy WHERE semantic_object_id=1")
    for row in cursor.fetchall():
        print(f"   • Role={row['role']}, Action={row['action']}, Effect={row['effect']}, Priority={row['priority']}")

    # 显示生产数据
    print("\n6. fact_production_records 表（实际数据，Line A, 2026-01-27）:")
    cursor.execute("""
        SELECT record_date, line, product_id, good_qty, rework_qty, total_qty, shift
        FROM fact_production_records
        WHERE line='A' AND record_date='2026-01-27'
        ORDER BY shift
    """)
    for row in cursor.fetchall():
        fpy = row['good_qty'] / row['total_qty']
        print(f"   • Shift={row['shift']}, Good={row['good_qty']}, Rework={row['rework_qty']}, Total={row['total_qty']}, Shift FPY={fpy:.3f}")

    conn.close()

    print("\n" + "=" * 80)

    # 初始化
    print("\n[步骤 0] 初始化 SemanticOrchestrator")
    print("-" * 80)
    orchestrator = SemanticOrchestrator('data/semantic_layer.db')

    # 创建上下文
    context = ExecutionContext(
        user_id=1,
        role='operator',
        parameters={},
        timestamp=datetime.now()
    )

    # 执行查询
    print("\n[步骤 7] 执行语义查询（完整流程）")
    print("-" * 80)
    print("问题: 昨天产线A的一次合格率是多少？")
    print("参数: {'line': 'A', 'start_date': '2026-01-27', 'end_date': '2026-01-27', 'scenario': {'rework_enabled': True}}")
    print()

    result = orchestrator.query(
        question="昨天产线A的一次合格率是多少？",
        parameters={
            'line': 'A',
            'start_date': '2026-01-27',
            'end_date': '2026-01-27',
            'scenario': {'rework_enabled': True}
        },
        context=context
    )

    print("\n" + "=" * 80)
    print("📊 查询结果")
    print("=" * 80)
    print(f"✅ 状态: {result['status'].upper()}")
    print(f"✅ Semantic Object: {result.get('semantic_object', 'N/A')}")
    print(f"✅ Version: {result.get('version', 'N/A')}")
    print(f"✅ Logic: {result.get('logic', 'N/A')}")
    print(f"✅ Data: {result.get('data', [])}")
    print(f"✅ Row Count: {result.get('row_count', 0)}")
    print(f"✅ Execution Time: {result.get('execution_time_ms', 0)}ms")
    print(f"✅ Audit ID: {result.get('audit_id', 'N/A')}")

    # 显示决策链摘要
    print("\n" + "=" * 80)
    print("🔗 决策链摘要（共 {} 步）".format(len(result.get('decision_trace', []))))
    print("=" * 80)

    for i, step in enumerate(result.get('decision_trace', []), 1):
        step_name = step.get('step', 'unknown')
        print(f"\n{i}. {step_name}")
        print("   " + "-" * 70)

        # 提取关键信息
        data = step.get('data', {})

        if 'semantic_object_name' in data:
            print(f"   → Semantic Object: {data['semantic_object_name']}")
            print(f"   → Reason: {data.get('semantic_object_reason', 'N/A')}")

        elif 'version_id' in data:
            print(f"   → Version ID: {data['version_id']}")
            print(f"   → Version Name: {data.get('version_name', 'N/A')}")
            print(f"   → Scenario Condition: {data.get('scenario_condition', 'N/A')}")
            print(f"   → Priority: {data.get('priority', 'N/A')}")
            print(f"   → Reason: {data.get('version_selection_reason', 'N/A')}")

        elif 'logical_definition_id' in data:
            print(f"   → Logical Definition ID: {data['logical_definition_id']}")
            print(f"   → Expression: {data.get('logic_expression', 'N/A')}")
            print(f"   → Grain: {data.get('grain', 'N/A')}")
            print(f"   → Reason: {data.get('logic_resolution_reason', 'N/A')}")

        elif 'physical_mapping_id' in data:
            print(f"   → Physical Mapping ID: {data['physical_mapping_id']}")
            print(f"   → Engine: {data.get('engine_type', 'N/A')}")
            print(f"   → Connection: {data.get('connection_ref', 'N/A')}")
            print(f"   → Priority: {data.get('priority', 'N/A')}")
            print(f"   → Reason: {data.get('physical_mapping_reason', 'N/A')}")

        elif 'policy_decision' in data:
            policy = data.get('policy_details', {})
            print(f"   → Decision: {data.get('policy_decision', 'N/A')}")
            print(f"   → Allow: {policy.get('allow', 'N/A')}")
            print(f"   → Reason: {data.get('policy_reason', 'N/A')}")
            print(f"   → Policy Count: {policy.get('policy_count', 'N/A')}")

        elif 'sql_preview' in data:
            sql = data.get('sql_preview', 'N/A')
            print(f"   → SQL (first 100 chars): {sql[:100]}...")

        elif 'row_count' in data:
            print(f"   → Row Count: {data.get('row_count', 'N/A')}")
            print(f"   → Execution Time: {data.get('execution_time_ms', 'N/A')}ms")
            print(f"   → Result: {data.get('execution_result', 'N/A')}")

        elif 'replay_mode' in data:
            print(f"   → Replay Mode: {data.get('replay_mode', 'N/A')}")
            print(f"   → Replay Source Audit ID: {data.get('replay_source_audit_id', 'N/A')}")
            print(f"   → Original SQL: {data.get('original_sql', 'N/A')[:80]}...")
            print(f"   → Reason: {data.get('replay_reason', 'N/A')}")

    print("\n" + "=" * 80)
    print("🎯 总结")
    print("=" * 80)
    print("通过上面的日志，你可以看到：")
    print()
    print("1️⃣ 语义解析阶段")
    print("   - 调用 semantic_resolver.resolve_semantic_object()")
    print("   - 查询 semantic_object 表（关键词匹配）")
    print("   - 返回 FPY 语义对象")
    print()
    print("2️⃣  版本选择阶段")
    print("   - 调用 semantic_resolver.resolve_version()")
    print("   - 查询 semantic_version 表（获取所有版本）")
    print("   - ScenarioMatcher 评估每个版本：")
    print("     • FPY_v1_standard: score=1 (default, no scenario match)")
    print("     • FPY_v2_rework: score=2 (scenario match: rework_enabled=True)")
    print("   - 选择 FPY_v2_rework（score 最高）")
    print("   - 查询 logical_definition 表（获取业务公式）")
    print()
    print("3️⃣ 物理映射阶段")
    print("   - 调用 execution_engine.resolve_physical_mapping()")
    print("   - 查询 physical_mapping 表（SQL 实现）")
    print("   - 选择 priority=2 的 mapping（FPY v2 with rework）")
    print()
    print("4️⃣ SQL 渲染阶段")
    print("   - 调用 execution_engine.render_sql()")
    print("   - 使用 Jinja2 渲染 SQL 模板")
    print("   - 替换参数: {{ line }} → 'A', {{ start_date }} → '2026-01-27'")
    print()
    print("5️⃣ 策略检查阶段")
    print("   - 调用 policy_engine.check_access()")
    print("   - 查询 access_policy 表（权限规则）")
    print("   - 检查: operator role 可以 query FPY")
    print("   - 决策: ALLOW")
    print()
    print("6️⃣ 执行阶段")
    print("   - 调用 execution_engine.execute()")
    print("   - 执行 SQL: SELECT SUM(CAST(good_qty + rework_qty AS REAL)) / ...")
    print("   - 查询 fact_production_records 表（数据）")
    print("   - 返回结果: FPY = 0.9867 (包含返工)")
    print()
    print("7️⃣ 审计阶段")
    print("   - 调用 orchestrator._save_audit()")
    print("   - 插入 execution_audit 表（审计记录）")
    print("   - 记录完整的 decision_trace")
    print()
    print("=" * 80)

if __name__ == "__main__":
    ensure_database()
    demo_detailed_logs()
