#!/usr/bin/env python3
"""
Demo Queries for Palantir-Style Semantic Control Plane

This script demonstrates the complete semantic layer functionality:
- Semantic object resolution
- Version selection
- Policy enforcement
- SQL generation and execution
- Full audit trail
"""

import sys
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

# Add src directory to path for local package imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from semantic_layer.orchestrator import SemanticOrchestrator
from semantic_layer.models import ExecutionContext


# Database configuration
DB_PATH = "data/semantic_layer.db"


def setup_database():
    """
    Initialize database with schema and seed data.
    """
    print("=" * 80)
    print("SETUP: Initializing Database")
    print("=" * 80)

    # Create data directory if needed
    Path("data").mkdir(exist_ok=True)

    # Check if database exists
    db_file = Path(DB_PATH)
    if db_file.exists():
        print(f"✓ Database already exists: {DB_PATH}")
        response = input("Recreate database? (y/N): ").strip().lower()
        if response == 'y':
            db_file.unlink()
            print("  Deleted existing database")
        else:
            print("  Using existing database")
            return

    # Create schema
    print("\nCreating schema...")
    conn = sqlite3.connect(DB_PATH)
    with open('schema.sql', 'r') as f:
        schema_sql = f.read()
        conn.executescript(schema_sql)
    conn.commit()
    conn.close()
    print("✓ Schema created")

    # Load seed data
    print("\nLoading seed data...")
    conn = sqlite3.connect(DB_PATH)
    with open('seed_data.sql', 'r') as f:
        seed_sql = f.read()
        conn.executescript(seed_sql)
    conn.commit()
    conn.close()
    print("✓ Seed data loaded")

    print(f"\n✓ Database initialized: {DB_PATH}")


def print_separator(title: str = ""):
    """Print a visual separator"""
    print("\n" + "=" * 80)
    if title:
        print(f"  {title}")
    print("=" * 80)


def print_result(result: dict):
    """Pretty print query result"""
    print(f"\n📊 QUERY RESULT")
    print(f"  Audit ID: {result.get('audit_id')}")
    print(f"  Status: {result.get('status').upper()}")

    if result.get('status') == 'success':
        print(f"\n  Semantic Object: {result.get('semantic_object')}")
        print(f"  Version: {result.get('version')}")
        print(f"  Logic: {result.get('logic')}")
        print(f"\n  Generated SQL:")
        print("  " + "-" * 76)
        for line in result.get('sql', '').split('\n'):
            print(f"  {line}")
        print("  " + "-" * 76)

        print(f"\n  Execution:")
        print(f"    Rows: {result.get('row_count')}")
        print(f"    Time: {result.get('execution_time_ms')}ms")

        if result.get('data'):
            print(f"\n  Data (first 3 rows):")
            for i, row in enumerate(result.get('data', [])[:3], 1):
                print(f"    Row {i}: {row}")

    elif result.get('status') == 'denied':
        print(f"\n  ❌ ACCESS DENIED: {result.get('error')}")

    elif result.get('status') == 'error':
        print(f"\n  ⚠️  ERROR: {result.get('error')}")
        if result.get('error_type') == 'AmbiguityError':
            print(f"\n  Candidates:")
            for cand in result.get('candidates', []):
                print(f"    - {cand['name']} (ID: {cand['id']}, Domain: {cand['domain']})")

    print(f"\n  Decision Steps: {len(result.get('decision_trace', []))}")


def demo_1_basic_query(orchestrator: SemanticOrchestrator):
    """
    Demo 1: Basic semantic query
    Question: "昨天产线A的一次合格率是多少？"
    """
    print_separator("DEMO 1: Basic Semantic Query")

    # Simulated current context
    context = ExecutionContext(
        user_id=1,
        role='operator',
        parameters={},
        timestamp=datetime.now()
    )

    # Calculate "yesterday"
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    question = "昨天产线A的一次合格率是多少？"

    print(f"\n📝 Question: {question}")
    print(f"👤 User: {context.user_id} (role: {context.role})")

    # Execute query
    result = orchestrator.query(
        question=question,
        parameters={
            'line': 'A',
            'start_date': yesterday,
            'end_date': yesterday
        },
        context=context
    )

    print_result(result)

    return result.get('audit_id')


def demo_2_preview_mode(orchestrator: SemanticOrchestrator):
    """
    Demo 2: Preview mode (dry run)
    Shows SQL generation without execution
    """
    print_separator("DEMO 2: Preview Mode (Dry Run)")

    context = ExecutionContext(user_id=1, role='operator', parameters={})

    today = datetime.now().strftime('%Y-%m-%d')

    question = "今天产线B的产量是多少？"

    print(f"\n📝 Question: {question}")
    print(f"👤 User: {context.user_id} (role: {context.role})")
    print(f"⚠️  PREVIEW MODE - SQL NOT EXECUTED")

    # Preview query
    result = orchestrator.query(
        question=question,
        parameters={
            'line': 'B',
            'start_date': today,
            'end_date': today
        },
        context=context,
        preview_only=True
    )

    print(f"\n  Status: {result.get('status').upper()}")
    print(f"  Semantic Object: {result.get('semantic_object')}")
    print(f"  Version: {result.get('version')}")
    print(f"  Logic: {result.get('logic')}")
    print(f"\n  Generated SQL:")
    print("  " + "-" * 76)
    for line in result.get('sql', '').split('\n'):
        print(f"  {line}")
    print("  " + "-" * 76)


