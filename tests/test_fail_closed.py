"""
Fail-Closed Tests

This test suite demonstrates the PPT Fail-Closed scenario:
- User asks: "广告点击率高，为啥订单没涨？给我结论。"
- System should:
  ✅ Allow: Comparative analysis (show data side by side)
  🚫 Deny: Causal conclusions ("广告无效", "投放失败")
  
The key insight: Ontology constrains what the system CAN and CANNOT say.
Not for intelligence, but for NOT making mistakes.
"""

import pytest
import sqlite3
from datetime import datetime
from pathlib import Path
import tempfile
import os
import json


@pytest.fixture
def fail_closed_db():
    """
    Create a test database for fail-closed scenarios.
    
    Setup:
    - AdClick entity with metrics
    - Order entity with metrics
    - Weak link between AdClick → User → Order
    - Strong link for User → Order (conversion)
    """
    db_path = tempfile.mktemp(suffix='.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create schema
    schema_path = Path(__file__).parent.parent / 'schema.sql'
    with open(schema_path, 'r') as f:
        conn.executescript(f.read())
    
    # ============================================================
    # 1. Insert Entities
    # ============================================================
    
    cursor.execute("""
        INSERT INTO ontology_entity (name, domain, entity_type, description)
        VALUES ('AdClick', 'marketing', 'fact', '广告点击事件')
    """)  # ID: 1
    
    cursor.execute("""
        INSERT INTO ontology_entity (name, domain, entity_type, description)
        VALUES ('User', 'customer', 'dimension', '用户')
    """)  # ID: 2
    
    cursor.execute("""
        INSERT INTO ontology_entity (name, domain, entity_type, description)
        VALUES ('Order', 'transaction', 'fact', '订单')
    """)  # ID: 3
    
    # ============================================================
    # 2. Insert Relationships with Causal Flags
    # ============================================================
    
    # WEAK LINK: AdClick → User (correlation only, NO causation)
    cursor.execute("""
        INSERT INTO ontology_relationship 
        (from_entity_id, to_entity_id, relationship_type, cardinality, join_keys, link_strength, allows_causal)
        VALUES (1, 2, 'click_attribution', 'many_to_one', '["user_id"]', 'weak', 0)
    """)
    
    # STRONG LINK: User → Order (causation allowed)
    cursor.execute("""
        INSERT INTO ontology_relationship 
        (from_entity_id, to_entity_id, relationship_type, cardinality, join_keys, link_strength, allows_causal)
        VALUES (2, 3, 'conversion', 'one_to_many', '["user_id"]', 'strong', 1)
    """)
    
    # ============================================================
    # 3. Insert Semantic Objects for Ad Metrics
    # ============================================================
    
    # Click Rate metric
    cursor.execute("""
        INSERT INTO semantic_object (name, description, aliases, domain, status)
        VALUES ('ClickRate', '广告点击率', '["点击率", "CTR"]', 'marketing', 'active')
    """)
    
    cursor.execute("""
        INSERT INTO semantic_version
        (semantic_object_id, version_name, effective_from, scenario_condition, is_active, priority, description)
        VALUES (1, 'ClickRate_v1', '2024-01-01 00:00:00', NULL, 1, 0, '标准点击率')
    """)
    
    cursor.execute("""
        INSERT INTO logical_definition (semantic_version_id, expression, grain, description, variables)
        VALUES (1, 'clicks / impressions', 'campaign,day', '点击数/展示数', '["clicks", "impressions"]')
    """)
    
    cursor.execute("""
        INSERT INTO physical_mapping 
        (logical_definition_id, engine_type, connection_ref, sql_template, params_schema, priority, description)
        VALUES (1, 'sqlite', 'default', 'SELECT 0.052 as click_rate', '{}', 1, '点击率5.2%')
    """)
    
    # Order Count metric
    cursor.execute("""
        INSERT INTO semantic_object (name, description, aliases, domain, status)
        VALUES ('OrderCount', '订单数量', '["订单数", "订单量"]', 'transaction', 'active')
    """)
    
    cursor.execute("""
        INSERT INTO semantic_version
        (semantic_object_id, version_name, effective_from, scenario_condition, is_active, priority, description)
        VALUES (2, 'OrderCount_v1', '2024-01-01 00:00:00', NULL, 1, 0, '标准订单计数')
    """)
    
    cursor.execute("""
        INSERT INTO logical_definition (semantic_version_id, expression, grain, description, variables)
        VALUES (2, 'COUNT(order_id)', 'day', '每日订单数', '["order_id"]')
    """)
    
    cursor.execute("""
        INSERT INTO physical_mapping 
        (logical_definition_id, engine_type, connection_ref, sql_template, params_schema, priority, description)
        VALUES (2, 'sqlite', 'default', 'SELECT 1234 as order_count', '{}', 1, '订单数1234')
    """)
    
    # ============================================================
    # 4. Insert Access Policies
    # ============================================================
    
    cursor.execute("""
        INSERT INTO access_policy (semantic_object_id, role, action, condition, effect, priority)
        VALUES (1, 'analyst', 'query', NULL, 'allow', 1)
    """)
    
    cursor.execute("""
        INSERT INTO access_policy (semantic_object_id, role, action, condition, effect, priority)
        VALUES (2, 'analyst', 'query', NULL, 'allow', 1)
    """)
    
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Cleanup
    try:
        os.unlink(db_path)
    except:
        pass


class TestFailClosedConcept:
    """
    Test suite: Fail-Closed concept validation.
    
    The core principle:
    - System REFUSES to make claims it cannot support
    - Better to say "I cannot conclude X" than to guess wrong
    """
    
    def test_weak_link_is_properly_marked(self, fail_closed_db):
        """
        Test: AdClick → User relationship is marked as weak.
        
        This is the foundation of fail-closed:
        The relationship metadata tells the system what NOT to conclude.
        """
        conn = sqlite3.connect(fail_closed_db)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT link_strength, allows_causal 
            FROM ontology_relationship 
            WHERE relationship_type = 'click_attribution'
        """)
        row = cursor.fetchone()
        
        assert row is not None
        assert row[0] == 'weak'  # Marked as weak link
        assert row[1] == 0  # Causal inference NOT allowed
        
        conn.close()
    
    def test_strong_link_allows_causal(self, fail_closed_db):
        """
        Test: User → Order relationship allows causal inference.
        
        We CAN say: "Users who visited converted at X rate"
        Because conversion_link has allows_causal=True
        """
        conn = sqlite3.connect(fail_closed_db)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT link_strength, allows_causal 
            FROM ontology_relationship 
            WHERE relationship_type = 'conversion'
        """)
        row = cursor.fetchone()
        
        assert row is not None
        assert row[0] == 'strong'
        assert row[1] == 1  # Causal inference IS allowed
        
        conn.close()


