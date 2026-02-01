"""
Semantic Orchestrator

The core coordinator that orchestrates the entire semantic query lifecycle.
Connects natural language questions to executable SQL with full audit trail.

This is the brain of the semantic control plane.
"""

import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

from .models import (
    SemanticObject, SemanticVersion, LogicalDefinition,
    PhysicalMapping, ExecutionContext, ExecutionAudit,
    PolicyDeniedError, AmbiguityError, VersionNotFoundError
)
from .semantic_resolver import SemanticResolver
from .policy_engine import PolicyEngine
from .execution_engine import ExecutionEngine, ExecutionResult
from .interfaces import MetadataStore, PolicyStore, AuditStore, QueryExecutor
from .config import OrchestratorConfig
from .impact_analysis import ImpactAnalyzer
from .dependency_builder import DependencyBuilder
from .grain_validator import GrainValidator
from .sqlite_stores import (
    SQLiteMetadataStore,
    SQLitePolicyStore,
    SQLiteAuditStore,
    SQLiteQueryExecutor,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SemanticOrchestrator:
    """
    Main orchestrator for semantic queries.

    Orchestrates the complete flow:
    1. Resolve semantic object
    2. Resolve version
    3. Resolve logic
    4. Resolve physical mapping
    5. Check access policy
    6. Generate execution plan
    7. Preview (optional)
    8. Execute
    9. Audit

    Every decision is tracked for replayability.
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        config: Optional[OrchestratorConfig] = None,
        metadata_store: Optional[MetadataStore] = None,
        policy_store: Optional[PolicyStore] = None,
        audit_store: Optional[AuditStore] = None,
        query_executor: Optional[QueryExecutor] = None
    ):
        """
        Initialize the orchestrator.

        Args:
            db_path: Path to SQLite database (contains both metadata and data)
            config: Orchestrator configuration (preferred over db_path when provided)
            metadata_store: Metadata store implementation
            policy_store: Policy store implementation
            audit_store: Audit store implementation
            query_executor: Query executor implementation
        """
        if config is not None and db_path is None:
            db_path = config.db_path

        if metadata_store is None or policy_store is None or audit_store is None or query_executor is None:
            if not db_path:
                raise ValueError("db_path is required when stores/executor are not provided")

        self.default_engine_type = config.default_engine_type if config else "sqlite"
        self.metadata_store = metadata_store or SQLiteMetadataStore(db_path)
        self.policy_store = policy_store or SQLitePolicyStore(db_path)
        self.audit_store = audit_store or SQLiteAuditStore(db_path)
        self.query_executor = query_executor or SQLiteQueryExecutor(db_path)

        # Initialize components
        self.resolver = SemanticResolver(metadata_store=self.metadata_store)
        self.policy_engine = PolicyEngine(policy_store=self.policy_store)
        self.execution_engine = ExecutionEngine(
            metadata_store=self.metadata_store,
            query_executor=self.query_executor
        )
        self.impact_analyzer = ImpactAnalyzer(self.metadata_store)
        self.dependency_builder = DependencyBuilder(self.metadata_store)
        self.grain_validator = GrainValidator(self.metadata_store)

        logger.info(f"SemanticOrchestrator initialized with database: {db_path}")

    # ============================================================
    # MAIN QUERY FLOW
    # ============================================================

    def query(
        self,
        question: str,
        parameters: Dict[str, Any],
        context: ExecutionContext,
        preview_only: bool = False
    ) -> Dict[str, Any]:
        """
        Execute a semantic query end-to-end.

        Args:
            question: Natural language question
            parameters: Query parameters (e.g., dates, filters)
            context: Execution context (user, role, timestamp)
            preview_only: If True, preview without executing

        Returns:
            Result dict with decision trace and data
        """
        audit_id = self._generate_audit_id()
        decision_trace = []
        trace = lambda step, data: decision_trace.append({
            'step': step,
            'timestamp': datetime.now().isoformat(),
            'data': data
        })

        logger.info("=" * 80)
        logger.info(f"SEMANTIC QUERY: {question}")
        logger.info(f"Audit ID: {audit_id}")
        logger.info("=" * 80)

        semantic_obj = None
        version = None
        logical_def = None
        physical_mapping = None
        policy_decision = None
        execution_result = None

        try:
            # STEP 1: Resolve semantic object
            trace('resolve_semantic_object_start', {
                'question': question,
                'semantic_object_reason': 'Extracting semantic object from natural language'
            })
            semantic_obj = self.resolver.resolve_semantic_object(question)
            trace('resolve_semantic_object_complete', {
                'semantic_object_id': semantic_obj.id,
                'semantic_object_name': semantic_obj.name,
                'semantic_object_reason': f'Matched semantic object "{semantic_obj.name}" (domain: {semantic_obj.domain}, aliases: {semantic_obj.aliases})'
            })

            # STEP 2: Resolve version
            scenario_provided = parameters.get('scenario')
            trace('resolve_version_start', {
                'semantic_object_id': semantic_obj.id,
                'scenario_evaluated': scenario_provided,
                'version_selection_reason': 'Evaluating versions based on scenario match and time effectiveness'
            })
            version = self.resolver.resolve_version(
                semantic_obj.id,
                scenario=parameters.get('scenario'),
                timestamp=context.timestamp
            )
            trace('resolve_version_complete', {
                'version_id': version.id,
                'version_name': version.version_name,
                'scenario_condition': version.scenario_condition,
                'version_selection_reason': f'Selected version "{version.version_name}" - scenario_match={scenario_provided is not None and version.scenario_condition is not None}'
            })

            # STEP 3: Resolve logic
            trace('resolve_logic_start', {
                'version_id': version.id,
                'logic_resolution_reason': 'Resolving business logic formula from version definition'
            })
            logical_def = self.resolver.resolve_logic(version.id)
            trace('resolve_logic_complete', {
                'logical_definition_id': logical_def.id,
                'expression': logical_def.expression,
                'grain': logical_def.grain,
                'logic_expression': logical_def.expression,
                'logic_resolution_reason': f'Business logic: {logical_def.expression} (grain: {logical_def.grain})'
            })

            # STEP 3.5: Grain validation
            validation = self.grain_validator.validate(semantic_obj.id, parameters, logical_def.grain or "")
            trace('grain_validation', validation)
            if validation.get("status") == "FAIL":
                reason = validation.get("reason", "Grain validation failed")
                suggestions = validation.get("suggestions", {})
                if suggestions:
                    reason = f"{reason}. Suggestions: {suggestions}"
                raise ValueError(reason)

            # STEP 4: Resolve physical mapping
            trace('resolve_physical_mapping_start', {
                'logical_definition_id': logical_def.id,
                'physical_mapping_reason': 'Mapping logical definition to SQL implementation'
            })
            physical_mapping = self.execution_engine.resolve_physical_mapping(
                logical_def.id,
                engine_type=self.default_engine_type
            )
            trace('resolve_physical_mapping_complete', {
                'physical_mapping_id': physical_mapping.id,
                'engine_type': physical_mapping.engine_type,
                'connection_ref': physical_mapping.connection_ref,
                'physical_mapping_reason': f'Selected physical mapping using {physical_mapping.engine_type} engine (priority: {physical_mapping.priority})'
            })

            # STEP 5: Check access policy
            trace('policy_check_start', {
                'semantic_object_id': semantic_obj.id,
                'user_role': context.role,
                'policy_check_reason': 'Evaluating access policies'
            })
            policy_decision = self.policy_engine.check_access(
                semantic_object_id=semantic_obj.id,
                role=context.role,
                action='query',
                context=parameters
            )
            trace('policy_check_complete', {
                'policy_decision': 'ALLOW' if policy_decision.get('allow') else 'DENY',
                'policy_reason': policy_decision.get('reason'),
                'policy_details': {
                    'allow': policy_decision.get('allow'),
                    'reason': policy_decision.get('reason'),
                    'policy_count': len(policy_decision.get('policies', []))
                }
            })

            # STEP 6: Render SQL
            trace('render_sql_start', {
                'parameters': parameters,
                'sql_generation_reason': 'Rendering SQL from Jinja2 template with parameters'
            })
            sql = self.execution_engine.render_sql(physical_mapping, parameters)
            trace('render_sql_complete', {
                'sql_preview': sql[:200] + '...' if len(sql) > 200 else sql
            })

            # STEP 7: Preview or execute
            if preview_only:
                trace('preview_complete', {
                    'preview': True,
                    'sql': sql
                })

                logger.info("=" * 80)
                logger.info("PREVIEW MODE - SQL NOT EXECUTED")
                logger.info("=" * 80)

                return {
                    'audit_id': audit_id,
                    'status': 'preview',
                    'semantic_object': semantic_obj.name,
                    'version': version.version_name,
                    'logic': logical_def.expression,
                    'sql': sql,
                    'decision_trace': decision_trace
                }

            # STEP 8: Execute
            trace('execution_start', {
                'sql': sql,
                'execution_reason': 'Executing generated SQL against data source'
            })
            execution_result = self.execution_engine.execute(
                sql,
                physical_mapping.connection_ref,
                parameters
            )
            trace('execution_complete', {
                'row_count': execution_result.row_count,
                'execution_time_ms': execution_result.execution_time_ms,
                'execution_result': 'Query executed successfully' if execution_result.success else f'Query failed: {execution_result.error}'
            })

            # STEP 9: Audit
            audit_record = self._create_audit_record(
                audit_id=audit_id,
                question=question,
                semantic_obj=semantic_obj,
                version=version,
                logical_def=logical_def,
                physical_mapping=physical_mapping,
                sql=sql,
                decision_trace=decision_trace,
                context=context,
                policy_decision=policy_decision,
                execution_result=execution_result,
                status='success' if execution_result.success else 'error'
            )

            self._save_audit(audit_record)

            logger.info("=" * 80)
            logger.info(f"QUERY COMPLETE - Status: {audit_record.status}")
            logger.info(f"Audit ID: {audit_id}")
            logger.info(f"Row Count: {execution_result.row_count}")
            logger.info("=" * 80)

            return {
                'audit_id': audit_id,
                'status': audit_record.status,
                'semantic_object': semantic_obj.name,
                'version': version.version_name,
                'logic': logical_def.expression,
                'sql': sql,
                'data': execution_result.data,
                'row_count': execution_result.row_count,
                'execution_time_ms': execution_result.execution_time_ms,
                'decision_trace': decision_trace
            }

        except PolicyDeniedError as e:
            # Policy denied - audit and return
            trace('policy_denied', {'reason': str(e)})
            self._audit_denied(
                audit_id=audit_id,
                question=question,
                semantic_obj=semantic_obj,
                decision_trace=decision_trace,
                context=context,
                error=str(e)
            )

            logger.warning(f"ACCESS DENIED: {e}")
            return {
                'audit_id': audit_id,
                'status': 'denied',
                'error': str(e),
                'decision_trace': decision_trace
            }

        except (AmbiguityError, VersionNotFoundError) as e:
            # Resolution error - audit and return structured error
            trace('resolution_error', {'error': str(e), 'type': type(e).__name__})

            logger.warning(f"RESOLUTION ERROR: {e}")

            # Audit the error
            self._audit_denied(
                audit_id=audit_id,
                question=question,
                semantic_obj=semantic_obj,
                decision_trace=decision_trace,
                context=context,
                error=str(e)
            )

            error_response = {
                'audit_id': audit_id,
                'status': 'error',
                'error_type': type(e).__name__,
                'error': str(e),
                'decision_trace': decision_trace
            }

            if isinstance(e, AmbiguityError):
                error_response['candidates'] = e.candidates

            return error_response

        except Exception as e:
            # Unexpected error
            trace('unexpected_error', {'error': str(e)})
            logger.error(f"UNEXPECTED ERROR: {e}", exc_info=True)

            self._audit_denied(
                audit_id=audit_id,
                question=question,
                semantic_obj=semantic_obj,
                decision_trace=decision_trace,
                context=context,
                error=str(e)
            )

            return {
                'audit_id': audit_id,
                'status': 'error',
                'error': str(e),
                'decision_trace': decision_trace
            }

    # ============================================================
    # REPLAY FUNCTIONALITY
    # ============================================================

    def replay(self, audit_id: str) -> Dict[str, Any]:
        """
        Replay a previous query execution.

        Replay uses the original SQL (final_sql) without re-executing
        semantic resolution, version selection, or policy checks.

        This ensures replay consistency:
        - Same SQL as original
        - Only data may change (if underlying data changed)
        - Decision chain preserved from original execution

        Args:
            audit_id: Audit ID to replay

        Returns:
            Replay result with previous and new data
        """
        logger.info(f"REPLAY REQUEST: {audit_id}")

        # Load original audit record
        original = self._load_audit(audit_id)

        if not original:
            raise ValueError(f"Audit record not found: {audit_id}")

        logger.info(f"Original Query: {original.question}")
        logger.info(f"Original Status: {original.status}")
        logger.info(f"Replay Mode: Using original SQL without re-resolution")

        if original.status != 'success':
            logger.warning(f"Cannot replay unsuccessful query (status={original.status})")
            return {
                'error': f'Cannot replay query with status: {original.status}',
                'original_audit': original.to_dict()
            }

        # Create replay decision trace
        replay_decision_trace = [
            {
                'step': 'replay_start',
                'timestamp': datetime.now().isoformat(),
                'data': {
                    'replay_mode': True,
                    'replay_source_audit_id': audit_id,
                    'original_question': original.question,
                    'original_sql': original.final_sql,
                    'replay_reason': 'Using original SQL without re-executing semantic resolution or version selection'
                }
            },
            {
                'step': 'replay_execution_start',
                'timestamp': datetime.now().isoformat(),
                'data': {
                    'sql': original.final_sql,
                    'connection_ref': original.connection_ref,
                    'execution_reason': 'Re-executing original SQL'
                }
            }
        ]

        # Execute original SQL
        execution_result = self.execution_engine.execute(
            original.final_sql,
            original.connection_ref
        )

        replay_decision_trace.append({
            'step': 'replay_execution_complete',
            'timestamp': datetime.now().isoformat(),
            'data': {
                'row_count': execution_result.row_count,
                'execution_time_ms': execution_result.execution_time_ms,
                'execution_result': 'Query executed successfully' if execution_result.success else f'Query failed: {execution_result.error}'
            }
        })

        # Create replay audit record
        replay_audit_id = self._generate_audit_id()
        replay_audit = self._create_audit_record(
            audit_id=replay_audit_id,
            question=original.question,
            semantic_obj=SemanticObject(id=original.semantic_object_id or 0, name=original.semantic_object_name or '', description='', aliases=[], domain='', status=''),
            version=SemanticVersion(id=original.version_id or 0, semantic_object_id=0, version_name=original.version_name or '', effective_from=datetime.now(), effective_to=None, scenario_condition=None, is_active=True, priority=0),
            logical_def=LogicalDefinition(id=original.logical_definition_id or 0, semantic_version_id=0, expression=original.logical_expression or '', grain='', description='', variables='[]'),
            physical_mapping=PhysicalMapping(id=original.physical_mapping_id or 0, logical_definition_id=0, engine_type='', connection_ref=original.connection_ref or '', sql_template=original.final_sql or '', params_schema='', priority=0, description=''),
            sql=original.final_sql or '',
            decision_trace=replay_decision_trace,
            context=ExecutionContext(user_id=original.user_id or 0, role=original.user_role or 'unknown', parameters={}, timestamp=datetime.now()),
            policy_decision={'allow': True, 'reason': 'Replay uses pre-authorized SQL', 'policy_count': 0},
            execution_result=execution_result,
            status='success' if execution_result.success else 'error'
        )

        self._save_audit(replay_audit)

        logger.info("=" * 80)
        logger.info(f"REPLAY COMPLETE - Status: {execution_result.success}")
        logger.info(f"Original Audit ID: {audit_id}")
        logger.info(f"New Audit ID: {replay_audit_id}")
        logger.info(f"Row Count: {execution_result.row_count}")
        logger.info("=" * 80)

        return {
            'original_audit_id': audit_id,
            'new_audit_id': replay_audit_id,
            'original': original.to_dict(),
            'new': {
                'audit_id': replay_audit_id,
                'status': 'success' if execution_result.success else 'error',
                'data': execution_result.data,
                'row_count': execution_result.row_count,
                'execution_time_ms': execution_result.execution_time_ms,
                'decision_trace': replay_decision_trace
            }
        }

    # ============================================================
    # AUDIT FUNCTIONALITY
    # ============================================================

    def get_audit_history(
        self,
        limit: int = 50,
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get audit history.

        Args:
            limit: Maximum number of records
            user_id: Optional user filter

        Returns:
            List of audit records
        """
        return self.audit_store.list_audit_history(limit=limit, user_id=user_id)

    # ============================================================
    # UTILITY METHODS
    # ============================================================

    def _generate_audit_id(self) -> str:
        """Generate unique audit ID"""
        return datetime.now().strftime("%Y%m%d_%H%M%S_") + str(uuid.uuid4())[:8]

    def _create_audit_record(
        self,
        audit_id: str,
        question: str,
        semantic_obj: SemanticObject,
        version: SemanticVersion,
        logical_def: LogicalDefinition,
        physical_mapping: PhysicalMapping,
        sql: str,
        decision_trace: List[Dict],
        context: ExecutionContext,
        policy_decision: Dict,
        execution_result: ExecutionResult,
        status: str
    ) -> ExecutionAudit:
        """Create audit record from query execution"""

        # Convert policy_decision to JSON-serializable format
        serializable_policy = {
            'allow': policy_decision.get('allow'),
            'reason': policy_decision.get('reason'),
            'policy_count': len(policy_decision.get('policies', []))
        }

        return ExecutionAudit(
            id=0,  # Will be assigned by DB
            audit_id=audit_id,
            question=question,
            semantic_object_id=semantic_obj.id,
            semantic_object_name=semantic_obj.name,
            version_id=version.id,
            version_name=version.version_name,
            logical_definition_id=logical_def.id,
            logical_expression=logical_def.expression,
            physical_mapping_id=physical_mapping.id,
            connection_ref=physical_mapping.connection_ref,
            final_sql=sql,
            decision_trace={'steps': decision_trace},
            request_params=context.parameters if context.parameters else None,
            execution_context=context.to_dict(),
            user_id=context.user_id,
            user_role=context.role,
            policy_decision=json.dumps(serializable_policy),
            executed_at=datetime.now(),
            status=status,
            row_count=execution_result.row_count,
            execution_time_ms=execution_result.execution_time_ms,
            error_message=execution_result.error
        )

    def _save_audit(self, audit: ExecutionAudit) -> None:
        """Save audit record to database"""
        self.audit_store.save_audit(audit)
        logger.info(f"Audit record saved: {audit.audit_id}")

    def _audit_denied(
        self,
        audit_id: str,
        question: str,
        semantic_obj: Optional[SemanticObject],
        decision_trace: List[Dict],
        context: ExecutionContext,
        error: str
    ) -> None:
        """Save audit record for denied/failed query"""
        self.audit_store.save_denied(
            audit_id=audit_id,
            question=question,
            semantic_obj=semantic_obj,
            decision_trace=decision_trace,
            context=context,
            error=error
        )

    def _load_audit(self, audit_id: str) -> Optional[ExecutionAudit]:
        """Load audit record by ID"""
        return self.audit_store.load_audit(audit_id)

    # ============================================================
    # CONVENIENCE METHODS
    # ============================================================

    def list_semantic_objects(self) -> List[Dict[str, Any]]:
        """List all available semantic objects"""
        objects = self.resolver.get_all_semantic_objects()
        return [
            {
                'id': obj.id,
                'name': obj.name,
                'description': obj.description,
                'domain': obj.domain,
                'aliases': obj.aliases
            }
            for obj in objects
        ]

    # ============================================================
    # IMPACT ANALYSIS
    # ============================================================

    def impact(self, target_type: str, target_id: int) -> Dict[str, Any]:
        """Return impact analysis for a target node."""
        return self.impact_analyzer.impact(target_type, target_id)

    def diff_versions(self, metric_name: str, version_a: str, version_b: str) -> Dict[str, Any]:
        """Return diff summary between two metric versions."""
        return self.impact_analyzer.diff(metric_name, version_a, version_b)

    def impact_report(self, metric_name: str, version_a: str, version_b: str) -> Dict[str, Any]:
        """Generate impact report (JSON + markdown)."""
        return self.impact_analyzer.generate_report(metric_name, version_a, version_b)

    def rebuild_dependencies(self) -> None:
        """Rebuild metric dependencies from logical definitions."""
        self.dependency_builder.rebuild_all()

    def rebuild_dependencies_for_metric(self, metric_name: str) -> None:
        """Rebuild dependencies for a single metric."""
        self.dependency_builder.rebuild_for_metric(metric_name)

    def detect_dependency_cycles(self) -> List[List[tuple]]:
        """Detect cycles in metric dependencies."""
        return self.dependency_builder.detect_cycles()
