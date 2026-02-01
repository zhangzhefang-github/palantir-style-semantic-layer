"""
Data Models for Palantir-Style Semantic Control Plane

Defines the structure for all metadata entities in the semantic layer.
All models are decoupled from physical implementation details.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
import json


@dataclass
class SemanticObject:
    """
    Represents a business concept/metric in the semantic layer.
    This is WHAT the business cares about, not HOW it's calculated.
    """
    id: int
    name: str
    description: str
    aliases: List[str]
    domain: str
    status: str = 'active'
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_db_row(cls, row: tuple) -> 'SemanticObject':
        """Create instance from database row"""
        id, name, description, aliases_json, domain, status, created_at, updated_at = row
        return cls(
            id=id,
            name=name,
            description=description,
            aliases=json.loads(aliases_json) if aliases_json else [],
            domain=domain,
            status=status,
            created_at=datetime.fromisoformat(created_at) if created_at else None,
            updated_at=datetime.fromisoformat(updated_at) if updated_at else None
        )

    def matches_alias(self, term: str) -> bool:
        """Check if term matches name or any alias"""
        term_lower = term.lower()
        if term_lower == self.name.lower():
            return True
        return any(term_lower == alias.lower() for alias in self.aliases)

    def __repr__(self) -> str:
        return f"SemanticObject(id={self.id}, name='{self.name}', domain='{self.domain}')"


@dataclass
class OntologyEntity:
    """
    Represents an ontology entity (core business object).
    """
    id: int
    name: str
    description: Optional[str]
    domain: str
    status: str = 'active'
    created_at: Optional[datetime] = None

    @classmethod
    def from_db_row(cls, row: tuple) -> 'OntologyEntity':
        id, name, description, domain, status, created_at = row
        return cls(
            id=id,
            name=name,
            description=description,
            domain=domain,
            status=status,
            created_at=datetime.fromisoformat(created_at) if created_at else None
        )


@dataclass
class OntologyDimension:
    """
    Represents a dimension attached to an entity.
    """
    id: int
    entity_id: int
    name: str
    description: Optional[str]
    data_type: str
    status: str = 'active'
    created_at: Optional[datetime] = None

    @classmethod
    def from_db_row(cls, row: tuple) -> 'OntologyDimension':
        id, entity_id, name, description, data_type, status, created_at = row
        return cls(
            id=id,
            entity_id=entity_id,
            name=name,
            description=description,
            data_type=data_type,
            status=status,
            created_at=datetime.fromisoformat(created_at) if created_at else None
        )


@dataclass
class OntologyAttribute:
    """
    Represents an attribute attached to an entity.
    """
    id: int
    entity_id: int
    name: str
    description: Optional[str]
    data_type: str
    is_key: bool = False
    status: str = 'active'
    created_at: Optional[datetime] = None

    @classmethod
    def from_db_row(cls, row: tuple) -> 'OntologyAttribute':
        id, entity_id, name, description, data_type, is_key, status, created_at = row
        return cls(
            id=id,
            entity_id=entity_id,
            name=name,
            description=description,
            data_type=data_type,
            is_key=bool(is_key),
            status=status,
            created_at=datetime.fromisoformat(created_at) if created_at else None
        )


@dataclass
class OntologyRelationship:
    """
    Represents a relationship between entities.
    """
    id: int
    from_entity_id: int
    to_entity_id: int
    relationship_type: str
    description: Optional[str]
    cardinality: Optional[str]
    status: str = 'active'
    created_at: Optional[datetime] = None

    @classmethod
    def from_db_row(cls, row: tuple) -> 'OntologyRelationship':
        (id, from_entity_id, to_entity_id, relationship_type,
         description, cardinality, status, created_at) = row
        return cls(
            id=id,
            from_entity_id=from_entity_id,
            to_entity_id=to_entity_id,
            relationship_type=relationship_type,
            description=description,
            cardinality=cardinality,
            status=status,
            created_at=datetime.fromisoformat(created_at) if created_at else None
        )


@dataclass
class MetricEntityMap:
    """
    Explicit mapping between metric and entity, with grain constraints.
    """
    id: int
    metric_id: int
    entity_id: int
    grain_level: str
    allowed_dimensions: List[str]
    forbidden_dimensions: List[str]
    join_path_policy: Optional[str]
    created_at: Optional[datetime] = None

    @classmethod
    def from_db_row(cls, row: tuple) -> 'MetricEntityMap':
        (id, metric_id, entity_id, grain_level,
         allowed_dimensions_json, forbidden_dimensions_json,
         join_path_policy, created_at) = row
        return cls(
            id=id,
            metric_id=metric_id,
            entity_id=entity_id,
            grain_level=grain_level,
            allowed_dimensions=json.loads(allowed_dimensions_json) if allowed_dimensions_json else [],
            forbidden_dimensions=json.loads(forbidden_dimensions_json) if forbidden_dimensions_json else [],
            join_path_policy=join_path_policy,
            created_at=datetime.fromisoformat(created_at) if created_at else None
        )


@dataclass
class MetricDependency:
    """
    Metric-to-metric dependency edge.
    """
    id: int
    upstream_metric_id: int
    downstream_metric_id: int
    upstream_version_id: Optional[int]
    downstream_version_id: Optional[int]
    dependency_type: str
    description: Optional[str]
    created_at: Optional[datetime] = None

    @classmethod
    def from_db_row(cls, row: tuple) -> 'MetricDependency':
        (id, upstream_metric_id, downstream_metric_id,
         upstream_version_id, downstream_version_id,
         dependency_type, description, created_at) = row
        return cls(
            id=id,
            upstream_metric_id=upstream_metric_id,
            downstream_metric_id=downstream_metric_id,
            upstream_version_id=upstream_version_id,
            downstream_version_id=downstream_version_id,
            dependency_type=dependency_type,
            description=description,
            created_at=datetime.fromisoformat(created_at) if created_at else None
        )


@dataclass
class TermDictionary:
    """
    Lightweight term dictionary for normalization.
    """
    id: int
    term: str
    normalized_term: str
    object_type: str
    object_id: int
    language: str
    status: str
    created_at: Optional[datetime] = None

    @classmethod
    def from_db_row(cls, row: tuple) -> 'TermDictionary':
        (id, term, normalized_term, object_type,
         object_id, language, status, created_at) = row
        return cls(
            id=id,
            term=term,
            normalized_term=normalized_term,
            object_type=object_type,
            object_id=object_id,
            language=language,
            status=status,
            created_at=datetime.fromisoformat(created_at) if created_at else None
        )


@dataclass
class SemanticVersion:
    """
    Represents a version of a semantic object's definition.
    Handles temporal and scenario-based variations.
    """
    id: int
    semantic_object_id: int
    version_name: str
    effective_from: datetime
    effective_to: Optional[datetime]
    scenario_condition: Optional[Dict[str, Any]]
    is_active: bool
    priority: int = 0  # For conflict resolution: higher priority wins when scores are equal
    description: Optional[str] = None
    created_at: Optional[datetime] = None

    @classmethod
    def from_db_row(cls, row: tuple) -> 'SemanticVersion':
        """Create instance from database row"""
        (id, semantic_object_id, version_name, effective_from, effective_to,
         scenario_json, is_active, priority, description, created_at) = row
        return cls(
            id=id,
            semantic_object_id=semantic_object_id,
            version_name=version_name,
            effective_from=datetime.fromisoformat(effective_from),
            effective_to=datetime.fromisoformat(effective_to) if effective_to else None,
            scenario_condition=json.loads(scenario_json) if scenario_json else None,
            is_active=bool(is_active),
            priority=priority,
            description=description,
            created_at=datetime.fromisoformat(created_at) if created_at else None
        )

    def is_effective(self, timestamp: Optional[datetime] = None) -> bool:
        """Check if this version is effective at given timestamp"""
        if not self.is_active:
            return False

        ts = timestamp or datetime.now()
        if ts < self.effective_from:
            return False
        if self.effective_to and ts > self.effective_to:
            return False
        return True

    def matches_scenario(self, scenario: Optional[Dict[str, Any]]) -> bool:
        """Check if this version matches the given scenario conditions"""
        if not self.scenario_condition:
            # No condition means this is the default version
            return True

        if not scenario:
            # If there's a condition but no scenario provided, don't match
            return False

        # Simple matching: all key-value pairs in condition must match scenario
        for key, value in self.scenario_condition.items():
            if scenario.get(key) != value:
                return False
        return True

    def __repr__(self) -> str:
        return f"SemanticVersion(id={self.id}, name='{self.version_name}', active={self.is_active})"


@dataclass
class LogicalDefinition:
    """
    Pure business logic formula.
    Contains NO physical implementation details (no table names, no SQL).
    """
    id: int
    semantic_version_id: int
    expression: str
    grain: Optional[str]
    description: Optional[str]
    variables: List[str]
    created_at: Optional[datetime] = None

    @classmethod
    def from_db_row(cls, row: tuple) -> 'LogicalDefinition':
        """Create instance from database row"""
        id, semantic_version_id, expression, grain, description, variables_json, created_at = row
        return cls(
            id=id,
            semantic_version_id=semantic_version_id,
            expression=expression,
            grain=grain,
            description=description,
            variables=json.loads(variables_json) if variables_json else [],
            created_at=datetime.fromisoformat(created_at) if created_at else None
        )

    def __repr__(self) -> str:
        return f"LogicalDefinition(id={self.id}, expression='{self.expression}', grain='{self.grain}')"


@dataclass
class PhysicalMapping:
    """
    Maps logical definition to actual SQL implementation.
    This is WHERE and HOW the calculation happens physically.
    """
    id: int
    logical_definition_id: int
    engine_type: str
    connection_ref: str
    sql_template: str
    params_schema: Dict[str, str]
    priority: int
    description: Optional[str]
    created_at: Optional[datetime] = None

    @classmethod
    def from_db_row(cls, row: tuple) -> 'PhysicalMapping':
        """Create instance from database row"""
        (id, logical_definition_id, engine_type, connection_ref,
         sql_template, params_schema_json, priority, description, created_at) = row
        return cls(
            id=id,
            logical_definition_id=logical_definition_id,
            engine_type=engine_type,
            connection_ref=connection_ref,
            sql_template=sql_template,
            params_schema=json.loads(params_schema_json) if params_schema_json else {},
            priority=priority,
            description=description,
            created_at=datetime.fromisoformat(created_at) if created_at else None
        )

    def __repr__(self) -> str:
        return f"PhysicalMapping(id={self.id}, engine='{self.engine_type}', priority={self.priority})"


@dataclass
class AccessPolicy:
    """
    Authorization policy for semantic object access.
    Defines WHO can do WHAT.
    """
    id: int
    semantic_object_id: int
    role: str
    action: str
    condition: Optional[Dict[str, Any]]
    effect: str  # 'allow' or 'deny'
    priority: int
    created_at: Optional[datetime] = None

    @classmethod
    def from_db_row(cls, row: tuple) -> 'AccessPolicy':
        """Create instance from database row"""
        (id, semantic_object_id, role, action, condition_json,
         effect, priority, created_at) = row
        return cls(
            id=id,
            semantic_object_id=semantic_object_id,
            role=role,
            action=action,
            condition=json.loads(condition_json) if condition_json else None,
            effect=effect,
            priority=priority,
            created_at=datetime.fromisoformat(created_at) if created_at else None
        )

    def __repr__(self) -> str:
        return f"AccessPolicy(id={self.id}, role='{self.role}', effect='{self.effect}')"


@dataclass
class ExecutionAudit:
    """
    Complete audit trail for semantic query execution.
    Records every decision for traceability and replayability.
    """
    id: int
    audit_id: str
    question: str

    # Semantic resolution
    semantic_object_id: Optional[int]
    semantic_object_name: Optional[str]
    version_id: Optional[int]
    version_name: Optional[str]

    # Logic resolution
    logical_definition_id: Optional[int]
    logical_expression: Optional[str]

    # Physical mapping
    physical_mapping_id: Optional[int]
    connection_ref: Optional[str]

    # Execution
    final_sql: Optional[str]
    decision_trace: Dict[str, Any]
    request_params: Optional[Dict[str, Any]]
    execution_context: Optional[Dict[str, Any]]
    user_id: Optional[int]
    user_role: Optional[str]
    policy_decision: Optional[str]
    executed_at: Optional[datetime]
    status: str
    row_count: Optional[int]
    execution_time_ms: Optional[int]
    error_message: Optional[str]

    @classmethod
    def from_db_row(cls, row: tuple) -> 'ExecutionAudit':
        """Create instance from database row"""
        (
            id, audit_id, question,
            semantic_object_id, semantic_object_name,
            version_id, version_name,
            logical_definition_id, logical_expression,
            physical_mapping_id, connection_ref,
            final_sql, decision_trace_json,
            request_params_json, execution_context_json,
            user_id, user_role, policy_decision,
            executed_at, status, row_count, execution_time_ms, error_message
        ) = row

        return cls(
            id=id,
            audit_id=audit_id,
            question=question,
            semantic_object_id=semantic_object_id,
            semantic_object_name=semantic_object_name,
            version_id=version_id,
            version_name=version_name,
            logical_definition_id=logical_definition_id,
            logical_expression=logical_expression,
            physical_mapping_id=physical_mapping_id,
            connection_ref=connection_ref,
            final_sql=final_sql,
            decision_trace=json.loads(decision_trace_json) if decision_trace_json else {},
            request_params=json.loads(request_params_json) if request_params_json else None,
            execution_context=json.loads(execution_context_json) if execution_context_json else None,
            user_id=user_id,
            user_role=user_role,
            policy_decision=policy_decision,
            executed_at=datetime.fromisoformat(executed_at) if executed_at else None,
            status=status,
            row_count=row_count,
            execution_time_ms=execution_time_ms,
            error_message=error_message
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'audit_id': self.audit_id,
            'question': self.question,
            'semantic_object': {
                'id': self.semantic_object_id,
                'name': self.semantic_object_name
            },
            'version': {
                'id': self.version_id,
                'name': self.version_name
            },
            'logical_definition': {
                'id': self.logical_definition_id,
                'expression': self.logical_expression
            },
            'physical_mapping': {
                'id': self.physical_mapping_id,
                'connection_ref': self.connection_ref
            },
            'final_sql': self.final_sql,
            'decision_trace': self.decision_trace,
            'request_params': self.request_params,
            'execution_context': self.execution_context,
            'user': {
                'id': self.user_id,
                'role': self.user_role
            },
            'policy_decision': self.policy_decision,
            'executed_at': self.executed_at.isoformat() if self.executed_at else None,
            'status': self.status,
            'row_count': self.row_count,
            'execution_time_ms': self.execution_time_ms,
            'error_message': self.error_message
        }

    def __repr__(self) -> str:
        return f"ExecutionAudit(audit_id='{self.audit_id}', status='{self.status}')"


@dataclass
class ExecutionContext:
    """
    Execution context for a semantic query.
    Contains user info, parameters, and temporal context.
    """
    user_id: int
    role: str
    parameters: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'user_id': self.user_id,
            'role': self.role,
            'parameters': self.parameters,
            'timestamp': self.timestamp.isoformat()
        }


# ============================================================
# CUSTOM EXCEPTIONS
# ============================================================

class SemanticError(Exception):
    """Base exception for semantic layer errors"""
    pass


class AmbiguityError(SemanticError):
    """Raised when multiple semantic objects match and clarification is needed"""

    def __init__(self, candidates: List[Dict[str, Any]], message: str = "Multiple semantic objects matched. Please clarify."):
        self.candidates = candidates
        self.type = "ambiguity"
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "candidates": self.candidates,
            "message": str(self)
        }


class PolicyDeniedError(SemanticError):
    """Raised when access policy denies execution"""

    def __init__(self, reason: str = "Access denied by policy"):
        self.reason = reason
        super().__init__(reason)


class VersionNotFoundError(SemanticError):
    """Raised when no active version is found for a semantic object"""
    pass


class MappingNotFoundError(SemanticError):
    """Raised when no physical mapping exists for a logical definition"""
    pass