def demo_3_policy_enforcement(orchestrator: SemanticOrchestrator):
    """
    Demo 3: Policy enforcement
    Shows access denial for unauthorized users
    """
    print_separator("DEMO 3: Policy Enforcement (Access Denial)")

    # Simulate anonymous user (no access)
    context = ExecutionContext(
        user_id=999,
        role='anonymous',
        parameters={},
        timestamp=datetime.now()
    )

    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    question = "昨天产线A的不良率是多少？"

    print(f"\n📝 Question: {question}")
    print(f"👤 User: {context.user_id} (role: {context.role})")

    # Try to execute query
    result = orchestrator.query(
        question=question,
        parameters={
            'line': 'A',
            'start_date': yesterday,
            'end_date': yesterday
        },
        context=context
    )

    print_result(result)


def demo_4_ambiguity_detection(orchestrator: SemanticOrchestrator):
    """
    Demo 4: Ambiguity detection
    Shows how system handles ambiguous queries
    """
    print_separator("DEMO 4: Ambiguity Detection")

    context = ExecutionContext(user_id=1, role='operator', parameters={})

    # Intentionally ambiguous query
    question = "产线A的指标是多少？"  # "指标" (metric) is ambiguous

    print(f"\n📝 Question: {question}")
    print(f"👤 User: {context.user_id} (role: {context.role})")
    print(f"⚠️  This question is intentionally ambiguous")

    # Execute query
    result = orchestrator.query(
        question=question,
        parameters={},
        context=context
    )

    print_result(result)


def demo_5_replay(orchestrator: SemanticOrchestrator, audit_id: str):
    """
    Demo 5: Replay functionality
    Re-runs a previous query for verification
    """
    print_separator("DEMO 5: Replay Previous Query")

    print(f"\n🔄 Replaying audit ID: {audit_id}")

    try:
        replay_result = orchestrator.replay(audit_id)

        print(f"\n  Original Audit ID: {replay_result['original_audit_id']}")
        print(f"  New Audit ID: {replay_result.get('new_audit_id')}")
        print(f"  Original Question: {replay_result['original']['question']}")
        print(f"  Original Result: {replay_result['original']['row_count']} rows")

        if replay_result.get('new'):
            print(f"  New Result: {replay_result['new']['row_count']} rows")

        print(f"\n  ✓ Replay successful")

    except Exception as e:
        print(f"\n  ❌ Replay failed: {e}")


def demo_6_list_semantic_objects(orchestrator: SemanticOrchestrator):
    """
    Demo 6: List all available semantic objects
    """
    print_separator("DEMO 6: Available Semantic Objects")

    objects = orchestrator.list_semantic_objects()

    print(f"\n  Found {len(objects)} semantic objects:\n")
    for obj in objects:
        print(f"  • {obj['name']}")
        print(f"    Description: {obj['description']}")
        print(f"    Domain: {obj['domain']}")
        print(f"    Aliases: {', '.join(obj['aliases'])}")
        print()


def demo_7_audit_history(orchestrator: SemanticOrchestrator):
    """
    Demo 7: View audit history
    """
    print_separator("DEMO 7: Audit History")

    history = orchestrator.get_audit_history(limit=10)

    print(f"\n  Recent {len(history)} executions:\n")
    for i, record in enumerate(history, 1):
        print(f"  {i}. {record['audit_id']}")
        print(f"     Question: {record['question']}")
        print(f"     Semantic: {record['semantic_object_name']}")
        print(f"     User: {record['user_role']}")
        print(f"     Status: {record['status'].upper()}")
        print(f"     Time: {record['executed_at']}")
        if record['row_count']:
            print(f"     Rows: {record['row_count']}")
        print()


def main():
    """Main demo execution"""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "  Palantir-Style Semantic Control Plane - Interactive Demo".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "═" * 78 + "╝")

    # Setup database
    setup_database()

    # Initialize orchestrator
    print(f"\nInitializing Semantic Orchestrator...")
    orchestrator = SemanticOrchestrator(DB_PATH)
    print("✓ Orchestrator ready\n")

    # Run demos
    try:
        # Demo 1: Basic query
        audit_id_1 = demo_1_basic_query(orchestrator)
        input("\n[Press Enter to continue...]")

        # Demo 2: Preview mode
        demo_2_preview_mode(orchestrator)
        input("\n[Press Enter to continue...]")

        # Demo 3: Policy enforcement
        demo_3_policy_enforcement(orchestrator)
        input("\n[Press Enter to continue...]")

        # Demo 4: Ambiguity detection
        demo_4_ambiguity_detection(orchestrator)
        input("\n[Press Enter to continue...]")

        # Demo 5: Replay
        if audit_id_1:
            demo_5_replay(orchestrator, audit_id_1)
        input("\n[Press Enter to continue...]")

        # Demo 6: List semantic objects
        demo_6_list_semantic_objects(orchestrator)
        input("\n[Press Enter to continue...]")

        # Demo 7: Audit history
        demo_7_audit_history(orchestrator)

    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")

    print("\n" + "=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)
    print(f"\nDatabase location: {DB_PATH}")
    print("You can inspect the database using:")
    print(f"  sqlite3 {DB_PATH}")
    print("\nExample queries:")
    print("  SELECT * FROM execution_audit;")
    print("  SELECT * FROM semantic_object;")
    print("  SELECT * FROM fact_production_records;")
    print()


if __name__ == "__main__":
    main()
