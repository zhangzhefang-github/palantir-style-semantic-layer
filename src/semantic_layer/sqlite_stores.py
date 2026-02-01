"""
SQLite implementations for storage and execution interfaces.
"""

import json
import sqlite3
from typing import Optional, List, Dict, Any

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


class SQLiteMetadataStore:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def list_active_semantic_objects(self) -> List[SemanticObject]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, description, aliases, domain, status, created_at, updated_at
            FROM semantic_object
            WHERE status = 'active'
        """)
        objects = [SemanticObject.from_db_row(tuple(row)) for row in cursor.fetchall()]
        conn.close()
        return objects

    def get_semantic_object_by_id(self, obj_id: int) -> Optional[SemanticObject]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, description, aliases, domain, status, created_at, updated_at
            FROM semantic_object
            WHERE id = ?
        """, (obj_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return SemanticObject.from_db_row(tuple(row))
        return None

    def get_semantic_object_by_name(self, name: str) -> Optional[SemanticObject]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, description, aliases, domain, status, created_at, updated_at
            FROM semantic_object
            WHERE name = ?
        """, (name,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return SemanticObject.from_db_row(tuple(row))
        return None

    def get_versions_for_object(self, semantic_object_id: int) -> List[SemanticVersion]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, semantic_object_id, version_name, effective_from, effective_to,
                   scenario_condition, is_active, priority, description, created_at
            FROM semantic_version
            WHERE semantic_object_id = ?
            ORDER BY effective_from DESC
        """, (semantic_object_id,))
        versions = [SemanticVersion.from_db_row(tuple(row)) for row in cursor.fetchall()]
        conn.close()
        return versions

    def get_logical_definition(self, semantic_version_id: int) -> Optional[LogicalDefinition]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, semantic_version_id, expression, grain, description, variables, created_at
            FROM logical_definition
            WHERE semantic_version_id = ?
        """, (semantic_version_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return LogicalDefinition.from_db_row(tuple(row))
        return None

    def get_physical_mappings(
        self,
        logical_definition_id: int,
        engine_type: Optional[str] = None
    ) -> List[PhysicalMapping]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = """
            SELECT id, logical_definition_id, engine_type, connection_ref,
                   sql_template, params_schema, priority, description, created_at
            FROM physical_mapping
            WHERE logical_definition_id = ?
        """
        params = [logical_definition_id]
        if engine_type:
            query += " AND engine_type = ?"
            params.append(engine_type)
        query += " ORDER BY priority DESC"

        cursor.execute(query, params)
        mappings = [PhysicalMapping.from_db_row(tuple(row)) for row in cursor.fetchall()]
        conn.close()
        return mappings

    def list_ontology_entities(self) -> List[OntologyEntity]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, description, domain, status, created_at
            FROM ontology_entity
            WHERE status = 'active'
        """)
        entities = [OntologyEntity.from_db_row(tuple(row)) for row in cursor.fetchall()]
        conn.close()
        return entities

    def list_dimensions_by_entity(self, entity_id: int) -> List[OntologyDimension]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, entity_id, name, description, data_type, status, created_at
            FROM ontology_dimension
            WHERE entity_id = ? AND status = 'active'
        """, (entity_id,))
        dims = [OntologyDimension.from_db_row(tuple(row)) for row in cursor.fetchall()]
        conn.close()
        return dims

    def list_attributes_by_entity(self, entity_id: int) -> List[OntologyAttribute]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, entity_id, name, description, data_type, is_key, status, created_at
            FROM ontology_attribute
            WHERE entity_id = ? AND status = 'active'
        """, (entity_id,))
        attrs = [OntologyAttribute.from_db_row(tuple(row)) for row in cursor.fetchall()]
        conn.close()
        return attrs

    def list_relationships(self) -> List[OntologyRelationship]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, from_entity_id, to_entity_id, relationship_type,
                   description, cardinality, status, created_at
            FROM ontology_relationship
            WHERE status = 'active'
        """)
        rels = [OntologyRelationship.from_db_row(tuple(row)) for row in cursor.fetchall()]
        conn.close()
        return rels

    def list_metric_entity_maps(self) -> List[MetricEntityMap]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, metric_id, entity_id, grain_level,
                   allowed_dimensions, forbidden_dimensions, join_path_policy, created_at
            FROM metric_entity_map
        """)
        maps = [MetricEntityMap.from_db_row(tuple(row)) for row in cursor.fetchall()]
        conn.close()
        return maps

    def list_metric_dependencies(self) -> List[MetricDependency]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, upstream_metric_id, downstream_metric_id,
                   upstream_version_id, downstream_version_id,
                   dependency_type, description, created_at
            FROM metric_dependency
        """)
        deps = [MetricDependency.from_db_row(tuple(row)) for row in cursor.fetchall()]
        conn.close()
        return deps

    def find_terms_in_text(self, text: str) -> List[TermDictionary]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, term, normalized_term, object_type, object_id,
                   language, status, created_at
            FROM term_dictionary
            WHERE status = 'active'
        """)
        terms = []
        for row in cursor.fetchall():
            term = row['term']
            if term and term in text:
                terms.append(TermDictionary.from_db_row(tuple(row)))
        conn.close()
        return terms

    def replace_metric_dependencies_for_version(
        self,
        downstream_metric_id: int,
        downstream_version_id: int,
        dependencies: List[MetricDependency]
    ) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM metric_dependency
            WHERE downstream_metric_id = ? AND downstream_version_id = ?
        """, (downstream_metric_id, downstream_version_id))

        for dep in dependencies:
            cursor.execute("""
                INSERT INTO metric_dependency (
                    upstream_metric_id, downstream_metric_id,
                    upstream_version_id, downstream_version_id,
                    dependency_type, description
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                dep.upstream_metric_id, dep.downstream_metric_id,
                dep.upstream_version_id, dep.downstream_version_id,
                dep.dependency_type, dep.description
            ))

        conn.commit()
        conn.close()


