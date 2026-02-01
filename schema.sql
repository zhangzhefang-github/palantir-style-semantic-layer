-- ============================================================
-- Palantir-Style Semantic Control Plane
-- Database Schema
-- ============================================================

-- Drop tables if they exist (for clean rebuild)
DROP TABLE IF EXISTS execution_audit;
DROP TABLE IF EXISTS access_policy;
DROP TABLE IF EXISTS physical_mapping;
DROP TABLE IF EXISTS logical_definition;
DROP TABLE IF EXISTS semantic_version;
DROP TABLE IF EXISTS term_dictionary;
DROP TABLE IF EXISTS metric_dependency;
DROP TABLE IF EXISTS metric_entity_map;
DROP TABLE IF EXISTS ontology_relationship;
DROP TABLE IF EXISTS ontology_attribute;
DROP TABLE IF EXISTS ontology_dimension;
DROP TABLE IF EXISTS ontology_entity;
DROP TABLE IF EXISTS semantic_object;
DROP TABLE IF EXISTS fact_production_records;
DROP TABLE IF EXISTS fact_finance_records;

-- ============================================================
-- 1️⃣ SEMANTIC_OBJECT
-- Defines what business concepts exist in the system
-- ============================================================
CREATE TABLE semantic_object (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    aliases TEXT NOT NULL,  -- JSON array of alternative names
    domain TEXT NOT NULL,   -- e.g., 'production', 'quality', 'sales'
    status TEXT NOT NULL DEFAULT 'active',  -- active, deprecated
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 2️⃣ SEMANTIC_VERSION
-- Tracks different versions of semantic object definitions
-- Handles business logic changes over time/scenario
-- ============================================================
CREATE TABLE semantic_version (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    semantic_object_id INTEGER NOT NULL,
    version_name TEXT NOT NULL,
    effective_from TIMESTAMP NOT NULL,
    effective_to TIMESTAMP,
    scenario_condition TEXT,  -- JSON: conditions for this version
    is_active BOOLEAN DEFAULT 1,
    priority INTEGER DEFAULT 0,  -- For conflict resolution: higher priority wins when scores are equal
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (semantic_object_id) REFERENCES semantic_object(id),
    UNIQUE(semantic_object_id, version_name)
);

-- ============================================================
-- 2️⃣.1 ONTOLOGY_ENTITY
-- Core business entities for ontology modeling
-- ============================================================
CREATE TABLE ontology_entity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    domain TEXT NOT NULL,
    entity_type TEXT DEFAULT 'dimension',  -- 'fact' or 'dimension'
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 2️⃣.2 ONTOLOGY_DIMENSION
-- Dimensions attached to entities
-- ============================================================
CREATE TABLE ontology_dimension (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    data_type TEXT NOT NULL,   -- string, date, number, bool
    is_time INTEGER DEFAULT 0, -- 1 if this is a time dimension
    grain_level TEXT,          -- 'day', 'week', 'month', 'quarter', 'year' for time dimensions
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (entity_id) REFERENCES ontology_entity(id),
    UNIQUE(entity_id, name)
);

-- ============================================================
-- 2️⃣.3 ONTOLOGY_ATTRIBUTE
-- Attributes attached to entities
-- ============================================================
CREATE TABLE ontology_attribute (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    data_type TEXT NOT NULL,   -- string, date, number, bool
    is_key BOOLEAN DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (entity_id) REFERENCES ontology_entity(id),
    UNIQUE(entity_id, name)
);

-- ============================================================
-- 2️⃣.4 ONTOLOGY_RELATIONSHIP
-- Relationships between entities
-- ============================================================
CREATE TABLE ontology_relationship (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_entity_id INTEGER NOT NULL,
    to_entity_id INTEGER NOT NULL,
    relationship_type TEXT NOT NULL,  -- e.g., "has_many", "belongs_to", "conversion_link", "weak_link"
    description TEXT,
    cardinality TEXT,                 -- e.g., "one_to_many", "many_to_one", "one_to_one", "many_to_many"
    join_keys TEXT,                   -- JSON array of join keys, e.g., '["user_id"]'
    link_strength TEXT DEFAULT 'strong',  -- 'strong', 'medium', 'weak' - for causal inference
    allows_causal INTEGER DEFAULT 1,  -- 1=causal inference allowed, 0=correlation only
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (from_entity_id) REFERENCES ontology_entity(id),
    FOREIGN KEY (to_entity_id) REFERENCES ontology_entity(id)
);

-- ============================================================
-- 2️⃣.5 METRIC_ENTITY_MAP
-- Explicit mapping between metric and entity
-- ============================================================
CREATE TABLE metric_entity_map (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_id INTEGER NOT NULL,
    entity_id INTEGER NOT NULL,
    grain_level TEXT NOT NULL,           -- e.g., "line,day"
    allowed_dimensions TEXT,             -- JSON array
    forbidden_dimensions TEXT,           -- JSON array
    join_path_policy TEXT,               -- e.g., "single_entity", "explicit_path"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (metric_id) REFERENCES semantic_object(id),
    FOREIGN KEY (entity_id) REFERENCES ontology_entity(id),
    UNIQUE(metric_id, entity_id)
);

-- ============================================================
-- 2️⃣.6 METRIC_DEPENDENCY
-- Metric-to-metric dependencies (DAG edges)
-- ============================================================
CREATE TABLE metric_dependency (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    upstream_metric_id INTEGER NOT NULL,
    downstream_metric_id INTEGER NOT NULL,
    upstream_version_id INTEGER,
    downstream_version_id INTEGER,
    dependency_type TEXT DEFAULT 'logical', -- logical/physical
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (upstream_metric_id) REFERENCES semantic_object(id),
    FOREIGN KEY (downstream_metric_id) REFERENCES semantic_object(id),
    FOREIGN KEY (upstream_version_id) REFERENCES semantic_version(id),
    FOREIGN KEY (downstream_version_id) REFERENCES semantic_version(id),
    UNIQUE(upstream_metric_id, upstream_version_id, downstream_metric_id, downstream_version_id)
);

-- ============================================================
-- 2️⃣.7 TERM_DICTIONARY
-- Lightweight term dictionary for normalization
-- ============================================================
CREATE TABLE term_dictionary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    term TEXT NOT NULL,
    normalized_term TEXT NOT NULL,
    object_type TEXT NOT NULL,  -- semantic_object/entity/dimension/attribute
    object_id INTEGER NOT NULL,
    language TEXT DEFAULT 'zh',
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 3️⃣ LOGICAL_DEFINITION
-- Business formula WITHOUT physical implementation details
-- Pure business logic, no table/field names
-- ============================================================
CREATE TABLE logical_definition (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    semantic_version_id INTEGER NOT NULL,
    expression TEXT NOT NULL,      -- Business formula (e.g., "good_qty / total_qty")
    grain TEXT,                    -- Aggregation level (e.g., 'day', 'line', 'product')
    description TEXT,
    variables TEXT,                -- JSON: variables used in expression
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (semantic_version_id) REFERENCES semantic_version(id)
);

-- ============================================================
-- 4️⃣ PHYSICAL_MAPPING
-- Maps logical definition to actual SQL implementation
-- This is where table names and physical schemas appear
-- ============================================================
CREATE TABLE physical_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    logical_definition_id INTEGER NOT NULL,
    engine_type TEXT NOT NULL,     -- sqlite, postgres, snowflake, etc.
    connection_ref TEXT NOT NULL,  -- Connection string reference
    sql_template TEXT NOT NULL,    -- Jinja2 template for SQL
    params_schema TEXT,            -- JSON: required parameters
    priority INTEGER DEFAULT 0,    -- For selecting between multiple mappings
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (logical_definition_id) REFERENCES logical_definition(id)
);