class TestCausalConstraintEnforcement:
    """
    Test suite: Causal constraint enforcement.
    
    These tests verify that the system has the DATA to enforce constraints.
    The actual enforcement would happen in the application layer.
    """
    
    def test_can_query_link_strength_for_any_path(self, fail_closed_db):
        """
        Test: System can determine link strength for any entity path.
        
        Before making a claim like "Ad caused Order", system should:
        1. Find path: AdClick → User → Order
        2. Check: Is the weakest link strong enough?
        3. Result: No, because AdClick → User is weak
        """
        conn = sqlite3.connect(fail_closed_db)
        cursor = conn.cursor()
        
        # Find all relationships in the AdClick → User → Order path
        cursor.execute("""
            SELECT r.from_entity_id, r.to_entity_id, r.link_strength, r.allows_causal,
                   e1.name as from_name, e2.name as to_name
            FROM ontology_relationship r
            JOIN ontology_entity e1 ON r.from_entity_id = e1.id
            JOIN ontology_entity e2 ON r.to_entity_id = e2.id
        """)
        relationships = cursor.fetchall()
        
        # Build a map for easier analysis
        path_info = {}
        for row in relationships:
            key = f"{row[4]} → {row[5]}"
            path_info[key] = {
                'link_strength': row[2],
                'allows_causal': row[3]
            }
        
        # AdClick → User should be weak
        assert path_info['AdClick → User']['link_strength'] == 'weak'
        assert path_info['AdClick → User']['allows_causal'] == 0
        
        # User → Order should be strong
        assert path_info['User → Order']['link_strength'] == 'strong'
        assert path_info['User → Order']['allows_causal'] == 1
        
        conn.close()
    
    def test_causal_chain_is_only_as_strong_as_weakest_link(self, fail_closed_db):
        """
        Test: A causal chain's validity depends on its weakest link.
        
        Path: AdClick → User → Order
        - AdClick → User: weak (allows_causal=0)
        - User → Order: strong (allows_causal=1)
        
        Conclusion: Cannot make causal claims about AdClick → Order
        """
        conn = sqlite3.connect(fail_closed_db)
        cursor = conn.cursor()
        
        # Get all links in the path
        cursor.execute("""
            SELECT MIN(allows_causal) as chain_allows_causal
            FROM ontology_relationship
            WHERE (from_entity_id = 1 AND to_entity_id = 2)  -- AdClick → User
               OR (from_entity_id = 2 AND to_entity_id = 3)  -- User → Order
        """)
        result = cursor.fetchone()
        
        # The chain's causal permission is the MIN of all links
        # If ANY link disallows causation, the whole chain does
        assert result[0] == 0  # Chain does NOT allow causal inference
        
        conn.close()


