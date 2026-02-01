"""
Gross Margin Cross-Department Scenario Tests

This test suite demonstrates the core PPT scenario:
- Finance department calculates: (Revenue - Total Cost) / Revenue = 23.5%
- Sales department calculates: (Revenue - Direct Cost) / Revenue = 28.2%
- System automatically selects the correct version based on scenario context

This proves:
1. Same metric can have multiple valid definitions (versions)
2. Scenario-driven version selection works
3. Full audit trail explains which version was used and why
"""

import pytest
import sqlite3
from datetime import datetime
from pathlib import Path
import tempfile
import os

from semantic_layer.orchestrator import SemanticOrchestrator
from semantic_layer.models import ExecutionContext


@pytest.fixture
def gross_margin_db():
    """
    Create a test database with Gross Margin scenario.
    
    Setup:
    - GrossMargin semantic object with two versions:
      - v1_finance: (revenue - total_cost) / revenue (Finance department)
      - v2_sales: (revenue - direct_cost) / revenue (Sales department)
    - Sample financial data for testing
    """
    db_path = tempfile.mktemp(suffix='.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create schema
    schema_path = Path(__file__).parent.parent / 'schema.sql'
    with open(schema_path, 'r') as f:
        conn.executescript(f.read())
    
    # ============================================================
    # 1. Insert GrossMargin semantic object
    # ============================================================
    cursor.execute("""
        INSERT INTO semantic_object (name, description, aliases, domain, status)
        VALUES (
            'GrossMargin', 
            'Gross Margin - 毛利率，衡量盈利能力的核心指标',
            '["毛利率", "Gross Margin", "毛利", "利润率"]',
            'finance',
            'active'
        )
    """)
    
    # ============================================================
    # 2. Insert two versions with different scenario conditions
    # ============================================================
    
    # Finance version: scenario = {"department": "finance"}
    cursor.execute("""
        INSERT INTO semantic_version
        (semantic_object_id, version_name, effective_from, scenario_condition, is_active, priority, description)
        VALUES (
            1, 
            'GrossMargin_v1_finance', 
            '2024-01-01 00:00:00', 
            '{"department": "finance"}', 
            1, 
            10, 
            '财务口径：(收入-总成本)/收入，包含所有成本'
        )
    """)
    
    # Sales version: scenario = {"department": "sales"}
    cursor.execute("""
        INSERT INTO semantic_version
        (semantic_object_id, version_name, effective_from, scenario_condition, is_active, priority, description)
        VALUES (
            1, 
            'GrossMargin_v2_sales', 
            '2024-01-01 00:00:00', 
            '{"department": "sales"}', 
            1, 
            10, 
            '销售口径：(收入-直接成本)/收入，仅含直接成本'
        )
    """)
    
    # Default version (no scenario): for when no department is specified
    cursor.execute("""
        INSERT INTO semantic_version
        (semantic_object_id, version_name, effective_from, scenario_condition, is_active, priority, description)
        VALUES (
            1, 
            'GrossMargin_v0_default', 
            '2024-01-01 00:00:00', 
            NULL, 
            1, 
            0, 
            '默认口径：当未指定部门时使用财务口径'
        )
    """)
    
    # ============================================================
    # 3. Insert logical definitions for each version
    # ============================================================
    
    # Finance version formula
    cursor.execute("""
        INSERT INTO logical_definition (semantic_version_id, expression, grain, description, variables)
        VALUES (
            1, 
            '(revenue - total_cost) / revenue', 
            'region,month', 
            '财务毛利率：包含直接成本和间接成本',
            '["revenue", "total_cost"]'
        )
    """)
    
    # Sales version formula
    cursor.execute("""
        INSERT INTO logical_definition (semantic_version_id, expression, grain, description, variables)
        VALUES (
            2, 
            '(revenue - direct_cost) / revenue', 
            'region,month', 
            '销售毛利率：仅含直接成本',
            '["revenue", "direct_cost"]'
        )
    """)
    
    # Default version formula (same as finance)
    cursor.execute("""
        INSERT INTO logical_definition (semantic_version_id, expression, grain, description, variables)
        VALUES (
            3, 
            '(revenue - total_cost) / revenue', 
            'region,month', 
            '默认毛利率公式',
            '["revenue", "total_cost"]'
        )
    """)
    
    # ============================================================
    # 4. Insert physical mappings (SQL implementations)
    # ============================================================
    
    # Finance version SQL - returns 23.5%
    cursor.execute("""
        INSERT INTO physical_mapping 
        (logical_definition_id, engine_type, connection_ref, sql_template, params_schema, priority, description)
        VALUES (
            1, 
            'sqlite', 
            'default', 
            'SELECT (5000.0 - 3825.0) / 5000.0 as gross_margin',
            '{}', 
            1, 
            '财务口径SQL：(¥5000万收入 - ¥3825万总成本) / ¥5000万 = 23.5%'
        )
    """)
    
    # Sales version SQL - returns 28.2%
    cursor.execute("""
        INSERT INTO physical_mapping 
        (logical_definition_id, engine_type, connection_ref, sql_template, params_schema, priority, description)
        VALUES (
            2, 
            'sqlite', 
            'default', 
            'SELECT (5000.0 - 3590.0) / 5000.0 as gross_margin',
            '{}', 
            1, 
            '销售口径SQL：(¥5000万收入 - ¥3590万直接成本) / ¥5000万 = 28.2%'
        )
    """)
    
    # Default version SQL
    cursor.execute("""
        INSERT INTO physical_mapping 
        (logical_definition_id, engine_type, connection_ref, sql_template, params_schema, priority, description)
        VALUES (
            3, 
            'sqlite', 
            'default', 
            'SELECT (5000.0 - 3825.0) / 5000.0 as gross_margin',
            '{}', 
            1, 
            '默认口径SQL'
        )
    """)
    
    # ============================================================
    # 5. Insert access policies
    # ============================================================
    cursor.execute("""
        INSERT INTO access_policy (semantic_object_id, role, action, condition, effect, priority)
        VALUES (1, 'finance_manager', 'query', NULL, 'allow', 1)
    """)
    
    cursor.execute("""
        INSERT INTO access_policy (semantic_object_id, role, action, condition, effect, priority)
        VALUES (1, 'sales_manager', 'query', NULL, 'allow', 1)
    """)
    
    cursor.execute("""
        INSERT INTO access_policy (semantic_object_id, role, action, condition, effect, priority)
        VALUES (1, 'cfo', 'query', NULL, 'allow', 1)
    """)
    
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Cleanup
    try:
        os.unlink(db_path)
    except:
        pass


class TestGrossMarginCrossDepartment:
    """
    Test suite: Cross-department Gross Margin scenario.
    
    This is the core PPT demo scenario:
    - CFO asks: "What's the Gross Margin for East Region last month?"
    - Finance says: 23.5%
    - Sales says: 28.2%
    - System automatically selects based on scenario context
    """
    
    def test_finance_department_gets_finance_version(self, gross_margin_db):
        """
        Test: Finance department context returns finance version (23.5%).
        
        Scenario:
        - User role: finance_manager
        - Scenario: {"department": "finance"}
        
        Expected:
        - Version: GrossMargin_v1_finance
        - Result: 23.5% (0.235)
        - Logic: (revenue - total_cost) / revenue
        """
        orchestrator = SemanticOrchestrator(gross_margin_db)
        
        context = ExecutionContext(
            user_id=1,
            role='finance_manager',
            parameters={},
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
        
        # Should succeed
        assert result['status'] == 'success'
        
        # Should select finance version
        assert result['version'] == 'GrossMargin_v1_finance'
        
        # Should return 23.5%
        assert abs(result['data'][0]['gross_margin'] - 0.235) < 0.001
        
        # Decision trace should explain version selection
        trace = result['decision_trace']
        version_step = next(s for s in trace if 'resolve_version_complete' in s['step'])
        assert 'finance' in version_step['data'].get('version_name', '').lower() or \
               'finance' in result['version'].lower()
    
    def test_sales_department_gets_sales_version(self, gross_margin_db):
        """
        Test: Sales department context returns sales version (28.2%).
        
        Scenario:
        - User role: sales_manager
        - Scenario: {"department": "sales"}
        
        Expected:
        - Version: GrossMargin_v2_sales
        - Result: 28.2% (0.282)
        - Logic: (revenue - direct_cost) / revenue
        """
        orchestrator = SemanticOrchestrator(gross_margin_db)
        
        context = ExecutionContext(
            user_id=2,
            role='sales_manager',
            parameters={},
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
        
        # Should succeed
        assert result['status'] == 'success'
        
        # Should select sales version
        assert result['version'] == 'GrossMargin_v2_sales'
        
        # Should return 28.2%
        assert abs(result['data'][0]['gross_margin'] - 0.282) < 0.001
    
    def test_no_department_falls_back_to_default(self, gross_margin_db):
        """
        Test: No department specified falls back to default version.
        
        Scenario:
        - No scenario parameter provided
        
        Expected:
        - Version: GrossMargin_v0_default
        - Uses default (finance) calculation
        """
        orchestrator = SemanticOrchestrator(gross_margin_db)
        
        context = ExecutionContext(
            user_id=3,
            role='cfo',
            parameters={},
            timestamp=datetime.now()
        )
        
        result = orchestrator.query(
            question="上月华东区毛利率是多少？",
            parameters={
                'region': '华东',
                'period': '2026-01'
                # No scenario - should use default
            },
            context=context
        )
        
        # Should succeed
        assert result['status'] == 'success'
        
        # Should select default version
        assert 'default' in result['version'].lower()
    
    def test_same_question_different_answers_both_correct(self, gross_margin_db):
        """
        Test: Same question can have different valid answers based on context.
        
        This is the KEY enterprise insight:
        - Both 23.5% and 28.2% are "correct"
        - They are just calculated with different business rules
        - The system tracks which rule was used
        """
        orchestrator = SemanticOrchestrator(gross_margin_db)
        
        # Finance query
        finance_context = ExecutionContext(
            user_id=1,
            role='finance_manager',
            parameters={},
            timestamp=datetime.now()
        )
        
        finance_result = orchestrator.query(
            question="毛利率是多少？",
            parameters={'scenario': {'department': 'finance'}},
            context=finance_context
        )
        
        # Sales query
        sales_context = ExecutionContext(
            user_id=2,
            role='sales_manager',
            parameters={},
            timestamp=datetime.now()
        )
        
        sales_result = orchestrator.query(
            question="毛利率是多少？",
            parameters={'scenario': {'department': 'sales'}},
            context=sales_context
        )
        
        # Both should succeed
        assert finance_result['status'] == 'success'
        assert sales_result['status'] == 'success'
        
        # Different versions selected
        assert finance_result['version'] != sales_result['version']
        
        # Different results
        finance_margin = finance_result['data'][0]['gross_margin']
        sales_margin = sales_result['data'][0]['gross_margin']
        assert abs(finance_margin - 0.235) < 0.001  # 23.5%
        assert abs(sales_margin - 0.282) < 0.001    # 28.2%
        
        # Both have audit trails
        assert finance_result['audit_id'] is not None
        assert sales_result['audit_id'] is not None
        assert finance_result['audit_id'] != sales_result['audit_id']
    
    def test_audit_trail_explains_version_selection(self, gross_margin_db):
        """
        Test: Audit trail clearly explains why a version was selected.
        
        This is critical for enterprise trust:
        - When CFO asks "why 23.5% not 28.2%?"
        - System can show: "Because scenario was finance department"
        """
        orchestrator = SemanticOrchestrator(gross_margin_db)
        
        context = ExecutionContext(
            user_id=1,
            role='finance_manager',
            parameters={},
            timestamp=datetime.now()
        )
        
        result = orchestrator.query(
            question="毛利率是多少？",
            parameters={'scenario': {'department': 'finance'}},
            context=context
        )
        
        # Should have decision trace
        assert 'decision_trace' in result
        trace = result['decision_trace']
        
        # Should have version selection step
        version_steps = [s for s in trace if 'version' in s['step'].lower()]
        assert len(version_steps) > 0
        
        # Should explain the selection
        version_step = next(s for s in trace if 'resolve_version_complete' in s['step'])
        assert 'version_selection_reason' in version_step['data']