-- ============================================================
-- 5️⃣ ACCESS_POLICY
-- Runtime authorization control
-- Who can do what with which semantic objects
-- ============================================================
CREATE TABLE access_policy (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    semantic_object_id INTEGER NOT NULL,
    role TEXT NOT NULL,            -- e.g., 'operator', 'analyst', 'admin'
    action TEXT NOT NULL,          -- e.g., 'query', 'execute', 'export'
    condition TEXT,                -- JSON: additional conditions
    effect TEXT NOT NULL,          -- 'allow' or 'deny'
    priority INTEGER DEFAULT 0,    -- Higher priority policies evaluated first
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (semantic_object_id) REFERENCES semantic_object(id)
);

-- ============================================================
-- 6️⃣ EXECUTION_AUDIT
-- Complete decision trace for every execution
-- Enables replayability and accountability
-- ============================================================
CREATE TABLE execution_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    audit_id TEXT NOT NULL UNIQUE,  -- Human-readable ID
    question TEXT NOT NULL,         -- Original natural language question

    -- Decision chain
    semantic_object_id INTEGER,
    semantic_object_name TEXT,
    version_id INTEGER,
    version_name TEXT,
    logical_definition_id INTEGER,
    logical_expression TEXT,
    physical_mapping_id INTEGER,
    connection_ref TEXT,

    -- Execution details
    final_sql TEXT,
    decision_trace TEXT NOT NULL,  -- JSON: complete decision path
    request_params TEXT,           -- JSON: original request parameters
    execution_context TEXT,        -- JSON: execution context snapshot
    user_id INTEGER,
    user_role TEXT,
    policy_decision TEXT,          -- allow/deny with reason
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL,          -- success, denied, error
    row_count INTEGER,
    execution_time_ms INTEGER,
    error_message TEXT,

    FOREIGN KEY (semantic_object_id) REFERENCES semantic_object(id),
    FOREIGN KEY (version_id) REFERENCES semantic_version(id),
    FOREIGN KEY (logical_definition_id) REFERENCES logical_definition(id),
    FOREIGN KEY (physical_mapping_id) REFERENCES physical_mapping(id)
);

