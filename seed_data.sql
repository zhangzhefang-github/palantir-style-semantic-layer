-- ============================================================
-- Palantir-Style Semantic Control Plane
-- Seed Data for POC
-- ============================================================

-- ============================================================
-- 1️⃣ SEMANTIC_OBJECTS
-- Business concepts available in the system
-- ============================================================
INSERT INTO semantic_object (name, description, aliases, domain, status) VALUES
(
    'FPY',
    'First Pass Yield - 一次合格率，衡量产品质量的关键指标',
    '["一次合格率", "First Pass Yield", "直通率", "FPY", "良率"]',
    'production',
    'active'
),
(
    'OutputQty',
    'Output Quantity - 产量，完成的产品数量',
    '["产量", "产出数量", "Output Qty", "Output Quantity", "生产量"]',
    'production',
    'active'
),
(
    'DefectRate',
    'Defect Rate - 不良率，缺陷产品占比',
    '["不良率", "次品率", "Defect Rate", "缺陷率"]',
    'quality',
    'active'
),
(
    'QualityScore',
    'Quality Score - 综合质量指标（示例）',
    '["质量评分", "Quality Score", "Quality KPI", "综合质量"]',
    'quality',
    'active'
),
(
    'GrossMargin',
    'Gross Margin - 毛利率，衡量盈利能力的关键指标',
    '["毛利率", "毛利", "Gross Margin", "GP Margin", "利润率"]',
    'finance',
    'active'
);

-- ============================================================
-- 2️⃣ SEMANTIC VERSIONS
-- Different calculation versions for scenario handling
-- ============================================================
-- FPY Version 1: Standard calculation
INSERT INTO semantic_version (semantic_object_id, version_name, effective_from, scenario_condition, is_active, priority, description) VALUES
(1, 'FPY_v1_standard', '2024-01-01 00:00:00', NULL, 1, 0, '标准FPY计算：良品数/总数');

-- FPY Version 2: Adjusted for rework scenario
INSERT INTO semantic_version (semantic_object_id, version_name, effective_from, scenario_condition, is_active, priority, description) VALUES
(1, 'FPY_v2_rework', '2024-06-01 00:00:00', '{"rework_enabled": true}', 1, 10, '包含返工的FPY计算（调整后公式）');

-- OutputQty Version 1
INSERT INTO semantic_version (semantic_object_id, version_name, effective_from, scenario_condition, is_active, priority, description) VALUES
(2, 'OutputQty_v1', '2024-01-01 00:00:00', NULL, 1, 0, '标准产量计算');

-- DefectRate Version 1
INSERT INTO semantic_version (semantic_object_id, version_name, effective_from, scenario_condition, is_active, priority, description) VALUES
(3, 'DefectRate_v1', '2024-01-01 00:00:00', NULL, 1, 0, '标准不良率计算');

-- QualityScore Version 1
INSERT INTO semantic_version (semantic_object_id, version_name, effective_from, scenario_condition, is_active, priority, description) VALUES
(4, 'QualityScore_v1', '2024-01-01 00:00:00', NULL, 1, 0, '综合质量指标：0.7*FPY + 0.3*(1-DefectRate)');

-- GrossMargin Version 1: Finance department calculation (conservative)
INSERT INTO semantic_version (semantic_object_id, version_name, effective_from, scenario_condition, is_active, priority, description) VALUES
(5, 'GrossMargin_v1_finance', '2024-01-01 00:00:00', '{"department": "finance"}', 1, 10, '财务部口径：(收入-总成本)/收入，含所有成本项');

-- GrossMargin Version 2: Sales department calculation (optimistic)
INSERT INTO semantic_version (semantic_object_id, version_name, effective_from, scenario_condition, is_active, priority, description) VALUES
(5, 'GrossMargin_v2_sales', '2024-01-01 00:00:00', '{"department": "sales"}', 1, 10, '销售部口径：(收入-直接成本)/收入，不含间接费用');

-- GrossMargin Version 3: Default (no department specified)
INSERT INTO semantic_version (semantic_object_id, version_name, effective_from, scenario_condition, is_active, priority, description) VALUES
(5, 'GrossMargin_v0_default', '2024-01-01 00:00:00', NULL, 1, 0, '默认口径：标准毛利率计算');

