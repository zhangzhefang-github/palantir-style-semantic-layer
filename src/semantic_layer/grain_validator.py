"""
Grain validation for metrics based on metric_entity_map.
"""

from typing import Dict, Any, List

from .interfaces import MetadataStore


class GrainValidator:
    def __init__(self, metadata_store: MetadataStore):
        self.metadata_store = metadata_store

    def validate(self, metric_id: int, parameters: Dict[str, Any], metric_grain: str) -> Dict[str, Any]:
        requested_dimensions = self._get_requested_dimensions(parameters)
        requested_grain = parameters.get("grain")

        maps = [m for m in self.metadata_store.list_metric_entity_maps() if m.metric_id == metric_id]
        if not maps:
            return {"status": "WARN", "reason": "No metric_entity_map defined", "action": "SUGGEST"}

        mapping = maps[0]
        allowed = set(mapping.allowed_dimensions or [])
        forbidden = set(mapping.forbidden_dimensions or [])

        if requested_dimensions:
            if allowed and not set(requested_dimensions).issubset(allowed):
                return {
                    "status": "FAIL",
                    "reason": f"Requested dimensions not allowed: {requested_dimensions}",
                    "action": "REFUSE",
                    "suggestions": {
                        "allowed_dimensions": sorted(list(allowed))
                    }
                }
            if set(requested_dimensions) & forbidden:
                return {
                    "status": "FAIL",
                    "reason": f"Requested dimensions forbidden: {requested_dimensions}",
                    "action": "REFUSE",
                    "suggestions": {
                        "allowed_dimensions": sorted(list(allowed))
                    }
                }

        if requested_grain:
            metric_grain_set = {g.strip() for g in metric_grain.split(",") if g.strip()}
            requested_grain_set = {g.strip() for g in requested_grain.split(",") if g.strip()}
            if not requested_grain_set.issubset(metric_grain_set):
                return {
                    "status": "FAIL",
                    "reason": f"Requested grain finer than metric grain: {requested_grain}",
                    "action": "REFUSE",
                    "suggestions": {
                        "recommended_grain": metric_grain
                    }
                }

        return {"status": "PASS", "reason": "Grain validation passed", "action": "PASS"}

    def _get_requested_dimensions(self, parameters: Dict[str, Any]) -> List[str]:
        dims = parameters.get("dimensions") or parameters.get("group_by")
        if not dims:
            return []
        if isinstance(dims, str):
            return [d.strip() for d in dims.split(",") if d.strip()]
        return list(dims)
