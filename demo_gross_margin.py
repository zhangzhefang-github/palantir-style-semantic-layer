#!/usr/bin/env python3
"""
毛利率跨部门口径冲突演示 - 与 PPT 场景一致

场景：财务总监问"上月华东区毛利率是多少？"
- 财务部口径：(收入-总成本)/收入 = 23.5%
- 销售部口径：(收入-直接成本)/收入 = 28.2%

演示重点：
1. 场景驱动的版本选择
2. 完整审计链路
3. 不同部门看到不同结果
"""

import os
import sys
import sqlite3

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from datetime import datetime
from semantic_layer import SemanticOrchestrator
from semantic_layer.models import ExecutionContext

def setup_database():
    """Initialize database with schema and seed data."""
    db_path = 'data/semantic_layer.db'
    os.makedirs('data', exist_ok=True)
    
    # Remove old database to ensure fresh data
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    
    # Load schema
    with open('schema.sql', 'r') as f:
        conn.executescript(f.read())
    
    # Load seed data
    with open('seed_data.sql', 'r') as f:
        conn.executescript(f.read())
    
    conn.close()
    print("✅ 数据库已初始化")
    return db_path

def show_database_state(db_path):
    """Display relevant database state for demo."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n" + "=" * 80)
    print("🗄️  数据库状态（GrossMargin 相关）")
    print("-" * 80)
    
    # GrossMargin semantic object
    print("\n1. semantic_object 表（毛利率）:")
    cursor.execute("SELECT id, name, description, domain FROM semantic_object WHERE name = 'GrossMargin'")
    for row in cursor.fetchall():
        print(f"   • ID={row[0]}, Name={row[1]}")
        print(f"     描述: {row[2]}")
        print(f"     域: {row[3]}")
    
    # GrossMargin versions
    print("\n2. semantic_version 表（毛利率版本）:")
    cursor.execute("""
        SELECT sv.id, sv.version_name, sv.scenario_condition, sv.priority, sv.description
        FROM semantic_version sv
        JOIN semantic_object so ON sv.semantic_object_id = so.id
        WHERE so.name = 'GrossMargin'
        ORDER BY sv.priority DESC
    """)
    for row in cursor.fetchall():
        print(f"   • ID={row[0]}, Name={row[1]}")
        print(f"     Scenario: {row[2]}")
        print(f"     Priority: {row[3]}")
        print(f"     描述: {row[4]}")
    
    # Logical definitions
    print("\n3. logical_definition 表（业务公式）:")
    cursor.execute("""
        SELECT ld.id, sv.version_name, ld.expression, ld.grain
        FROM logical_definition ld
        JOIN semantic_version sv ON ld.semantic_version_id = sv.id
        JOIN semantic_object so ON sv.semantic_object_id = so.id
        WHERE so.name = 'GrossMargin'
    """)
    for row in cursor.fetchall():
        print(f"   • Version: {row[1]}")
        print(f"     公式: {row[2]}")
        print(f"     粒度: {row[3]}")
    
    # Finance data
    print("\n4. fact_finance_records 表（华东区 2026-01 数据）:")
    cursor.execute("""
        SELECT region, period, product_line, revenue, direct_cost, indirect_cost, total_cost,
               ROUND((revenue - total_cost) * 100.0 / revenue, 1) as finance_margin,
               ROUND((revenue - direct_cost) * 100.0 / revenue, 1) as sales_margin
        FROM fact_finance_records
        WHERE region = '华东' AND period = '2026-01'
    """)
    for row in cursor.fetchall():
        print(f"   • 产品线: {row[2]}")
        print(f"     收入: ¥{row[3]:,.0f}, 直接成本: ¥{row[4]:,.0f}, 间接成本: ¥{row[5]:,.0f}")
        print(f"     财务口径毛利率: {row[7]}%, 销售口径毛利率: {row[8]}%")
    
    # Calculate total
    cursor.execute("""
        SELECT 
            SUM(revenue) as total_revenue,
            SUM(direct_cost) as total_direct,
            SUM(total_cost) as total_cost,
            ROUND((SUM(revenue) - SUM(total_cost)) * 100.0 / SUM(revenue), 1) as finance_margin,
            ROUND((SUM(revenue) - SUM(direct_cost)) * 100.0 / SUM(revenue), 1) as sales_margin
        FROM fact_finance_records
        WHERE region = '华东' AND period = '2026-01'
    """)
    row = cursor.fetchone()
    print(f"\n   📊 华东区 2026-01 汇总:")
    print(f"      总收入: ¥{row[0]:,.0f}")
    print(f"      财务口径毛利率: {row[3]}%  ← 财务部看到的")
    print(f"      销售口径毛利率: {row[4]}%  ← 销售部看到的")
    
    conn.close()

def demo_finance_query(orchestrator):
    """Demo: Finance department query."""
    print("\n" + "=" * 80)
    print("💰 场景 1：财务经理查询毛利率")
    print("-" * 80)
    
    context = ExecutionContext(
        user_id=1,
        role='finance_manager',
        parameters={'department': 'finance'},
        timestamp=datetime.now()
    )
    
    result = orchestrator.query(
        question="上月华东区毛利率是多少？",
        parameters={
            'region': '华东',
            'period': '2026-01',
            'scenario': {'department': 'finance'}
        },
        context=context
    )
    
    print(f"\n📊 查询结果:")
    print(f"   问题: 上月华东区毛利率是多少？")
    print(f"   部门: 财务部")
    print(f"   ✅ Version: {result.get('version_name', 'N/A')}")
    print(f"   ✅ 公式: (收入-总成本)/收入")
    
    if result.get('status') == 'success' and result.get('data'):
        margin = result['data'][0].get('gross_margin', 0) * 100
        print(f"   ✅ 毛利率: {margin:.1f}%")
    else:
        print(f"   ⚠️  结果: {result}")
    
    print(f"   ✅ Audit ID: {result.get('audit_id', 'N/A')}")
    
    return result

def demo_sales_query(orchestrator):
    """Demo: Sales department query."""
    print("\n" + "=" * 80)
    print("📈 场景 2：销售经理查询毛利率")
    print("-" * 80)
    
    context = ExecutionContext(
        user_id=2,
        role='sales_manager',
        parameters={'department': 'sales'},
        timestamp=datetime.now()
    )
    
    result = orchestrator.query(
        question="上月华东区毛利率是多少？",
        parameters={
            'region': '华东',
            'period': '2026-01',
            'scenario': {'department': 'sales'}
        },
        context=context
    )
    
    print(f"\n📊 查询结果:")
    print(f"   问题: 上月华东区毛利率是多少？")
    print(f"   部门: 销售部")
    print(f"   ✅ Version: {result.get('version_name', 'N/A')}")
    print(f"   ✅ 公式: (收入-直接成本)/收入")
    
    if result.get('status') == 'success' and result.get('data'):
        margin = result['data'][0].get('gross_margin', 0) * 100
        print(f"   ✅ 毛利率: {margin:.1f}%")
    else:
        print(f"   ⚠️  结果: {result}")
    
    print(f"   ✅ Audit ID: {result.get('audit_id', 'N/A')}")
    
    return result

def demo_default_query(orchestrator):
    """Demo: No department specified (default version)."""
    print("\n" + "=" * 80)
    print("🔍 场景 3：不指定部门（使用默认版本）")
    print("-" * 80)
    
    context = ExecutionContext(
        user_id=3,
        role='operator',
        parameters={},
        timestamp=datetime.now()
    )
    
    result = orchestrator.query(
        question="上月华东区毛利率是多少？",
        parameters={
            'region': '华东',
            'period': '2026-01'
        },
        context=context
    )
    
    print(f"\n📊 查询结果:")
    print(f"   问题: 上月华东区毛利率是多少？")
    print(f"   部门: 未指定")
    print(f"   ✅ Version: {result.get('version_name', 'N/A')}")
    
    if result.get('status') == 'success' and result.get('data'):
        margin = result['data'][0].get('gross_margin', 0) * 100
        print(f"   ✅ 毛利率: {margin:.1f}%")
    else:
        print(f"   ⚠️  结果: {result}")
    
    print(f"   ✅ Audit ID: {result.get('audit_id', 'N/A')}")
    
    return result

def main():
    print("=" * 80)
    print("🔍 Palantir-Style Semantic Control Layer - 毛利率跨部门口径冲突演示")
    print("=" * 80)
    print('\n📝 场景：财务总监问"上月华东区毛利率是多少？"')
    print("   - 财务部口径：(收入-总成本)/收入")
    print("   - 销售部口径：(收入-直接成本)/收入")
    print("   - 传统做法：开会扯皮 3 小时")
    print("   - 语义控制面：系统根据上下文自动选版本")
    
    # Setup
    db_path = setup_database()
    
    # Show database state
    show_database_state(db_path)
    
    # Initialize orchestrator
    print("\n" + "=" * 80)
    print("[步骤 0] 初始化 SemanticOrchestrator")
    print("-" * 80)
    orchestrator = SemanticOrchestrator(db_path)
    
    # Run demos
    finance_result = demo_finance_query(orchestrator)
    sales_result = demo_sales_query(orchestrator)
    default_result = demo_default_query(orchestrator)
    
    # Summary
    print("\n" + "=" * 80)
    print("🎯 总结：跨部门口径冲突解决方案")
    print("=" * 80)
    print("""
┌─────────────────────────────────────────────────────────────────────────────┐
│  传统做法                       │  语义控制面                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  财务说 23.5%                   │  scenario={'department':'finance'}       │
│  销售说 28.2%                   │  → GrossMargin_v1_finance (score=2)      │
│  老板问到底是多少？              │  → 23.5% + Audit ID 可追溯               │
│  开会扯皮 3 小时                 │                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  "都对，但口径不同"              │  每个版本有明确的定义和适用场景          │
│  "谁也说不清"                   │  每个查询都有 15 步决策链可追溯          │
└─────────────────────────────────────────────────────────────────────────────┘
""")
    
    print("✅ 核心价值：")
    print("   1️⃣ 场景驱动版本选择：系统根据上下文自动选版本，不再靠人脑记")
    print("   2️⃣ 完整审计链路：每一步决策都有记录，出问题可以复盘")
    print("   3️⃣ 口径透明：每个版本的公式和适用场景都在元数据中定义")
    print("\n" + "=" * 80)

if __name__ == '__main__':
    main()
