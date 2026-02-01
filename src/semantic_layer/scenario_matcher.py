"""
Scenario Matcher

Evaluates scenario conditions for semantic version selection.
Implements precise matching logic with explainable scores.
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ScenarioMatchResult:
    """Result of scenario matching for a single version."""
    version_id: int
    version_name: str
    score: int
    reason: str
    is_time_effective: bool
    matches_scenario: bool


class ScenarioMatcher:
    """
    Matches semantic versions based on scenario conditions and time effectiveness.

    Matching priority:
    1. Scenario match (all keys match) + time effective → score = 2
    2. No scenario condition + time effective → score = 1 (default version)
    3. Scenario mismatch OR not time effective → score = 0

    Selection rules:
    - Highest score wins
    - If multiple versions have same score:
        - If scenario match ties → use priority field, or raise AmbiguityError
        - If default ties → use priority field, or raise AmbiguityError
    """

    # Score definitions
    SCORE_SCENARIO_AND_TIME_MATCH = 2
    SCORE_DEFAULT_TIME_EFFECTIVE = 1
    SCORE_NO_MATCH = 0

    def evaluate_version(
        self,
        version,
        scenario: Optional[Dict[str, Any]],
        timestamp: Optional[datetime],
        priority: int
    ) -> ScenarioMatchResult:
        """
        Evaluate a single version against scenario and time criteria.

        Returns:
            ScenarioMatchResult with score and reason
        """
        # Check time effectiveness
        is_time_effective = version.is_effective(timestamp)

        # Check scenario match
        matches_scenario = version.matches_scenario(scenario)

        # Calculate score
        score, reason = self._calculate_score(
            version.version_name,
            version.scenario_condition,
            scenario,
            is_time_effective,
            matches_scenario
        )

        return ScenarioMatchResult(
            version_id=version.id,
            version_name=version.version_name,
            score=score,
            reason=reason,
            is_time_effective=is_time_effective,
            matches_scenario=matches_scenario
        )

    def _calculate_score(
        self,
        version_name: str,
        scenario_condition: Optional[Dict[str, Any]],
        provided_scenario: Optional[Dict[str, Any]],
        is_time_effective: bool,
        matches_scenario: bool
    ) -> tuple[int, str]:
        """
        Calculate match score and reason.

        Returns:
            (score, reason) tuple
        """
        # Not time effective → no match regardless of scenario
        if not is_time_effective:
            return (
                self.SCORE_NO_MATCH,
                f"not_time_effective"
            )

        # Scenario condition exists and matches → highest score
        if scenario_condition and matches_scenario:
            return (
                self.SCORE_SCENARIO_AND_TIME_MATCH,
                f"scenario_match: {scenario_condition}"
            )

        # Scenario condition exists but doesn't match → no match
        if scenario_condition and not matches_scenario:
            return (
                self.SCORE_NO_MATCH,
                f"scenario_mismatch: expected={scenario_condition}, provided={provided_scenario}"
            )

        # No scenario condition → default version
        if not scenario_condition:
            return (
                self.SCORE_DEFAULT_TIME_EFFECTIVE,
                f"default_version_no_scenario"
            )

        # Fallback
        return (self.SCORE_NO_MATCH, "unknown")

    def select_best_version(
        self,
        match_results: List[ScenarioMatchResult],
        versions_with_priority: Dict[int, int]
    ) -> ScenarioMatchResult:
        """
        Select the best version from match results.

        Args:
            match_results: List of evaluated versions
            versions_with_priority: Map of version_id → priority (higher is better)

        Returns:
            Selected ScenarioMatchResult

        Raises:
            ValueError: If no versions match
            AmbiguityError: If multiple versions tie with same score
        """
        if not match_results:
            raise ValueError("No versions to select from")

        # Group by score
        score_groups = {}
        for result in match_results:
            if result.score not in score_groups:
                score_groups[result.score] = []
            score_groups[result.score].append(result)

        # Get highest score
        max_score = max(score_groups.keys())
        best_candidates = score_groups[max_score]

        # If only one candidate, return it
        if len(best_candidates) == 1:
            selected = best_candidates[0]
            logger.info(f"✓ Single best version: {selected.version_name}")
            return selected

        # Multiple candidates with same score → use priority or raise ambiguity
        logger.warning(f"Multiple versions with score={max_score}: {[r.version_name for r in best_candidates]}")

        # Sort by priority (higher is better)
        prioritized = sorted(
            best_candidates,
            key=lambda r: versions_with_priority.get(r.version_id, 0),
            reverse=True
        )

        # Check if top priorities are unique
        top_priority = versions_with_priority.get(prioritized[0].version_id, 0)
        top_priority_count = sum(
            1 for r in prioritized
            if versions_with_priority.get(r.version_id, 0) == top_priority
        )

        if top_priority_count == 1:
            selected = prioritized[0]
            logger.info(f"✓ Selected by priority: {selected.version_name} (priority={top_priority})")
            return selected
        else:
            # Ambiguity remains
            from .models import AmbiguityError
            raise AmbiguityError(
                candidates=[
                    {"id": r.version_id, "name": r.version_name, "priority": versions_with_priority.get(r.version_id, 0)}
                    for r in prioritized
                ],
                message=f"Multiple versions have score={max_score} and priority={top_priority}. "
                       f"Please clarify which version to use."
            )

    def log_evaluation_results(
        self,
        match_results: List[ScenarioMatchResult],
        selected: ScenarioMatchResult
    ) -> None:
        """
        Log detailed evaluation results for explainability.
        """
        logger.info("=" * 80)
        logger.info("SCENARIO MATCH EVALUATION RESULTS")
        logger.info("=" * 80)

        for result in match_results:
            status = "✓" if result == selected else "✗"
            logger.info(
                f"{status} {result.version_name}: "
                f"score={result.score} reason={result.reason} "
                f"(time_effective={result.is_time_effective}, "
                f"scenario_match={result.matches_scenario})"
            )

        logger.info("-" * 80)
        logger.info(f"Selected version: {selected.version_name}")
        logger.info(f"  Score: {selected.score}")
        logger.info(f"  Reason: {selected.reason}")
        logger.info("=" * 80)