-- ============================================================
-- 3️⃣ LOGICAL DEFINITIONS
-- Pure business formulas, no physical details
-- ============================================================
-- FPY: good_qty / total_qty
INSERT INTO logical_definition (semantic_version_id, expression, grain, description, variables) VALUES
(1, 'good_qty / total_qty', 'line,day', '良品数量除以总数量', '["good_qty", "total_qty"]');

-- FPY v2 (rework): (good_qty + rework_qty) / total_qty
INSERT INTO logical_definition (semantic_version_id, expression, grain, description, variables) VALUES
(2, '(good_qty + rework_qty) / total_qty', 'line,day', '包含返工的FPY： (良品+返工品)/总数', '["good_qty", "rework_qty", "total_qty"]');

-- OutputQty: SUM(good_qty)
INSERT INTO logical_definition (semantic_version_id, expression, grain, description, variables) VALUES
(3, 'SUM(good_qty)', 'line,day', '良品数量汇总', '["good_qty"]');

-- DefectRate: (total_qty - good_qty) / total_qty
INSERT INTO logical_definition (semantic_version_id, expression, grain, description, variables) VALUES
(4, '(total_qty - good_qty) / total_qty', 'line,day', '不良数量除以总数量', '["total_qty", "good_qty"]');

-- QualityScore: 0.7*FPY + 0.3*(1-DefectRate)
INSERT INTO logical_definition (semantic_version_id, expression, grain, description, variables) VALUES
(5, '0.7*{{ metric:FPY }} + 0.3*(1-{{ metric:DefectRate }})', 'line,day', '综合质量指标（示例）', '["FPY", "DefectRate"]');

-- GrossMargin v1 (Finance): (revenue - total_cost) / revenue
INSERT INTO logical_definition (semantic_version_id, expression, grain, description, variables) VALUES
(6, '(revenue - total_cost) / revenue', 'region,month', '财务口径毛利率：(收入-总成本)/收入', '["revenue", "total_cost"]');

-- GrossMargin v2 (Sales): (revenue - direct_cost) / revenue
INSERT INTO logical_definition (semantic_version_id, expression, grain, description, variables) VALUES
(7, '(revenue - direct_cost) / revenue', 'region,month', '销售口径毛利率：(收入-直接成本)/收入', '["revenue", "direct_cost"]');

-- GrossMargin v0 (Default): same as finance
INSERT INTO logical_definition (semantic_version_id, expression, grain, description, variables) VALUES
(8, '(revenue - total_cost) / revenue', 'region,month', '默认口径毛利率', '["revenue", "total_cost"]');

-- ============================================================
-- 4️⃣ PHYSICAL MAPPINGS
-- Map logical definitions to actual SQL implementations
-- ============================================================
-- FPY SQLite mapping
INSERT INTO physical_mapping (logical_definition_id, engine_type, connection_ref, sql_template, params_schema, priority, description) VALUES
(1, 'sqlite', 'default',
'
SELECT
    SUM(CAST(good_qty AS REAL)) / SUM(CAST(total_qty AS REAL)) AS fpy
FROM fact_production_records
WHERE line = :line
  AND record_date BETWEEN :start_date AND :end_date
',
'{"line": "string", "start_date": "date", "end_date": "date"}',
1,
'SQLite implementation for FPY calculation'
);

-- OutputQty SQLite mapping
INSERT INTO physical_mapping (logical_definition_id, engine_type, connection_ref, sql_template, params_schema, priority, description) VALUES
(3, 'sqlite', 'default',
'
SELECT
    SUM(good_qty) AS output_qty
FROM fact_production_records
WHERE line = :line
  AND record_date BETWEEN :start_date AND :end_date
',
'{"line": "string", "start_date": "date", "end_date": "date"}',
1,
'SQLite implementation for OutputQty calculation'
);

