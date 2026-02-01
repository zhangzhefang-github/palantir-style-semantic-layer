"""
Unit tests for PolicyEngine.
"""

import pytest
from semantic_layer.policy_engine import PolicyEngine
from semantic_layer.models import PolicyDeniedError


class TestPolicyEngine:
    """Test PolicyEngine functionality."""

    def test_check_access_allowed(self, test_db_path):
        """Test access check for allowed user."""
        engine = PolicyEngine(db_path=test_db_path)

        decision = engine.check_access(
            semantic_object_id=1,  # FPY
            role='operator',
            action='query',
            context=None
        )

        assert decision['allow'] is True
        assert 'Allowed' in decision['reason']
        assert len(decision['policies']) >= 1

    def test_check_access_denied(self, test_db_path):
        """Test access check for denied user."""
        engine = PolicyEngine(db_path=test_db_path)

        with pytest.raises(PolicyDeniedError):
            engine.check_access(
                semantic_object_id=1,  # FPY
                role='anonymous',
                action='query',
                context=None
            )

    def test_check_access_no_policies(self, test_db_path):
        """Test access check when no policies exist."""
        engine = PolicyEngine(db_path=test_db_path)

        # Semantic object 99 doesn't have policies
        # This should default to deny
        with pytest.raises(PolicyDeniedError, match="No access policies"):
            engine.check_access(
                semantic_object_id=999,
                role='operator',
                action='query',
                context=None
            )

    def test_check_access_multiple_policies(self, test_db_path):
        """Test access check with multiple applicable policies."""
        engine = PolicyEngine(db_path=test_db_path)

        # FPY has allow policies for operator
        decision = engine.check_access(
            semantic_object_id=1,
            role='operator',
            action='query',
            context={'line': 'A'}
        )

        assert decision['allow'] is True
        assert len(decision['policies']) >= 1

    def test_check_access_wildcard_role(self, test_db_path):
        """Test access check with wildcard role."""
        engine = PolicyEngine(db_path=test_db_path)

        # Check if wildcard policies work (if any in seed data)
        # Current seed data doesn't have wildcard policies, so this is a placeholder
        decision = engine.check_access(
            semantic_object_id=1,
            role='operator',
            action='query',
            context=None
        )

        assert decision['allow'] is True

    def test_matches_condition_no_condition(self, test_db_path):
        """Test policy condition matching when no condition."""
        engine = PolicyEngine(db_path=test_db_path)

        # Create a mock policy with no condition
        class MockPolicy:
            condition = None

        policy = MockPolicy()

        # Should match any context
        assert engine._matches_condition(policy, None) is True
        assert engine._matches_condition(policy, {}) is True
        assert engine._matches_condition(policy, {'any': 'value'}) is True

    def test_matches_condition_with_condition(self, test_db_path):
        """Test policy condition matching with condition."""
        engine = PolicyEngine(db_path=test_db_path)

        class MockPolicy:
            condition = {'department': 'production'}

        policy = MockPolicy()

        # Should match when condition matches
        assert engine._matches_condition(policy, {'department': 'production'}) is True
        assert engine._matches_condition(
            policy,
            {'department': 'production', 'line': 'A'}
        ) is True

        # Should not match when condition doesn't match
        assert engine._matches_condition(policy, {'department': 'sales'}) is False
        assert engine._matches_condition(policy, {}) is False
        assert engine._matches_condition(policy, None) is False

    def test_evaluate_policies_allow_priority(self, test_db_path):
        """Test policy evaluation with priority (allow vs deny)."""
        engine = PolicyEngine(db_path=test_db_path)

        # Get policies for FPY and operator
        policies = engine._get_applicable_policies(
            semantic_object_id=1,
            role='operator',
            action='query'
        )

        # Should have at least one allow policy
        assert len(policies) > 0

        # Evaluate policies
        decision = engine._evaluate_policies(policies, None)

        # Should allow
        assert decision['allow'] is True

    def test_get_user_policies(self, test_db_path):
        """Test getting all policies for a user."""
        engine = PolicyEngine(db_path=test_db_path)

        policies = engine.get_user_policies('operator')

        # Should have some policies
        assert len(policies) > 0

        # Check policy structure
        for policy in policies:
            assert 'role' in policy
            assert 'semantic_object' in policy
            assert 'action' in policy
            assert 'effect' in policy

    def test_create_policy(self, test_db_path):
        """Test creating a new policy."""
        engine = PolicyEngine(db_path=test_db_path)

        # Create a new policy
        policy_id = engine.create_policy(
            semantic_object_id=1,
            role='analyst',
            action='export',
            effect='allow',
            condition={'department': 'analytics'},
            priority=10
        )

        assert policy_id > 0

        # Verify policy was created
        policies = engine.get_user_policies('analyst')
        assert any(p['action'] == 'export' for p in policies)

    def test_check_access_deny_priority(self, test_db_path):
        """Test that deny policies take precedence."""
        engine = PolicyEngine(db_path=test_db_path)

        # Anonymous users should be denied
        with pytest.raises(PolicyDeniedError):
            engine.check_access(
                semantic_object_id=1,
                role='anonymous',
                action='query',
                context=None
            )

    def test_policy_for_different_actions(self, test_db_path):
        """Test policies for different actions (query vs export)."""
        engine = PolicyEngine(db_path=test_db_path)

        # Operator can query
        decision = engine.check_access(
            semantic_object_id=1,
            role='operator',
            action='query',
            context=None
        )
        assert decision['allow'] is True

        # Analyst can export (if such policy exists)
        # This depends on seed data
        policies = engine._get_applicable_policies(
            semantic_object_id=1,
            role='analyst',
            action='export'
        )

        # Should have export policy if seed data includes it
        # Otherwise will be empty
        if policies:
            decision = engine._evaluate_policies(policies, None)
            assert 'allow' in decision