-- ============================================================
-- MOCK PHYSICAL DATA
-- Fact table for production records
-- ============================================================
CREATE TABLE fact_production_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_date DATE NOT NULL,
    line TEXT NOT NULL,
    product_id TEXT,
    good_qty INTEGER NOT NULL,
    rework_qty INTEGER DEFAULT 0,  -- Quantity after rework
    total_qty INTEGER NOT NULL,
    shift TEXT,  -- morning, afternoon, night
    operator_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- MOCK FINANCE DATA
-- Fact table for finance records (毛利率场景)
-- ============================================================
CREATE TABLE fact_finance_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    period TEXT NOT NULL,           -- e.g., '2026-01'
    region TEXT NOT NULL,           -- e.g., '华东', '华北'
    product_line TEXT,              -- e.g., 'ProductA'
    revenue DECIMAL(15,2) NOT NULL, -- 收入
    direct_cost DECIMAL(15,2) NOT NULL,   -- 直接成本
    indirect_cost DECIMAL(15,2) DEFAULT 0, -- 间接成本
    total_cost DECIMAL(15,2) NOT NULL,    -- 总成本 = direct_cost + indirect_cost
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- INDEXES for performance
-- ============================================================
CREATE INDEX idx_semantic_object_name ON semantic_object(name);
CREATE INDEX idx_semantic_object_domain ON semantic_object(domain);
CREATE INDEX idx_semantic_version_object ON semantic_version(semantic_object_id);
CREATE INDEX idx_semantic_version_active ON semantic_version(is_active);
CREATE INDEX idx_ontology_entity_domain ON ontology_entity(domain);
CREATE INDEX idx_ontology_dimension_entity ON ontology_dimension(entity_id);
CREATE INDEX idx_ontology_attribute_entity ON ontology_attribute(entity_id);
CREATE INDEX idx_ontology_relationship_from ON ontology_relationship(from_entity_id);
CREATE INDEX idx_ontology_relationship_to ON ontology_relationship(to_entity_id);
CREATE INDEX idx_metric_entity_map_metric ON metric_entity_map(metric_id);
CREATE INDEX idx_metric_entity_map_entity ON metric_entity_map(entity_id);
CREATE INDEX idx_metric_dependency_upstream ON metric_dependency(upstream_metric_id);
CREATE INDEX idx_metric_dependency_downstream ON metric_dependency(downstream_metric_id);
CREATE INDEX idx_metric_dependency_upstream_version ON metric_dependency(upstream_version_id);
CREATE INDEX idx_metric_dependency_downstream_version ON metric_dependency(downstream_version_id);
CREATE INDEX idx_term_dictionary_term ON term_dictionary(term);
CREATE INDEX idx_logical_definition_version ON logical_definition(semantic_version_id);
CREATE INDEX idx_physical_mapping_logical ON physical_mapping(logical_definition_id);
CREATE INDEX idx_physical_mapping_engine ON physical_mapping(engine_type);
CREATE INDEX idx_access_policy_object_role ON access_policy(semantic_object_id, role);
CREATE INDEX idx_execution_audit_id ON execution_audit(audit_id);
CREATE INDEX idx_execution_audit_user ON execution_audit(user_id);
CREATE INDEX idx_execution_audit_date ON execution_audit(executed_at);

-- ============================================================
-- FACT PRODUCTION RECORDS INDEXES
-- ============================================================
CREATE INDEX idx_fact_records_date ON fact_production_records(record_date);
CREATE INDEX idx_fact_records_line ON fact_production_records(line);
CREATE INDEX idx_fact_records_date_line ON fact_production_records(record_date, line);

-- ============================================================
-- FACT FINANCE RECORDS INDEXES
-- ============================================================
CREATE INDEX idx_fact_finance_period ON fact_finance_records(period);
CREATE INDEX idx_fact_finance_region ON fact_finance_records(region);
CREATE INDEX idx_fact_finance_period_region ON fact_finance_records(period, region);