-- DefectRate SQLite mapping
INSERT INTO physical_mapping (logical_definition_id, engine_type, connection_ref, sql_template, params_schema, priority, description) VALUES
(4, 'sqlite', 'default',
'
SELECT
    SUM(CAST(total_qty AS REAL) - CAST(good_qty AS REAL)) / SUM(CAST(total_qty AS REAL)) AS defect_rate
FROM fact_production_records
WHERE line = :line
  AND record_date BETWEEN :start_date AND :end_date
',
'{"line": "string", "start_date": "date", "end_date": "date"}',
1,
'SQLite implementation for DefectRate calculation'
);

-- FPY v2 (rework) SQLite mapping
INSERT INTO physical_mapping (logical_definition_id, engine_type, connection_ref, sql_template, params_schema, priority, description) VALUES
(2, 'sqlite', 'default',
'
SELECT
    SUM(CAST(good_qty + rework_qty AS REAL)) / SUM(CAST(total_qty AS REAL)) AS fpy
FROM fact_production_records
WHERE line = :line
  AND record_date BETWEEN :start_date AND :end_date
',
'{"line": "string", "start_date": "date", "end_date": "date"}',
2,
'SQLite implementation for FPY v2 with rework calculation'
);

-- QualityScore SQLite mapping (composite KPI)
INSERT INTO physical_mapping (logical_definition_id, engine_type, connection_ref, sql_template, params_schema, priority, description) VALUES
(5, 'sqlite', 'default',
'
WITH agg AS (
    SELECT
        SUM(CAST(good_qty AS REAL)) AS good_qty,
        SUM(CAST(total_qty AS REAL)) AS total_qty
    FROM fact_production_records
    WHERE line = :line
      AND record_date BETWEEN :start_date AND :end_date
),
calc AS (
    SELECT
        good_qty / total_qty AS fpy,
        (total_qty - good_qty) / total_qty AS defect_rate
    FROM agg
)
SELECT
    (0.7 * fpy + 0.3 * (1 - defect_rate)) AS quality_score,
    fpy,
    defect_rate
FROM calc
',
'{"line": "string", "start_date": "date", "end_date": "date"}',
1,
'SQLite implementation for QualityScore composite KPI'
);

-- GrossMargin v1 (Finance) SQLite mapping
INSERT INTO physical_mapping (logical_definition_id, engine_type, connection_ref, sql_template, params_schema, priority, description) VALUES
(6, 'sqlite', 'default',
'
SELECT
    (SUM(CAST(revenue AS REAL)) - SUM(CAST(total_cost AS REAL))) / SUM(CAST(revenue AS REAL)) AS gross_margin
FROM fact_finance_records
WHERE region = :region
  AND period = :period
',
'{"region": "string", "period": "string"}',
2,
'SQLite implementation for GrossMargin (Finance口径)'
);

-- GrossMargin v2 (Sales) SQLite mapping
INSERT INTO physical_mapping (logical_definition_id, engine_type, connection_ref, sql_template, params_schema, priority, description) VALUES
(7, 'sqlite', 'default',
'
SELECT
    (SUM(CAST(revenue AS REAL)) - SUM(CAST(direct_cost AS REAL))) / SUM(CAST(revenue AS REAL)) AS gross_margin
FROM fact_finance_records
WHERE region = :region
  AND period = :period
',
'{"region": "string", "period": "string"}',
2,
'SQLite implementation for GrossMargin (Sales口径)'
);

-- GrossMargin v0 (Default) SQLite mapping
INSERT INTO physical_mapping (logical_definition_id, engine_type, connection_ref, sql_template, params_schema, priority, description) VALUES
(8, 'sqlite', 'default',
'
SELECT
    (SUM(CAST(revenue AS REAL)) - SUM(CAST(total_cost AS REAL))) / SUM(CAST(revenue AS REAL)) AS gross_margin
FROM fact_finance_records
WHERE region = :region
  AND period = :period
',
'{"region": "string", "period": "string"}',
1,
'SQLite implementation for GrossMargin (Default)'
);


-- ============================================================
-- 5️⃣ ACCESS POLICIES
-- Runtime authorization rules
-- ============================================================
-- Operators can query FPY
INSERT INTO access_policy (semantic_object_id, role, action, condition, effect, priority) VALUES
(1, 'operator', 'query', NULL, 'allow', 1);

-- Operators can query OutputQty
INSERT INTO access_policy (semantic_object_id, role, action, condition, effect, priority) VALUES
(2, 'operator', 'query', NULL, 'allow', 1);

