"""
Dependency builder for metric DAG based on logical definition parsing.
"""

import re
from typing import List, Dict, Set, Tuple

from .interfaces import MetadataStore
from .models import MetricDependency


class DependencyBuilder:
    METRIC_REF_PATTERN = re.compile(r"\{\{\s*metric:([A-Za-z0-9_]+)\s*\}\}")
    DBT_REF_PATTERN = re.compile(r"ref\(\s*[\"']([A-Za-z0-9_]+)[\"']\s*\)")

    def __init__(self, metadata_store: MetadataStore):
        self.metadata_store = metadata_store

    def _extract_metric_names(self, expression: str) -> List[str]:
        names = set(self.METRIC_REF_PATTERN.findall(expression))
        names.update(self.DBT_REF_PATTERN.findall(expression))
        return list(names)

    def build_dependencies(
        self,
        metric_name: str,
        version_name: str
    ) -> List[MetricDependency]:
        metric = self.metadata_store.get_semantic_object_by_name(metric_name)
        if not metric:
            raise ValueError(f"Metric not found: {metric_name}")

        versions = self.metadata_store.get_versions_for_object(metric.id)
        version_map = {v.version_name: v for v in versions}
        if version_name not in version_map:
            raise ValueError("Version not found for metric")

        version = version_map[version_name]
        logical_def = self.metadata_store.get_logical_definition(version.id)
        if not logical_def:
            raise ValueError("Logical definition not found for version")

        metric_names = self._extract_metric_names(logical_def.expression)
        dependencies: List[MetricDependency] = []

        for name in metric_names:
            upstream_metric = self.metadata_store.get_semantic_object_by_name(name)
            if not upstream_metric:
                # Fail-closed: unresolved dependency
                raise ValueError(f"Unresolved metric reference: {name}")

            upstream_versions = self.metadata_store.get_versions_for_object(upstream_metric.id)
            if not upstream_versions:
                raise ValueError(f"No versions found for upstream metric: {name}")

            upstream_version = upstream_versions[0]
            dependencies.append(
                MetricDependency(
                    id=0,
                    upstream_metric_id=upstream_metric.id,
                    downstream_metric_id=metric.id,
                    upstream_version_id=upstream_version.id,
                    downstream_version_id=version.id,
                    dependency_type="logical",
                    description=f"{metric.name} depends on {upstream_metric.name}"
                )
            )

        return dependencies

    def rebuild_all(self) -> None:
        metrics = self.metadata_store.list_active_semantic_objects()
        for metric in metrics:
            versions = self.metadata_store.get_versions_for_object(metric.id)
            for version in versions:
                logical_def = self.metadata_store.get_logical_definition(version.id)
                if not logical_def:
                    continue
                deps = self.build_dependencies(metric.name, version.version_name)
                self.metadata_store.replace_metric_dependencies_for_version(
                    downstream_metric_id=metric.id,
                    downstream_version_id=version.id,
                    dependencies=deps
                )
        cycles = self.detect_cycles()
        if cycles:
            raise ValueError(f"Dependency cycles detected: {cycles}")

    def rebuild_for_metric(self, metric_name: str) -> None:
        metric = self.metadata_store.get_semantic_object_by_name(metric_name)
        if not metric:
            raise ValueError(f"Metric not found: {metric_name}")
        versions = self.metadata_store.get_versions_for_object(metric.id)
        for version in versions:
            logical_def = self.metadata_store.get_logical_definition(version.id)
            if not logical_def:
                continue
            deps = self.build_dependencies(metric.name, version.version_name)
            self.metadata_store.replace_metric_dependencies_for_version(
                downstream_metric_id=metric.id,
                downstream_version_id=version.id,
                dependencies=deps
            )
        cycles = self.detect_cycles()
        if cycles:
            raise ValueError(f"Dependency cycles detected: {cycles}")

    def detect_cycles(self) -> List[List[Tuple[int, int]]]:
        deps = self.metadata_store.list_metric_dependencies()
        graph: Dict[Tuple[int, int], List[Tuple[int, int]]] = {}

        for dep in deps:
            downstream = (dep.downstream_metric_id, dep.downstream_version_id or 0)
            upstream = (dep.upstream_metric_id, dep.upstream_version_id or 0)
            graph.setdefault(downstream, []).append(upstream)

        visited: Set[Tuple[int, int]] = set()
        stack: Set[Tuple[int, int]] = set()
        cycles: List[List[Tuple[int, int]]] = []

        def dfs(node: Tuple[int, int], path: List[Tuple[int, int]]) -> None:
            visited.add(node)
            stack.add(node)
            path.append(node)

            for nxt in graph.get(node, []):
                if nxt not in visited:
                    dfs(nxt, path)
                elif nxt in stack:
                    cycle_start = path.index(nxt)
                    cycles.append(path[cycle_start:].copy())

            stack.remove(node)
            path.pop()

        for n in graph.keys():
            if n not in visited:
                dfs(n, [])

        return cycles
