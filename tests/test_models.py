"""
Unit tests for data models.
"""

import pytest
from datetime import datetime
from semantic_layer.models import (
    SemanticObject, SemanticVersion, LogicalDefinition,
    PhysicalMapping, AccessPolicy, ExecutionAudit, ExecutionContext,
    AmbiguityError, PolicyDeniedError, VersionNotFoundError, MappingNotFoundError
)


class TestSemanticObject:
    """Test SemanticObject model."""

    def test_from_db_row(self):
        """Test creating SemanticObject from database row."""
        row = (
            1,  # id
            'FPY',  # name
            'First Pass Yield',  # description
            '["FPY", "直通率"]',  # aliases (JSON)
            'production',  # domain
            'active',  # status
            '2024-01-01 00:00:00',  # created_at
            '2024-01-01 00:00:00'  # updated_at
        )

        obj = SemanticObject.from_db_row(row)

        assert obj.id == 1
        assert obj.name == 'FPY'
        assert obj.description == 'First Pass Yield'
        assert obj.aliases == ['FPY', '直通率']
        assert obj.domain == 'production'
        assert obj.status == 'active'

    def test_matches_alias_exact_name(self):
        """Test alias matching with exact name."""
        obj = SemanticObject(
            id=1,
            name='FPY',
            description='First Pass Yield',
            aliases=['FPY', '直通率', '良率'],
            domain='production'
        )

        assert obj.matches_alias('FPY') is True
        assert obj.matches_alias('fpy') is True
        assert obj.matches_alias('直通率') is True
        assert obj.matches_alias('良率') is True
        assert obj.matches_alias('产量') is False


class TestSemanticVersion:
    """Test SemanticVersion model."""

    def test_from_db_row(self):
        """Test creating SemanticVersion from database row."""
        row = (
            1,  # id
            1,  # semantic_object_id
            'FPY_v1',  # version_name
            '2024-01-01 00:00:00',  # effective_from
            None,  # effective_to
            None,  # scenario_condition
            1,  # is_active
            5,  # priority
            'Standard version',  # description
            '2024-01-01 00:00:00'  # created_at
        )

        version = SemanticVersion.from_db_row(row)

        assert version.id == 1
        assert version.semantic_object_id == 1
        assert version.version_name == 'FPY_v1'
        assert version.is_active is True
        assert version.priority == 5

    def test_is_effective_active_version(self):
        """Test effectiveness check for active version."""
        version = SemanticVersion(
            id=1,
            semantic_object_id=1,
            version_name='FPY_v1',
            effective_from=datetime(2024, 1, 1),
            effective_to=None,
            scenario_condition=None,
            is_active=True,
            description='Standard FPY version'
        )

        # Should be effective now
        assert version.is_effective(datetime(2024, 6, 1)) is True
        assert version.is_effective(datetime(2024, 1, 1)) is True

        # Should not be effective before effective_from
        assert version.is_effective(datetime(2023, 12, 31)) is False

    def test_is_effective_inactive_version(self):
        """Test effectiveness check for inactive version."""
        version = SemanticVersion(
            id=1,
            semantic_object_id=1,
            version_name='FPY_v1',
            effective_from=datetime(2024, 1, 1),
            effective_to=None,
            scenario_condition=None,
            is_active=False,  # Inactive
            description='Standard FPY version'
        )

        assert version.is_effective() is False

    def test_is_effective_with_expiry(self):
        """Test effectiveness check with expiry date."""
        version = SemanticVersion(
            id=1,
            semantic_object_id=1,
            version_name='FPY_v1',
            effective_from=datetime(2024, 1, 1),
            effective_to=datetime(2024, 6, 1),
            scenario_condition=None,
            is_active=True,
            description='Standard FPY version'
        )

        assert version.is_effective(datetime(2024, 3, 1)) is True
        assert version.is_effective(datetime(2024, 6, 2)) is False

    def test_matches_scenario_no_condition(self):
        """Test scenario matching when no condition."""
        version = SemanticVersion(
            id=1,
            semantic_object_id=1,
            version_name='FPY_v1',
            effective_from=datetime(2024, 1, 1),
            effective_to=None,
            scenario_condition=None,  # No condition
            is_active=True,
            description='Standard FPY version'
        )

        # Should match any scenario (default version)
        assert version.matches_scenario(None) is True
        assert version.matches_scenario({}) is True
        assert version.matches_scenario({'rework': True}) is True

    def test_matches_scenario_with_condition(self):
        """Test scenario matching with condition."""
        version = SemanticVersion(
            id=1,
            semantic_object_id=1,
            version_name='FPY_v2',
            effective_from=datetime(2024, 1, 1),
            effective_to=None,
            scenario_condition={'rework_enabled': True},
            is_active=True,
            description='FPY with rework calculation'
        )

        # Should match when scenario matches
        assert version.matches_scenario({'rework_enabled': True}) is True
        assert version.matches_scenario({'rework_enabled': True, 'other': 'value'}) is True

        # Should not match when scenario doesn't match
        assert version.matches_scenario({'rework_enabled': False}) is False
        assert version.matches_scenario({}) is False
        assert version.matches_scenario(None) is False


class TestLogicalDefinition:
    """Test LogicalDefinition model."""

    def test_from_db_row(self):
        """Test creating LogicalDefinition from database row."""
        row = (
            1,  # id
            1,  # semantic_version_id
            'good_qty / total_qty',  # expression
            'line,day',  # grain
            'FPY calculation',  # description
            '["good_qty", "total_qty"]',  # variables (JSON)
            '2024-01-01 00:00:00'  # created_at
        )

        logical_def = LogicalDefinition.from_db_row(row)

        assert logical_def.id == 1
        assert logical_def.expression == 'good_qty / total_qty'
        assert logical_def.grain == 'line,day'
        assert logical_def.variables == ['good_qty', 'total_qty']


