"""
Impact analysis and metric dependency DAG utilities.
"""

from typing import Dict, Any, List, Tuple, Set, Optional

from .interfaces import MetadataStore


Node = Tuple[str, int]  # (type, id)


class ImpactAnalyzer:
    def __init__(self, metadata_store: MetadataStore):
        self.metadata_store = metadata_store

    def build_dependency_graph(self) -> Dict[Node, Set[Node]]:
        edges: Dict[Node, Set[Node]] = {}

        def add_edge(src: Node, dst: Node) -> None:
            if src not in edges:
                edges[src] = set()
            edges[src].add(dst)

        # Metric -> Entity/Dimension/Attribute/Mapping
        metric_entity_maps = self.metadata_store.list_metric_entity_maps()
        for mem in metric_entity_maps:
            metric_node = ("metric", mem.metric_id)
            entity_node = ("entity", mem.entity_id)
            add_edge(metric_node, entity_node)

            dims = self.metadata_store.list_dimensions_by_entity(mem.entity_id)
            attrs = self.metadata_store.list_attributes_by_entity(mem.entity_id)

            allowed_dim_names = set(mem.allowed_dimensions or [])
            for dim in dims:
                if not allowed_dim_names or dim.name in allowed_dim_names:
                    add_edge(metric_node, ("dimension", dim.id))

            for attr in attrs:
                add_edge(metric_node, ("attribute", attr.id))

        # Metric -> Mapping (via versions and logical definitions)
        for metric in self.metadata_store.list_active_semantic_objects():
            versions = self.metadata_store.get_versions_for_object(metric.id)
            for version in versions:
                logical_def = self.metadata_store.get_logical_definition(version.id)
                if not logical_def:
                    continue
                mappings = self.metadata_store.get_physical_mappings(logical_def.id)
                for mapping in mappings:
                    add_edge(("metric", metric.id), ("mapping", mapping.id))

        # Metric dependencies (downstream depends on upstream)
        for dep in self.metadata_store.list_metric_dependencies():
            downstream_node = ("metric_version", dep.downstream_version_id or dep.downstream_metric_id)
            upstream_node = ("metric_version", dep.upstream_version_id or dep.upstream_metric_id)
            add_edge(downstream_node, upstream_node)
            add_edge(("metric", dep.downstream_metric_id), ("metric", dep.upstream_metric_id))

        return edges

    def impact(self, target_type: str, target_id: int) -> Dict[str, Any]:
        edges = self.build_dependency_graph()
        reverse_edges: Dict[Node, Set[Node]] = {}

        for src, dsts in edges.items():
            for dst in dsts:
                reverse_edges.setdefault(dst, set()).add(src)

        start = (target_type, target_id)
        visited: Set[Node] = set()
        stack: List[Node] = [start]

        while stack:
            node = stack.pop()
            if node in visited:
                continue
            visited.add(node)
            for parent in reverse_edges.get(node, set()):
                if parent not in visited:
                    stack.append(parent)

        impacted_metrics = sorted({n[1] for n in visited if n[0] == "metric"})
        impacted_mappings = sorted({n[1] for n in visited if n[0] == "mapping"})
        impacted_entities = sorted({n[1] for n in visited if n[0] == "entity"})
        impacted_dimensions = sorted({n[1] for n in visited if n[0] == "dimension"})
        impacted_attributes = sorted({n[1] for n in visited if n[0] == "attribute"})

        return {
            "target": {"type": target_type, "id": target_id},
            "impacted_metrics": impacted_metrics,
            "impacted_mappings": impacted_mappings,
            "impacted_entities": impacted_entities,
            "impacted_dimensions": impacted_dimensions,
            "impacted_attributes": impacted_attributes
        }

    def diff(self, metric_name: str, version_a: str, version_b: str) -> Dict[str, Any]:
        metric = self.metadata_store.get_semantic_object_by_name(metric_name)
        if not metric:
            raise ValueError(f"Metric not found: {metric_name}")

        versions = self.metadata_store.get_versions_for_object(metric.id)
        version_map = {v.version_name: v for v in versions}
        if version_a not in version_map or version_b not in version_map:
            raise ValueError("Version not found for metric")

        v_a = version_map[version_a]
        v_b = version_map[version_b]

        logical_a = self.metadata_store.get_logical_definition(v_a.id)
        logical_b = self.metadata_store.get_logical_definition(v_b.id)

        def mapping_fingerprint(version_id: int) -> Optional[Dict[str, Any]]:
            logical_def = self.metadata_store.get_logical_definition(version_id)
            if not logical_def:
                return None
            mappings = self.metadata_store.get_physical_mappings(logical_def.id)
            if not mappings:
                return None
            mapping = mappings[0]
            return {
                "sql_template": mapping.sql_template,
                "params_schema": mapping.params_schema
            }

        diff_summary = {
            "metric": metric.name,
            "version_a": version_a,
            "version_b": version_b,
            "logical_change": {},
            "mapping_change": {},
            "risk": "L1"
        }

        if logical_a and logical_b:
            diff_summary["logical_change"] = {
                "expression_changed": logical_a.expression != logical_b.expression,
                "variables_changed": logical_a.variables != logical_b.variables,
                "grain_changed": logical_a.grain != logical_b.grain
            }

        map_a = mapping_fingerprint(v_a.id)
        map_b = mapping_fingerprint(v_b.id)
        if map_a and map_b:
            diff_summary["mapping_change"] = {
                "sql_changed": map_a["sql_template"] != map_b["sql_template"],
                "params_changed": map_a["params_schema"] != map_b["params_schema"]
            }

        # Risk evaluation (simple heuristic)
        logical_changed = any(diff_summary["logical_change"].values()) if diff_summary["logical_change"] else False
        mapping_changed = any(diff_summary["mapping_change"].values()) if diff_summary["mapping_change"] else False

        if logical_changed and mapping_changed:
            diff_summary["risk"] = "L3"
        elif logical_changed or mapping_changed:
            diff_summary["risk"] = "L2"

        return diff_summary

    def generate_report(self, metric_name: str, version_a: str, version_b: str) -> Dict[str, Any]:
        diff = self.diff(metric_name, version_a, version_b)
        metric = self.metadata_store.get_semantic_object_by_name(metric_name)
        if not metric:
            raise ValueError(f"Metric not found: {metric_name}")

        impact = self.impact("metric", metric.id)
        risk = diff.get("risk", "L1")

        versions = self.metadata_store.get_versions_for_object(metric.id)
        version_map = {v.version_name: v for v in versions}
        if version_a not in version_map or version_b not in version_map:
            raise ValueError("Version not found for metric")
        v_a = version_map[version_a]
        v_b = version_map[version_b]

        report = {
            "summary": {
                "metric": metric_name,
                "version_a": version_a,
                "version_b": version_b,
                "version_a_id": v_a.id,
                "version_b_id": v_b.id,
                "risk": risk
            },
            "diff": diff,
            "impact": impact,
            "actions": self._suggest_actions(risk),
            "evidence": self._build_evidence(metric_name, v_a.id, v_b.id)
        }

        report["markdown"] = self._to_markdown(report)
        return report

    def _suggest_actions(self, risk: str) -> List[str]:
        if risk == "L3":
            return [
                "Business owner approval required",
                "Prepare rollback plan",
                "Run shadow queries for validation"
            ]
        if risk == "L2":
            return [
                "Data owner approval required",
                "Run regression queries"
            ]
        return ["Safe to release"]

    def _build_evidence(self, metric_name: str, version_a_id: int, version_b_id: int) -> Dict[str, Any]:
        # Evidence: audit query template + sample queries
        audit_query = (
            "SELECT audit_id, question, version_name, status, executed_at "
            "FROM execution_audit "
            "WHERE semantic_object_name = :metric_name "
            "ORDER BY executed_at DESC LIMIT 10;"
        )
        sample_queries = [
            {
                "name": "baseline_query",
                "sql": (
                    "SELECT * FROM execution_audit "
                    "WHERE semantic_object_name = :metric_name "
                    "ORDER BY executed_at DESC LIMIT 5;"
                )
            }
        ]
        return {
            "audit_query": audit_query,
            "sample_queries": sample_queries,
            "params": {
                "metric_name": metric_name,
                "version_a_id": version_a_id,
                "version_b_id": version_b_id
            }
        }

    def _to_markdown(self, report: Dict[str, Any]) -> str:
        summary = report["summary"]
        impact = report["impact"]
        actions = report["actions"]
        evidence = report.get("evidence", {})

        lines = [
            "# Impact Report",
            f"- Metric: {summary['metric']}",
            f"- Version A: {summary['version_a']}",
            f"- Version B: {summary['version_b']}",
            f"- Risk: {summary['risk']}",
            "",
            "## Impact Scope",
            f"- Metrics: {impact['impacted_metrics']}",
            f"- Mappings: {impact['impacted_mappings']}",
            f"- Entities: {impact['impacted_entities']}",
            f"- Dimensions: {impact['impacted_dimensions']}",
            f"- Attributes: {impact['impacted_attributes']}",
            "",
            "## Recommended Actions",
        ]
        lines.extend([f"- {action}" for action in actions])
        if evidence:
            lines.extend([
                "",
                "## Evidence",
                f"- Audit query: `{evidence.get('audit_query')}`"
            ])
        return "\n".join(lines)
