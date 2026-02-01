"""
Execution Engine

Handles physical SQL execution and result processing.
Responsible for rendering SQL templates and executing against data sources.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from jinja2 import Template, TemplateError

from .models import PhysicalMapping, MappingNotFoundError
from .interfaces import MetadataStore, QueryExecutor
from .sqlite_stores import SQLiteMetadataStore, SQLiteQueryExecutor

logger = logging.getLogger(__name__)


class ExecutionResult:
    """Container for execution results"""

    def __init__(
        self,
        success: bool,
        data: Optional[List[Dict[str, Any]]] = None,
        row_count: Optional[int] = None,
        sql: Optional[str] = None,
        execution_time_ms: Optional[int] = None,
        error: Optional[str] = None
    ):
        self.success = success
        self.data = data if data is not None else []
        self.row_count = row_count if row_count is not None else len(data) if data else 0
        self.sql = sql
        self.execution_time_ms = execution_time_ms
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'row_count': self.row_count,
            'sql': self.sql,
            'execution_time_ms': self.execution_time_ms,
            'error': self.error,
            'data': self.data
        }


class ExecutionEngine:
    """
    Executes SQL against physical data sources.

    Responsibilities:
    1. Render SQL templates from physical mappings
    2. Execute SQL against data sources
    3. Return structured results
    4. Track execution metrics
    """

    def __init__(
        self,
        metadata_store: Optional[MetadataStore] = None,
        query_executor: Optional[QueryExecutor] = None,
        metadata_db_path: Optional[str] = None,
        data_db_path: Optional[str] = None
    ):
        """
        Initialize the execution engine.

        Args:
            metadata_store: Metadata store implementation
            query_executor: Query executor implementation
            metadata_db_path: Path to metadata database (for sqlite default store)
            data_db_path: Path to data database (defaults to metadata_db_path for POC)
        """
        if metadata_store is None:
            if not metadata_db_path:
                raise ValueError("metadata_db_path is required when metadata_store is not provided")
            metadata_store = SQLiteMetadataStore(metadata_db_path)
        if query_executor is None:
            data_path = data_db_path or metadata_db_path
            if not data_path:
                raise ValueError("data_db_path is required when query_executor is not provided")
            query_executor = SQLiteQueryExecutor(data_path)

        self.metadata_store = metadata_store
        self.query_executor = query_executor

    def resolve_physical_mapping(
        self,
        logical_definition_id: int,
        engine_type: Optional[str] = None
    ) -> PhysicalMapping:
        """
        Resolve physical mapping for a logical definition.

        Args:
            logical_definition_id: ID of logical definition
            engine_type: Optional engine type filter (e.g., 'sqlite', 'postgres')

        Returns:
            Selected PhysicalMapping

        Raises:
            MappingNotFoundError: If no mapping found
        """
        logger.info(f"=== STEP 4: RESOLVE PHYSICAL MAPPING ===")
        logger.info(f"Logical Definition ID: {logical_definition_id}")

        mappings = self.metadata_store.get_physical_mappings(
            logical_definition_id=logical_definition_id,
            engine_type=engine_type
        )

        if not mappings:
            raise MappingNotFoundError(
                f"No physical mapping found for logical_definition_id={logical_definition_id}"
            )
        mapping = mappings[0]
        logger.info(f"✓ Selected physical mapping: {mapping.id}")
        logger.info(f"  Engine: {mapping.engine_type}")
        logger.info(f"  Connection: {mapping.connection_ref}")
        logger.info(f"  Priority: {mapping.priority}")

        return mapping

    def render_sql(
        self,
        mapping: PhysicalMapping,
        parameters: Dict[str, Any]
    ) -> str:
        """
        Render SQL template with parameters using Jinja2.

        Args:
            mapping: Physical mapping containing SQL template
            parameters: Parameters used for validation and optional template blocks

        Returns:
            Rendered SQL string

        Raises:
            ValueError: If required parameters are missing
            TemplateError: If template rendering fails
        """
        logger.info(f"=== STEP 5: RENDER SQL ===")
        logger.info(f"Parameters: {parameters}")

        # Validate required parameters
        if mapping.params_schema:
            missing_params = []
            for param_name in mapping.params_schema.keys():
                if param_name not in parameters:
                    missing_params.append(param_name)

            if missing_params:
                raise ValueError(
                    f"Missing required parameters: {missing_params}. "
                    f"Required schema: {mapping.params_schema}"
                )

        # Render SQL template
        try:
            template = Template(mapping.sql_template)
            rendered_sql = template.render(**parameters)

            # Clean up extra whitespace for logging
            clean_sql = ' '.join(rendered_sql.split())
            logger.info(f"✓ Rendered SQL:")
            logger.info(f"{clean_sql}")

            return rendered_sql

        except TemplateError as e:
            logger.error(f"SQL rendering failed: {e}")
            raise

    def execute(
        self,
        sql: str,
        connection_ref: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """
        Execute SQL against the data source.

        Args:
            sql: SQL to execute
            connection_ref: Connection reference (for POC, defaults to data_db_path)

        Returns:
            ExecutionResult with data and metrics
        """
        logger.info(f"=== STEP 6: EXECUTE SQL ===")

        start_time = datetime.now()

        try:
            data = self.query_executor.execute(sql, connection_ref, parameters)

            row_count = len(data)

            end_time = datetime.now()
            execution_time_ms = int((end_time - start_time).total_seconds() * 1000)

            logger.info(f"✓ Execution successful")
            logger.info(f"  Rows returned: {row_count}")
            logger.info(f"  Execution time: {execution_time_ms}ms")

            # Log sample data
            if data:
                sample = data[0]
                logger.info(f"  Sample result: {sample}")

            return ExecutionResult(
                success=True,
                data=data,
                row_count=row_count,
                sql=sql,
                execution_time_ms=execution_time_ms
            )

        except Exception as e:
            end_time = datetime.now()
            execution_time_ms = int((end_time - start_time).total_seconds() * 1000)

            logger.error(f"✗ Execution failed: {e}")
            return ExecutionResult(
                success=False,
                error=str(e),
                sql=sql,
                execution_time_ms=execution_time_ms
            )

    def execute_with_mapping(
        self,
        logical_definition_id: int,
        parameters: Dict[str, Any],
        engine_type: Optional[str] = None
    ) -> ExecutionResult:
        """
        Convenience method: resolve mapping, render SQL, and execute.

        Args:
            logical_definition_id: ID of logical definition
            parameters: Parameters for SQL rendering
            engine_type: Optional engine type filter

        Returns:
            ExecutionResult
        """
        # Resolve physical mapping
        mapping = self.resolve_physical_mapping(logical_definition_id, engine_type)

        # Render SQL
        sql = self.render_sql(mapping, parameters)

        # Execute
        result = self.execute(sql, mapping.connection_ref, parameters)

        return result

    def preview(
        self,
        logical_definition_id: int,
        parameters: Dict[str, Any],
        engine_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Preview execution without running (dry run).

        Returns:
            Dict with mapping info and rendered SQL
        """
        mapping = self.resolve_physical_mapping(logical_definition_id, engine_type)
        sql = self.render_sql(mapping, parameters)

        return {
            'mapping': {
                'id': mapping.id,
                'engine_type': mapping.engine_type,
                'connection_ref': mapping.connection_ref,
                'description': mapping.description
            },
            'sql': sql,
            'parameters': parameters
        }
