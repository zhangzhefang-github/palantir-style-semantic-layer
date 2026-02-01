"""
Minimal interfaces for storage and execution abstractions.
"""

from typing import Protocol, Optional, List, Dict, Any

from .models import (
    SemanticObject,
    SemanticVersion,
    LogicalDefinition,
    PhysicalMapping,
    AccessPolicy,
    ExecutionAudit,
    ExecutionContext,
    OntologyEntity,
    OntologyDimension,
    OntologyAttribute,
    OntologyRelationship,
    MetricEntityMap,
    MetricDependency,
    TermDictionary,
)


class MetadataStore(Protocol):
    def list_active_semantic_objects(self) -> List[SemanticObject]:
        ...

    def get_semantic_object_by_name(self, name: str) -> Optional[SemanticObject]:
        ...

    def get_semantic_object_by_id(self, obj_id: int) -> Optional[SemanticObject]:
        ...

    def get_versions_for_object(self, semantic_object_id: int) -> List[SemanticVersion]:
        ...

    def get_logical_definition(self, semantic_version_id: int) -> Optional[LogicalDefinition]:
        ...

    def get_physical_mappings(
        self,
        logical_definition_id: int,
        engine_type: Optional[str] = None
    ) -> List[PhysicalMapping]:
        ...

    def list_ontology_entities(self) -> List[OntologyEntity]:
        ...

    def list_dimensions_by_entity(self, entity_id: int) -> List[OntologyDimension]:
        ...

    def list_attributes_by_entity(self, entity_id: int) -> List[OntologyAttribute]:
        ...

    def list_relationships(self) -> List[OntologyRelationship]:
        ...

    def list_metric_entity_maps(self) -> List[MetricEntityMap]:
        ...

    def list_metric_dependencies(self) -> List[MetricDependency]:
        ...

    def find_terms_in_text(self, text: str) -> List[TermDictionary]:
        ...

    def replace_metric_dependencies_for_version(
        self,
        downstream_metric_id: int,
        downstream_version_id: int,
        dependencies: List[MetricDependency]
    ) -> None:
        ...


class PolicyStore(Protocol):
    def get_applicable_policies(
        self,
        semantic_object_id: int,
        role: str,
        action: str
    ) -> List[AccessPolicy]:
        ...

    def get_user_policies(self, role: str) -> List[Dict[str, Any]]:
        ...

    def create_policy(
        self,
        semantic_object_id: int,
        role: str,
        action: str,
        effect: str,
        condition: Optional[Dict[str, Any]] = None,
        priority: int = 0
    ) -> int:
        ...


class AuditStore(Protocol):
    def save_audit(self, audit: ExecutionAudit) -> None:
        ...

    def save_denied(
        self,
        audit_id: str,
        question: str,
        semantic_obj: Optional[SemanticObject],
        decision_trace: List[Dict[str, Any]],
        context: ExecutionContext,
        error: str
    ) -> None:
        ...

    def load_audit(self, audit_id: str) -> Optional[ExecutionAudit]:
        ...

    def list_audit_history(
        self,
        limit: int = 50,
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        ...


class QueryExecutor(Protocol):
    def execute(
        self,
        sql: str,
        connection_ref: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        ...