class TestPhysicalMapping:
    """Test PhysicalMapping model."""

    def test_from_db_row(self):
        """Test creating PhysicalMapping from database row."""
        row = (
            1,  # id
            1,  # logical_definition_id
            'sqlite',  # engine_type
            'default',  # connection_ref
            'SELECT {{ col }} FROM table',  # sql_template
            '{"col": "string"}',  # params_schema (JSON)
            1,  # priority
            'Test mapping',  # description
            '2024-01-01 00:00:00'  # created_at
        )

        mapping = PhysicalMapping.from_db_row(row)

        assert mapping.id == 1
        assert mapping.engine_type == 'sqlite'
        assert mapping.sql_template == 'SELECT {{ col }} FROM table'
        assert mapping.params_schema == {'col': 'string'}
        assert mapping.priority == 1


class TestAccessPolicy:
    """Test AccessPolicy model."""

    def test_from_db_row(self):
        """Test creating AccessPolicy from database row."""
        row = (
            1,  # id
            1,  # semantic_object_id
            'operator',  # role
            'query',  # action
            '{"department": "production"}',  # condition (JSON)
            'allow',  # effect
            1,  # priority
            '2024-01-01 00:00:00'  # created_at
        )

        policy = AccessPolicy.from_db_row(row)

        assert policy.id == 1
        assert policy.role == 'operator'
        assert policy.action == 'query'
        assert policy.condition == {'department': 'production'}
        assert policy.effect == 'allow'
        assert policy.priority == 1


class TestExecutionContext:
    """Test ExecutionContext model."""

    def test_creation(self):
        """Test creating ExecutionContext."""
        context = ExecutionContext(
            user_id=1,
            role='operator',
            parameters={'line': 'A'},
            timestamp=datetime(2024, 1, 1, 12, 0, 0)
        )

        assert context.user_id == 1
        assert context.role == 'operator'
        assert context.parameters == {'line': 'A'}
        assert context.timestamp == datetime(2024, 1, 1, 12, 0, 0)

    def test_to_dict(self):
        """Test converting ExecutionContext to dict."""
        context = ExecutionContext(
            user_id=1,
            role='operator',
            parameters={'line': 'A'},
            timestamp=datetime(2024, 1, 1, 12, 0, 0)
        )

        result = context.to_dict()

        assert result['user_id'] == 1
        assert result['role'] == 'operator'
        assert result['parameters'] == {'line': 'A'}
        assert 'timestamp' in result


class TestExecutionAudit:
    """Test ExecutionAudit model."""

    def test_from_db_row(self):
        """Test creating ExecutionAudit from database row."""
        row = (
            1,  # id
            '20240101_120000_abc',  # audit_id
            'What is FPY?',  # question
            1,  # semantic_object_id
            'FPY',  # semantic_object_name
            1,  # version_id
            'FPY_v1',  # version_name
            1,  # logical_definition_id
            'good / total',  # logical_expression
            1,  # physical_mapping_id
            'default',  # connection_ref
            'SELECT ...',  # final_sql
            '{"steps": []}',  # decision_trace (JSON)
            '{"line": "A"}',  # request_params (JSON)
            '{"user_id": 1}',  # execution_context (JSON)
            1,  # user_id
            'operator',  # user_role
            '{"allow": true}',  # policy_decision (JSON)
            '2024-01-01 12:00:00',  # executed_at
            'success',  # status
            5,  # row_count
            10,  # execution_time_ms
            None  # error_message
        )

        audit = ExecutionAudit.from_db_row(row)

        assert audit.id == 1
        assert audit.audit_id == '20240101_120000_abc'
        assert audit.question == 'What is FPY?'
        assert audit.semantic_object_name == 'FPY'
        assert audit.status == 'success'
        assert audit.row_count == 5
        assert audit.execution_time_ms == 10

    def test_to_dict(self):
        """Test converting ExecutionAudit to dict."""
        audit = ExecutionAudit(
            id=1,
            audit_id='20240101_120000_abc',
            question='What is FPY?',
            semantic_object_id=1,
            semantic_object_name='FPY',
            version_id=1,
            version_name='FPY_v1',
            logical_definition_id=1,
            logical_expression='good / total',
            physical_mapping_id=1,
            connection_ref='default',
            final_sql='SELECT ...',
            decision_trace={'steps': []},
            request_params={'line': 'A'},
            execution_context={'user_id': 1},
            user_id=1,
            user_role='operator',
            policy_decision='{"allow": true}',
            executed_at=datetime(2024, 1, 1, 12, 0, 0),
            status='success',
            row_count=5,
            execution_time_ms=10,
            error_message=None
        )

        result = audit.to_dict()

        assert result['audit_id'] == '20240101_120000_abc'
        assert result['question'] == 'What is FPY?'
        assert result['semantic_object']['name'] == 'FPY'
        assert result['status'] == 'success'
        assert result['row_count'] == 5


class TestExceptions:
    """Test custom exceptions."""

    def test_ambiguity_error(self):
        """Test AmbiguityError exception."""
        candidates = [
            {'id': 1, 'name': 'FPY'},
            {'id': 2, 'name': 'YieldRate'}
        ]

        error = AmbiguityError(candidates, "Multiple matches")

        assert error.candidates == candidates
        assert error.type == "ambiguity"

        result = error.to_dict()
        assert result['type'] == 'ambiguity'
        assert result['candidates'] == candidates
        assert 'message' in result

    def test_policy_denied_error(self):
        """Test PolicyDeniedError exception."""
        error = PolicyDeniedError("Access denied")

        assert str(error) == "Access denied"
        assert error.reason == "Access denied"