class TestAllowedVsDeniedConclusions:
    """
    Test suite: What conclusions ARE and ARE NOT allowed.
    
    PPT Example:
    Q: "广告点击率高，为啥订单没涨？给我结论。"
    
    ✅ Allowed: "Click rate increased 5.2%. Order count remained at 1,234."
    🚫 Denied: "Advertising is ineffective" (causal conclusion)
    """
    
    def test_correlation_analysis_data_is_available(self, fail_closed_db):
        """
        Test: Data for correlation analysis is available.
        
        We CAN show: Click rate = 5.2%, Orders = 1,234
        (Side-by-side comparison, no causal claims)
        """
        conn = sqlite3.connect(fail_closed_db)
        cursor = conn.cursor()
        
        # Check ClickRate metric exists
        cursor.execute("""
            SELECT pm.sql_template 
            FROM physical_mapping pm
            JOIN logical_definition ld ON pm.logical_definition_id = ld.id
            JOIN semantic_version sv ON ld.semantic_version_id = sv.id
            JOIN semantic_object so ON sv.semantic_object_id = so.id
            WHERE so.name = 'ClickRate'
        """)
        row = cursor.fetchone()
        assert row is not None
        assert '0.052' in row[0]  # 5.2% click rate
        
        # Check OrderCount metric exists
        cursor.execute("""
            SELECT pm.sql_template 
            FROM physical_mapping pm
            JOIN logical_definition ld ON pm.logical_definition_id = ld.id
            JOIN semantic_version sv ON ld.semantic_version_id = sv.id
            JOIN semantic_object so ON sv.semantic_object_id = so.id
            WHERE so.name = 'OrderCount'
        """)
        row = cursor.fetchone()
        assert row is not None
        assert '1234' in row[0]  # 1,234 orders
        
        conn.close()
    
    def test_causal_constraint_metadata_exists(self, fail_closed_db):
        """
        Test: Metadata for causal constraints exists.
        
        Before making a claim, system can check:
        1. Is there a relationship between these entities?
        2. What is the link_strength?
        3. Does allows_causal = True?
        """
        conn = sqlite3.connect(fail_closed_db)
        cursor = conn.cursor()
        
        # Query that would be used to check if causal claims are allowed
        cursor.execute("""
            SELECT 
                e1.name as from_entity,
                e2.name as to_entity,
                r.relationship_type,
                r.link_strength,
                CASE 
                    WHEN r.allows_causal = 1 THEN 'Causal claims ALLOWED'
                    ELSE 'Causal claims DENIED - correlation only'
                END as causal_permission
            FROM ontology_relationship r
            JOIN ontology_entity e1 ON r.from_entity_id = e1.id
            JOIN ontology_entity e2 ON r.to_entity_id = e2.id
            WHERE e1.name = 'AdClick' AND e2.name = 'User'
        """)
        row = cursor.fetchone()
        
        assert row is not None
        assert row[0] == 'AdClick'
        assert row[1] == 'User'
        assert row[3] == 'weak'
        assert 'DENIED' in row[4]  # Causal claims denied
        
        conn.close()