-- Operators can query DefectRate
INSERT INTO access_policy (semantic_object_id, role, action, condition, effect, priority) VALUES
(3, 'operator', 'query', NULL, 'allow', 1);

-- Operators can query QualityScore
INSERT INTO access_policy (semantic_object_id, role, action, condition, effect, priority) VALUES
(4, 'operator', 'query', NULL, 'allow', 1);

-- Finance managers can query GrossMargin
INSERT INTO access_policy (semantic_object_id, role, action, condition, effect, priority) VALUES
(5, 'finance_manager', 'query', NULL, 'allow', 1);

-- Sales managers can query GrossMargin
INSERT INTO access_policy (semantic_object_id, role, action, condition, effect, priority) VALUES
(5, 'sales_manager', 'query', NULL, 'allow', 1);

-- Operators can query GrossMargin (default)
INSERT INTO access_policy (semantic_object_id, role, action, condition, effect, priority) VALUES
(5, 'operator', 'query', NULL, 'allow', 1);

-- ============================================================
-- 5️⃣.1 ONTOLOGY SEED DATA
-- ============================================================
INSERT INTO ontology_entity (name, description, domain, status) VALUES
('ProductionLine', '生产线实体', 'production', 'active'),
('ProductionRecord', '生产记录实体', 'production', 'active');

INSERT INTO ontology_dimension (entity_id, name, description, data_type, status) VALUES
(1, 'line', '产线标识', 'string', 'active'),
(2, 'record_date', '记录日期', 'date', 'active');

INSERT INTO ontology_attribute (entity_id, name, description, data_type, is_key, status) VALUES
(2, 'good_qty', '良品数量', 'number', 0, 'active'),
(2, 'total_qty', '总数量', 'number', 0, 'active'),
(2, 'rework_qty', '返工数量', 'number', 0, 'active');

INSERT INTO ontology_relationship (from_entity_id, to_entity_id, relationship_type, description, cardinality, status) VALUES
(1, 2, 'has_many', '一条产线包含多条生产记录', '1:N', 'active');

-- ============================================================
-- 5️⃣.2 METRIC ENTITY MAP
-- ============================================================
INSERT INTO metric_entity_map (metric_id, entity_id, grain_level, allowed_dimensions, forbidden_dimensions, join_path_policy) VALUES
(1, 2, 'line,day', '["line", "record_date"]', '[]', 'single_entity'),  -- FPY -> ProductionRecord
(2, 2, 'line,day', '["line", "record_date"]', '[]', 'single_entity'),  -- OutputQty
(3, 2, 'line,day', '["line", "record_date"]', '[]', 'single_entity'),  -- DefectRate
(4, 2, 'line,day', '["line", "record_date"]', '[]', 'single_entity');  -- QualityScore

-- ============================================================
-- 5️⃣.3 METRIC DEPENDENCY (DAG)
-- ============================================================
INSERT INTO metric_dependency (upstream_metric_id, downstream_metric_id, upstream_version_id, downstream_version_id, dependency_type, description) VALUES
(1, 4, 1, 5, 'logical', 'QualityScore depends on FPY'),
(3, 4, 4, 5, 'logical', 'QualityScore depends on DefectRate');

-- ============================================================
-- 5️⃣.3 TERM DICTIONARY (LIGHTWEIGHT)
-- ============================================================
INSERT INTO term_dictionary (term, normalized_term, object_type, object_id, language, status) VALUES
('质量评分', 'QualityScore', 'semantic_object', 4, 'zh', 'active'),
('质量 KPI', 'QualityScore', 'semantic_object', 4, 'zh', 'active'),
('产线', 'ProductionLine', 'entity', 1, 'zh', 'active'),
('生产记录', 'ProductionRecord', 'entity', 2, 'zh', 'active');

-- Deny non-authenticated users
INSERT INTO access_policy (semantic_object_id, role, action, condition, effect, priority) VALUES
(1, 'anonymous', 'query', NULL, 'deny', 100);

-- Analysts can export data (example for future use)
INSERT INTO access_policy (semantic_object_id, role, action, condition, effect, priority) VALUES
(1, 'analyst', 'export', NULL, 'allow', 1);