class SQLitePolicyStore:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def get_applicable_policies(
        self,
        semantic_object_id: int,
        role: str,
        action: str
    ) -> List[AccessPolicy]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, semantic_object_id, role, action, condition,
                   effect, priority, created_at
            FROM access_policy
            WHERE semantic_object_id = ?
              AND (role = ? OR role = '*')
              AND (action = ? OR action = '*')
            ORDER BY priority DESC
        """, (semantic_object_id, role, action))

        policies = [AccessPolicy.from_db_row(tuple(row)) for row in cursor.fetchall()]
        conn.close()
        return policies

    def get_user_policies(self, role: str) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT ap.id, ap.role, ap.action, ap.effect, ap.priority,
                   so.name as semantic_object_name, so.domain
            FROM access_policy ap
            JOIN semantic_object so ON ap.semantic_object_id = so.id
            WHERE ap.role = ? OR ap.role = '*'
            ORDER BY ap.priority DESC
        """, (role,))

        policies = []
        for row in cursor.fetchall():
            policies.append({
                'id': row['id'],
                'role': row['role'],
                'semantic_object': row['semantic_object_name'],
                'domain': row['domain'],
                'action': row['action'],
                'effect': row['effect'],
                'priority': row['priority']
            })

        conn.close()
        return policies

    def create_policy(
        self,
        semantic_object_id: int,
        role: str,
        action: str,
        effect: str,
        condition: Optional[Dict[str, Any]] = None,
        priority: int = 0
    ) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        condition_json = json.dumps(condition) if condition else None

        cursor.execute("""
            INSERT INTO access_policy
            (semantic_object_id, role, action, condition, effect, priority)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (semantic_object_id, role, action, condition_json, effect, priority))

        policy_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return policy_id


class SQLiteAuditStore:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def save_audit(self, audit: ExecutionAudit) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO execution_audit (
                audit_id, question, semantic_object_id, semantic_object_name,
                version_id, version_name, logical_definition_id, logical_expression,
                physical_mapping_id, connection_ref, final_sql, decision_trace,
                request_params, execution_context, user_id, user_role, policy_decision, executed_at, status,
                row_count, execution_time_ms, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            audit.audit_id, audit.question, audit.semantic_object_id, audit.semantic_object_name,
            audit.version_id, audit.version_name, audit.logical_definition_id, audit.logical_expression,
            audit.physical_mapping_id, audit.connection_ref, audit.final_sql,
            json.dumps(audit.decision_trace),
            json.dumps(audit.request_params) if audit.request_params is not None else None,
            json.dumps(audit.execution_context) if audit.execution_context is not None else None,
            audit.user_id, audit.user_role, audit.policy_decision,
            audit.executed_at.isoformat() if audit.executed_at else None,
            audit.status, audit.row_count, audit.execution_time_ms, audit.error_message
        ))

        conn.commit()
        conn.close()

    def save_denied(
        self,
        audit_id: str,
        question: str,
        semantic_obj: Optional[SemanticObject],
        decision_trace: List[Dict[str, Any]],
        context: ExecutionContext,
        error: str
    ) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO execution_audit (
                audit_id, question, semantic_object_id, semantic_object_name,
                decision_trace, request_params, execution_context, user_id, user_role, executed_at, status, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            audit_id, question,
            semantic_obj.id if semantic_obj else None,
            semantic_obj.name if semantic_obj else None,
            json.dumps({'steps': decision_trace}),
            json.dumps(context.parameters) if context.parameters else None,
            json.dumps(context.to_dict()),
            context.user_id, context.role, context.timestamp.isoformat(),
            'denied', error
        ))

        conn.commit()
        conn.close()

    def load_audit(self, audit_id: str) -> Optional[ExecutionAudit]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, audit_id, question, semantic_object_id, semantic_object_name,
                   version_id, version_name, logical_definition_id, logical_expression,
                   physical_mapping_id, connection_ref, final_sql, decision_trace,
                   request_params, execution_context,
                   user_id, user_role, policy_decision, executed_at, status,
                   row_count, execution_time_ms, error_message
            FROM execution_audit
            WHERE audit_id = ?
        """, (audit_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return ExecutionAudit.from_db_row(tuple(row))
        return None

    def list_audit_history(
        self,
        limit: int = 50,
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = """
            SELECT audit_id, question, semantic_object_name, user_role,
                   executed_at, status, row_count
            FROM execution_audit
        """
        params = []
        if user_id:
            query += " WHERE user_id = ?"
            params.append(user_id)
        query += " ORDER BY executed_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        history = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return history


class SQLiteQueryExecutor:
    def __init__(self, data_db_path: str):
        self.data_db_path = data_db_path

    def execute(
        self,
        sql: str,
        connection_ref: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.data_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(sql, parameters or {})
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