class TestFailClosedDocumentation:
    """
    Test suite: Fail-closed behavior is documented and auditable.
    
    When system refuses to make a causal claim, it should explain why.
    """
    
    def test_weak_link_has_description(self, fail_closed_db):
        """
        Test: Weak links have explanatory descriptions.
        """
        conn = sqlite3.connect(fail_closed_db)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT relationship_type, link_strength
            FROM ontology_relationship 
            WHERE link_strength = 'weak'
        """)
        rows = cursor.fetchall()
        
        assert len(rows) > 0
        # Each weak link should be identifiable
        for row in rows:
            assert row[0] is not None  # Has a relationship type
            assert row[1] == 'weak'
        
        conn.close()
    
    def test_entity_domains_are_documented(self, fail_closed_db):
        """
        Test: Entities have domain classifications.
        
        This helps explain WHY certain links are weak:
        "AdClick (marketing) → User (customer) is weak because
        marketing impressions don't guarantee customer intent."
        """
        conn = sqlite3.connect(fail_closed_db)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name, domain, description 
            FROM ontology_entity
        """)
        rows = cursor.fetchall()
        
        entities = {row[0]: {'domain': row[1], 'description': row[2]} for row in rows}
        
        assert entities['AdClick']['domain'] == 'marketing'
        assert entities['User']['domain'] == 'customer'
        assert entities['Order']['domain'] == 'transaction'
        
        conn.close()


class TestFailClosedValueProposition:
    """
    Test suite: Demonstrate the VALUE of fail-closed behavior.
    
    Enterprise concern: "AI systems will make things up"
    Our answer: "No, our system refuses to make unsupported claims"
    """
    
    def test_system_has_all_constraints_needed_for_fail_closed(self, fail_closed_db):
        """
        Test: All necessary constraint data exists for fail-closed behavior.
        
        Required data:
        1. Entity definitions with domains
        2. Relationships with link_strength
        3. allows_causal flags
        4. Metrics with proper entity mappings
        """
        conn = sqlite3.connect(fail_closed_db)
        cursor = conn.cursor()
        
        # 1. Entities exist
        cursor.execute("SELECT COUNT(*) FROM ontology_entity")
        assert cursor.fetchone()[0] >= 3
        
        # 2. Relationships with link_strength
        cursor.execute("SELECT COUNT(*) FROM ontology_relationship WHERE link_strength IS NOT NULL")
        assert cursor.fetchone()[0] >= 2
        
        # 3. allows_causal flags are set
        cursor.execute("SELECT COUNT(*) FROM ontology_relationship WHERE allows_causal IS NOT NULL")
        assert cursor.fetchone()[0] >= 2
        
        # 4. Metrics exist
        cursor.execute("SELECT COUNT(*) FROM semantic_object")
        assert cursor.fetchone()[0] >= 2
        
        conn.close()
    
    def test_fail_closed_protects_against_false_conclusions(self, fail_closed_db):
        """
        Test: The constraint system can identify when a conclusion would be unsafe.
        
        Scenario: User wants to conclude "Ads don't work"
        System should identify:
        - This requires AdClick → Order causal claim
        - Path: AdClick → User → Order
        - AdClick → User is weak_link
        - Conclusion: CANNOT make this causal claim
        """
        conn = sqlite3.connect(fail_closed_db)
        cursor = conn.cursor()
        
        # Simulate checking if we can make a causal claim from AdClick to Order
        cursor.execute("""
            WITH RECURSIVE path_check AS (
                -- Start from AdClick (entity_id = 1)
                SELECT 
                    from_entity_id,
                    to_entity_id,
                    link_strength,
                    allows_causal,
                    1 as depth
                FROM ontology_relationship
                WHERE from_entity_id = 1  -- AdClick
                
                UNION ALL
                
                -- Follow the path
                SELECT 
                    r.from_entity_id,
                    r.to_entity_id,
                    r.link_strength,
                    r.allows_causal,
                    pc.depth + 1
                FROM ontology_relationship r
                JOIN path_check pc ON r.from_entity_id = pc.to_entity_id
                WHERE pc.depth < 3
            )
            SELECT 
                MIN(allows_causal) as can_make_causal_claim,
                GROUP_CONCAT(link_strength) as path_strengths
            FROM path_check
        """)
        result = cursor.fetchone()
        
        # The path includes a weak link, so causal claims are NOT allowed
        assert result[0] == 0  # can_make_causal_claim = False
        assert 'weak' in result[1]  # Path includes weak link
        
        conn.close()