-- ============================================================
-- MOCK FINANCE DATA (for GrossMargin scenario)
-- 数据设计使得：
--   财务口径 (revenue-total_cost)/revenue = 23.5%
--   销售口径 (revenue-direct_cost)/revenue = 28.2%
-- ============================================================
INSERT INTO fact_finance_records (period, region, product_line, revenue, direct_cost, indirect_cost, total_cost) VALUES
-- 2026-01 华东区数据 (与 PPT 一致: 财务 23.5%, 销售 28.2%)
('2026-01', '华东', 'ProductA', 1000000, 718000, 47000, 765000),
('2026-01', '华东', 'ProductB', 800000, 574400, 37600, 612000),
('2026-01', '华东', 'ProductC', 600000, 430800, 28200, 459000),
-- 2026-01 华北区数据
('2026-01', '华北', 'ProductA', 900000, 646200, 42300, 688500),
('2026-01', '华北', 'ProductB', 700000, 502600, 32900, 535500),
-- 2025-12 华东区数据（上月）
('2025-12', '华东', 'ProductA', 950000, 682100, 44650, 726750),
('2025-12', '华东', 'ProductB', 750000, 538500, 35250, 573750);

-- ============================================================
-- MOCK PRODUCTION DATA
-- Fact table records for testing
-- ============================================================
INSERT INTO fact_production_records (record_date, line, product_id, good_qty, rework_qty, total_qty, shift, operator_id) VALUES
-- Yesterday's data for Line A
('2026-01-27', 'A', 'PROD001', 950, 30, 1000, 'morning', 1),
('2026-01-27', 'A', 'PROD001', 980, 15, 1000, 'afternoon', 2),
('2026-01-27', 'A', 'PROD002', 960, 25, 1000, 'night', 3),
-- Today's data for Line A
('2026-01-28', 'A', 'PROD001', 970, 20, 1000, 'morning', 1),
('2026-01-28', 'A', 'PROD001', 975, 18, 1000, 'afternoon', 2),
-- Yesterday's data for Line B
('2026-01-27', 'B', 'PROD001', 920, 40, 1000, 'morning', 4),
('2026-01-27', 'B', 'PROD002', 940, 30, 1000, 'afternoon', 5),
('2026-01-27', 'B', 'PROD003', 965, 20, 1000, 'night', 6),
-- Today's data for Line B
('2026-01-28', 'B', 'PROD001', 930, 35, 1000, 'morning', 4),
('2026-01-28', 'B', 'PROD002', 950, 28, 1000, 'afternoon', 5);

-- ============================================================
-- Verify data insertion
-- ============================================================
SELECT 'Semantic Objects:' as info;
SELECT id, name, domain, status FROM semantic_object;

SELECT 'Semantic Versions:' as info;
SELECT sv.id, so.name as semantic_name, sv.version_name, sv.is_active
FROM semantic_version sv
JOIN semantic_object so ON sv.semantic_object_id = so.id;

SELECT 'Logical Definitions:' as info;
SELECT ld.id, so.name as semantic_name, ld.expression, ld.grain
FROM logical_definition ld
JOIN semantic_version sv ON ld.semantic_version_id = sv.id
JOIN semantic_object so ON sv.semantic_object_id = so.id;

SELECT 'Physical Mappings:' as info;
SELECT pm.id, so.name as semantic_name, pm.engine_type, pm.priority
FROM physical_mapping pm
JOIN logical_definition ld ON pm.logical_definition_id = ld.id
JOIN semantic_version sv ON ld.semantic_version_id = sv.id
JOIN semantic_object so ON sv.semantic_object_id = so.id;

SELECT 'Access Policies:' as info;
SELECT ap.id, so.name as semantic_name, ap.role, ap.action, ap.effect
FROM access_policy ap
JOIN semantic_object so ON ap.semantic_object_id = so.id;

SELECT 'Production Records (sample):' as info;
SELECT record_date, line, product_id, good_qty, total_qty,
    ROUND(CAST(good_qty AS REAL) / total_qty, 3) as shift_fpy
FROM fact_production_records
ORDER BY record_date DESC, line, shift
LIMIT 5;
