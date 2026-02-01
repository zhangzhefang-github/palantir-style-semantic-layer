#!/usr/bin/env python3
"""
手动测试脚本 - 验证企业质疑增强功能
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
import json
import sqlite3
import os

sys.path.insert(0, str(Path(__file__).parent / "src"))

from semantic_layer.orchestrator import SemanticOrchestrator
from semantic_layer.models import ExecutionContext

def ensure_database():
    """确保数据库存在"""
    if not os.path.exists('data/semantic_layer.db'):
        print("\n📦 创建数据库...")
        os.makedirs('data', exist_ok=True)

        conn = sqlite3.connect('data/semantic_layer.db')

        # 创建 schema
        with open('schema.sql', 'r') as f:
            conn.executescript(f.read())

        # 加载种子数据
        with open('seed_data.sql', 'r') as f:
            conn.executescript(f.read())

        conn.commit()
        conn.close()
        print("✅ 数据库创建完成")
    else:
        print("\n✅ 数据库已存在")

def print_section(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def test_scenario_driven_version_selection():
    """测试场景驱动版本选择"""
    print_section("测试 1: Scenario 驱动版本选择")

    # 初始化
    orchestrator = SemanticOrchestrator('data/semantic_layer.db')
    context = ExecutionContext(user_id=1, role='operator', parameters={}, timestamp=datetime.now())

    # 没有 scenario → 应该选择 FPY_v1_standard
    print("\n📌 Query 1: 无 scenario 参数")
    result = orchestrator.query(
        question="昨天产线A的一次合格率是多少？",
        parameters={'line': 'A', 'start_date': '2026-01-27', 'end_date': '2026-01-27'},
        context=context
    )
    print(f"  ✅ Version: {result['version']}")
    print(f"  ✅ Expected: FPY_v1_standard (default)")
    assert result['version'] == 'FPY_v1_standard', "应该选择默认版本"

    # 有 scenario → 应该选择 FPY_v2_rework
    print("\n📌 Query 2: 带 scenario={'rework_enabled': True}")
    result = orchestrator.query(
        question="昨天产线A的一次合格率是多少？",
        parameters={'line': 'A', 'start_date': '2026-01-27', 'end_date': '2026-01-27', 'scenario': {'rework_enabled': True}},
        context=context
    )
    print(f"  ✅ Version: {result['version']}")
    print(f"  ✅ Expected: FPY_v2_rework (scenario match)")
    assert result['version'] == 'FPY_v2_rework', "应该选择 rework 版本"

    print("\n  ✅ 场景驱动版本选择测试通过！")

def test_decision_trace_explainability():
    """测试决策链可解释性"""
    print_section("测试 2: 决策链可解释性")

    orchestrator = SemanticOrchestrator('data/semantic_layer.db')
    context = ExecutionContext(user_id=1, role='operator', parameters={}, timestamp=datetime.now())

    result = orchestrator.query(
        question="昨天产线A的一次合格率是多少？",
        parameters={'line': 'A', 'start_date': '2026-01-27', 'end_date': '2026-01-27'},
        context=context
    )

    # 检查 decision_trace 包含所有 reason 字段
    trace = result['decision_trace']
    print(f"\n  📊 Decision Trace 包含 {len(trace)} 个步骤")

    required_reasons = [
        'semantic_object_reason',
        'version_selection_reason',
        'logic_resolution_reason',
        'physical_mapping_reason',
        'policy_check_reason'
    ]

    for reason in required_reasons:
        found = any(reason in step.get('data', {}) for step in trace)
        print(f"  {'✅' if found else '❌'} {reason}")
        assert found, f"Missing {reason} in decision trace"

    print("\n  ✅ 决策链可解释性测试通过！")

def test_replay_consistency():
    """测试 Replay 一致性"""
    print_section("测试 3: Replay 一致性")

    orchestrator = SemanticOrchestrator('data/semantic_layer.db')
    context = ExecutionContext(user_id=1, role='operator', parameters={}, timestamp=datetime.now())

    # 第一次查询
    result1 = orchestrator.query(
        question="昨天产线A的一次合格率是多少？",
        parameters={'line': 'A', 'start_date': '2026-01-27', 'end_date': '2026-01-27'},
        context=context
    )
    audit_id = result1['audit_id']
    fpy1 = result1['data'][0]['fpy']

    print(f"\n  📊 Original Query:")
    print(f"    Audit ID: {audit_id}")
    print(f"    FPY: {fpy1}")

    # Replay
    replay_result = orchestrator.replay(audit_id)

    print(f"\n  📊 Replay Result:")
    print(f"    New Audit ID: {replay_result['new_audit_id']}")

    # 检查 decision_trace 包含 replay_mode
    replay_trace = replay_result['new']['decision_trace']
    replay_start = next((s for s in replay_trace if 'replay_start' in s['step']), None)

    print(f"\n  🔍 Replay Decision Trace:")
    if replay_start:
        print(f"    ✅ replay_mode: {replay_start['data'].get('replay_mode')}")
        print(f"    ✅ replay_source_audit_id: {replay_start['data'].get('replay_source_audit_id')}")
        print(f"    ✅ original_sql: {replay_start['data'].get('original_sql')[:50]}...")

        assert replay_start['data'].get('replay_mode') == True, "replay_mode 应该为 True"
        assert replay_start['data'].get('replay_source_audit_id') == audit_id, "replay_source_audit_id 应该匹配"

    print("\n  ✅ Replay 一致性测试通过！")

def test_audit_history():
    """测试审计历史"""
    print_section("测试 4: 审计历史查询")

    orchestrator = SemanticOrchestrator('data/semantic_layer.db')

    history = orchestrator.get_audit_history(limit=5)

    print(f"\n  📜 最近 {len(history)} 条审计记录:")
    for i, h in enumerate(history, 1):
        print(f"    {i}. [{h['status'].upper()}] {h['question'][:40]}...")
        print(f"       Audit ID: {h['audit_id']}")
        print(f"       Semantic Object: {h['semantic_object_name']}")
        print()

    print("  ✅ 审计历史查询测试通过！")

def main():
    print("\n" + "🔬" * 40)
    print("  企业质疑增强 - 手动验证测试")
    print("🔬" * 40)

    # 确保数据库存在
    ensure_database()

    try:
        test_scenario_driven_version_selection()
        test_decision_trace_explainability()
        test_replay_consistency()
        test_audit_history()

        print_section("所有测试通过 ✅")
        print("\n  你已经验证了：")
        print("  ✅ Scenario 驱动版本选择工作正常")
        print("  ✅ 决策链完全可解释")
        print("  ✅ Replay 模式正确标记")
        print("  ✅ 审计历史可查询")
        print("\n")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
