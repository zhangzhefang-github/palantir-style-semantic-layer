import sqlite3
from typing import Dict, Any


def create_metric(
    db_path: str,
    name: str,
    description: str,
    aliases_json: str,
    domain: str = "quality",
    status: str = "active"
) -> int:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO semantic_object (name, description, aliases, domain, status)
        VALUES (?, ?, ?, ?, ?)
        """,
        (name, description, aliases_json, domain, status)
    )
    metric_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return metric_id


def create_version(
    db_path: str,
    metric_id: int,
    version_name: str,
    effective_from: str,
    scenario_condition: str = None,
    priority: int = 0,
    description: str = ""
) -> int:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO semantic_version
        (semantic_object_id, version_name, effective_from, scenario_condition, is_active, priority, description)
        VALUES (?, ?, ?, ?, 1, ?, ?)
        """,
        (metric_id, version_name, effective_from, scenario_condition, priority, description)
    )
    version_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return version_id


def create_logical_definition(
    db_path: str,
    version_id: int,
    expression: str,
    grain: str,
    description: str,
    variables_json: str
) -> int:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO logical_definition
        (semantic_version_id, expression, grain, description, variables)
        VALUES (?, ?, ?, ?, ?)
        """,
        (version_id, expression, grain, description, variables_json)
    )
    logical_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return logical_id


def create_mapping(
    db_path: str,
    logical_id: int,
    sql_template: str,
    params_schema: str,
    priority: int = 1,
    engine_type: str = "sqlite",
    connection_ref: str = "default",
    description: str = ""
) -> int:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO physical_mapping
        (logical_definition_id, engine_type, connection_ref, sql_template, params_schema, priority, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (logical_id, engine_type, connection_ref, sql_template, params_schema, priority, description)
    )
    mapping_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return mapping_id


def create_term(
    db_path: str,
    term: str,
    normalized_term: str,
    object_type: str,
    object_id: int,
    language: str = "zh",
    status: str = "active"
) -> int:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO term_dictionary
        (term, normalized_term, object_type, object_id, language, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (term, normalized_term, object_type, object_id, language, status)
    )
    term_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return term_id
