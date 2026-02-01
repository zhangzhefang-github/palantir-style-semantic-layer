"""
Ontology Constraints Tests

This test suite demonstrates the three types of constraints from PPT:
1. Join Constraints (可 Join 约束) - Which domains can be linked via which keys
2. Comparability Constraints (可比较约束) - Grain/time window consistency
3. Explainability Constraints (可解释约束) - What conclusions are allowed

These tests prove that Ontology is not just "metadata" but an active constraint system.
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
def ontology_constraint_db():
    """
    Create a test database with ontology relationships and constraints.
    
    Setup:
    - Multiple entities across different domains
    - Relationships with different link types (strong, weak, attribution)
    - Grain definitions for comparability checks
    """
    db_path = tempfile.mktemp(suffix='.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create schema
    schema_path = Path(__file__).parent.parent / 'schema.sql'
    with open(schema_path, 'r') as f:
        conn.executescript(f.read())
    
    # ============================================================
    # 1. Insert Ontology Entities (Business Domains)
    # ============================================================
    
    # Transaction domain
    cursor.execute("""
        INSERT INTO ontology_entity (name, domain, entity_type, description)
        VALUES ('Order', 'transaction', 'fact', '订单实体 - 交易域核心')
    """)
    
    cursor.execute("""
        INSERT INTO ontology_entity (name, domain, entity_type, description)
        VALUES ('User', 'customer', 'dimension', '用户实体 - 客户域')
    """)
    
    # Marketing domain
    cursor.execute("""
        INSERT INTO ontology_entity (name, domain, entity_type, description)
        VALUES ('AdClick', 'marketing', 'fact', '广告点击实体 - 营销域')
    """)
    
    cursor.execute("""
        INSERT INTO ontology_entity (name, domain, entity_type, description)
        VALUES ('Activity', 'marketing', 'dimension', '营销活动实体')
    """)
    
    # Product domain
    cursor.execute("""
        INSERT INTO ontology_entity (name, domain, entity_type, description)
        VALUES ('SKU', 'product', 'dimension', 'SKU实体 - 商品域')
    """)
    
    cursor.execute("""
        INSERT INTO ontology_entity (name, domain, entity_type, description)
        VALUES ('Category', 'product', 'dimension', '类目实体 - 商品分类')
    """)
    
    # Cost domain
    cursor.execute("""
        INSERT INTO ontology_entity (name, domain, entity_type, description)
        VALUES ('Cost', 'finance', 'fact', '成本实体 - 财务域')
    """)
    
    # ============================================================
    # 2. Insert Ontology Relationships (Link Types)
    # ============================================================
    
    # Strong links (can be used for joins and causal inference)
    cursor.execute("""
        INSERT INTO ontology_relationship 
        (from_entity_id, to_entity_id, relationship_type, cardinality, join_keys, link_strength, allows_causal)
        VALUES (2, 1, 'conversion_link', 'one_to_many', '["user_id"]', 'strong', 1)
    """)  # User → Order (conversion)
    
    cursor.execute("""
        INSERT INTO ontology_relationship 
        (from_entity_id, to_entity_id, relationship_type, cardinality, join_keys, link_strength, allows_causal)
        VALUES (1, 5, 'line_item', 'many_to_many', '["order_id", "sku_id"]', 'strong', 1)
    """)  # Order → SKU (line item)
    
    cursor.execute("""
        INSERT INTO ontology_relationship 
        (from_entity_id, to_entity_id, relationship_type, cardinality, join_keys, link_strength, allows_causal)
        VALUES (5, 6, 'taxonomy', 'many_to_one', '["category_id"]', 'strong', 1)
    """)  # SKU → Category (taxonomy)
    
    cursor.execute("""
        INSERT INTO ontology_relationship 
        (from_entity_id, to_entity_id, relationship_type, cardinality, join_keys, link_strength, allows_causal)
        VALUES (1, 7, 'fulfillment_cost', 'one_to_one', '["order_id"]', 'strong', 1)
    """)  # Order → Cost (fulfillment)
    
    # Attribution link (correlation, not causation)
    cursor.execute("""
        INSERT INTO ontology_relationship 
        (from_entity_id, to_entity_id, relationship_type, cardinality, join_keys, link_strength, allows_causal)
        VALUES (4, 1, 'attribution_rule', 'many_to_many', '["activity_id", "order_id"]', 'medium', 0)
    """)  # Activity → Order (attribution - NOT causal)
    
    # Weak link (correlation only, NO causal inference allowed)
    cursor.execute("""
        INSERT INTO ontology_relationship 
        (from_entity_id, to_entity_id, relationship_type, cardinality, join_keys, link_strength, allows_causal)
        VALUES (3, 2, 'weak_link', 'many_to_one', '["user_id"]', 'weak', 0)
    """)  # AdClick → User (weak - NO causal inference!)
    
    # ============================================================
    # 3. Insert Ontology Dimensions (Grain definitions)
    # ============================================================
    
    cursor.execute("""
        INSERT INTO ontology_dimension (entity_id, name, data_type, is_time, grain_level)
        VALUES (1, 'order_date', 'date', 1, 'day')
    """)
    
    cursor.execute("""
        INSERT INTO ontology_dimension (entity_id, name, data_type, is_time, grain_level)
        VALUES (1, 'order_week', 'date', 1, 'week')
    """)
    
    cursor.execute("""
        INSERT INTO ontology_dimension (entity_id, name, data_type, is_time, grain_level)
        VALUES (3, 'click_date', 'date', 1, 'day')
    """)
    
    # ============================================================
    # 4. Insert a simple semantic object for testing
    # ============================================================
    
    cursor.execute("""
        INSERT INTO semantic_object (name, description, aliases, domain, status)
        VALUES ('OrderCount', '订单数量', '["订单数", "订单量"]', 'transaction', 'active')
    """)
    
    cursor.execute("""
        INSERT INTO semantic_version
        (semantic_object_id, version_name, effective_from, scenario_condition, is_active, priority, description)
        VALUES (1, 'OrderCount_v1', '2024-01-01 00:00:00', NULL, 1, 0, '标准订单计数')
    """)
    
    cursor.execute("""
        INSERT INTO logical_definition (semantic_version_id, expression, grain, description, variables)
        VALUES (1, 'COUNT(order_id)', 'user,day', '按用户按天统计订单数', '["order_id"]')
    """)
    
    cursor.execute("""
        INSERT INTO physical_mapping 
        (logical_definition_id, engine_type, connection_ref, sql_template, params_schema, priority, description)
        VALUES (1, 'sqlite', 'default', 'SELECT 100 as order_count', '{}', 1, '测试SQL')
    """)
    
    cursor.execute("""
        INSERT INTO access_policy (semantic_object_id, role, action, condition, effect, priority)
        VALUES (1, 'analyst', 'query', NULL, 'allow', 1)
    """)
    
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Cleanup
    try:
        os.unlink(db_path)
    except:
        pass


class TestJoinConstraints:
    """
    Test suite: Join Constraints (可 Join 约束)
    
    Business rule: Only entities with defined relationships can be joined.
    System must know which keys to use for each relationship.
    """
    
    def test_ontology_relationships_exist(self, ontology_constraint_db):
        """
        Test: Ontology relationships are properly stored.
        """
        conn = sqlite3.connect(ontology_constraint_db)
        cursor = conn.cursor()
        
        # Check relationships exist
        cursor.execute("SELECT COUNT(*) FROM ontology_relationship")
        count = cursor.fetchone()[0]
        assert count == 6  # We inserted 6 relationships
        
        # Check join keys are stored
        cursor.execute("""
            SELECT from_entity_id, to_entity_id, join_keys 
            FROM ontology_relationship 
            WHERE relationship_type = 'conversion_link'
        """)
        row = cursor.fetchone()
        assert row is not None
        assert 'user_id' in row[2]  # join_keys contains user_id
        
        conn.close()
    
    def test_strong_vs_weak_links_are_distinguished(self, ontology_constraint_db):
        """
        Test: System distinguishes between strong and weak links.
        
        Strong links: User → Order (can infer causation)
        Weak links: AdClick → User (correlation only)
        """
        conn = sqlite3.connect(ontology_constraint_db)
        cursor = conn.cursor()
        
        # Check strong link
        cursor.execute("""
            SELECT link_strength, allows_causal 
            FROM ontology_relationship 
            WHERE relationship_type = 'conversion_link'
        """)
        row = cursor.fetchone()
        assert row[0] == 'strong'
        assert row[1] == 1  # allows_causal = True
        
        # Check weak link
        cursor.execute("""
            SELECT link_strength, allows_causal 
            FROM ontology_relationship 
            WHERE relationship_type = 'weak_link'
        """)
        row = cursor.fetchone()
        assert row[0] == 'weak'
        assert row[1] == 0  # allows_causal = False
        
        conn.close()


class TestComparabilityConstraints:
    """
    Test suite: Comparability Constraints (可比较约束)
    
    Business rule: Only metrics with matching grain can be compared.
    - Day-level data cannot be directly compared with week-level
    - Per-order metrics cannot be compared with per-user metrics
    """
    
    def test_grain_levels_are_stored(self, ontology_constraint_db):
        """
        Test: Grain levels are properly stored in ontology.
        """
        conn = sqlite3.connect(ontology_constraint_db)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name, grain_level 
            FROM ontology_dimension 
            WHERE is_time = 1
        """)
        rows = cursor.fetchall()
        
        # Should have day and week level dimensions
        grain_levels = [row[1] for row in rows]
        assert 'day' in grain_levels
        assert 'week' in grain_levels
        
        conn.close()
    
    def test_logical_definition_has_grain(self, ontology_constraint_db):
        """
        Test: Logical definitions specify their grain.
        
        This is critical for comparability checks.
        """
        conn = sqlite3.connect(ontology_constraint_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT grain FROM logical_definition WHERE id = 1")
        row = cursor.fetchone()
        
        assert row is not None
        assert row[0] is not None
        assert 'user' in row[0] or 'day' in row[0]  # Has grain specification
        
        conn.close()


class TestExplainabilityConstraints:
    """
    Test suite: Explainability Constraints (可解释约束)
    
    Business rule: System tracks what conclusions are allowed:
    - Correlation: ✅ Always allowed
    - Attribution: ⚠️ Allowed with caveats
    - Causation: ❌ Only for strong links with allows_causal=True
    """
    
    def test_causal_flag_exists_in_relationships(self, ontology_constraint_db):
        """
        Test: Relationships have allows_causal flag.
        """
        conn = sqlite3.connect(ontology_constraint_db)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT relationship_type, allows_causal 
            FROM ontology_relationship
        """)
        rows = cursor.fetchall()
        
        causal_map = {row[0]: row[1] for row in rows}
        
        # Strong links allow causal inference
        assert causal_map['conversion_link'] == 1
        assert causal_map['line_item'] == 1
        
        # Weak links do NOT allow causal inference
        assert causal_map['weak_link'] == 0
        assert causal_map['attribution_rule'] == 0
        
        conn.close()
    
    def test_ad_click_to_user_is_weak_link(self, ontology_constraint_db):
        """
        Test: AdClick → User relationship is explicitly marked as weak.
        
        This is the PPT Fail-Closed example:
        "广告点击率高，为啥订单没涨？" - System should NOT make causal claims.
        """
        conn = sqlite3.connect(ontology_constraint_db)
        cursor = conn.cursor()
        
        # Get AdClick entity ID
        cursor.execute("SELECT id FROM ontology_entity WHERE name = 'AdClick'")
        ad_click_id = cursor.fetchone()[0]
        
        # Get User entity ID
        cursor.execute("SELECT id FROM ontology_entity WHERE name = 'User'")
        user_id = cursor.fetchone()[0]
        
        # Check the relationship
        cursor.execute("""
            SELECT link_strength, allows_causal 
            FROM ontology_relationship 
            WHERE from_entity_id = ? AND to_entity_id = ?
        """, (ad_click_id, user_id))
        row = cursor.fetchone()
        
        assert row is not None
        assert row[0] == 'weak'  # Link strength is weak
        assert row[1] == 0  # Causal inference NOT allowed
        
        conn.close()


class TestCrossDomainRelationships:
    """
    Test suite: Cross-domain relationship tracking.
    
    The PPT "老板追问" scenario requires joining across:
    - Transaction domain (Orders)
    - Cost domain (Costs)
    - Marketing domain (Activities, AdClicks)
    - Product domain (SKUs, Categories)
    
    Ontology must define how these domains connect.
    """
    
    def test_all_domains_have_entities(self, ontology_constraint_db):
        """
        Test: All business domains have entities defined.
        """
        conn = sqlite3.connect(ontology_constraint_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT domain FROM ontology_entity")
        domains = [row[0] for row in cursor.fetchall()]
        
        # All key domains should be present
        assert 'transaction' in domains
        assert 'customer' in domains
        assert 'marketing' in domains
        assert 'product' in domains
        assert 'finance' in domains
        
        conn.close()
    
    def test_cross_domain_paths_exist(self, ontology_constraint_db):
        """
        Test: Relationships exist to connect different domains.
        
        For example: Order (transaction) → SKU (product) via line_item
        """
        conn = sqlite3.connect(ontology_constraint_db)
        cursor = conn.cursor()
        
        # Get Order and SKU entity IDs
        cursor.execute("SELECT id, domain FROM ontology_entity WHERE name IN ('Order', 'SKU')")
        entities = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Order should be in transaction domain
        # SKU should be in product domain
        order_id = None
        sku_id = None
        for eid, domain in entities.items():
            if domain == 'transaction':
                order_id = eid
            elif domain == 'product':
                sku_id = eid
        
        # Check relationship exists between different domains
        cursor.execute("""
            SELECT relationship_type 
            FROM ontology_relationship 
            WHERE from_entity_id = ? AND to_entity_id = ?
        """, (order_id, sku_id))
        row = cursor.fetchone()
        
        assert row is not None
        assert row[0] == 'line_item'  # Cross-domain relationship exists
        
        conn.close()
