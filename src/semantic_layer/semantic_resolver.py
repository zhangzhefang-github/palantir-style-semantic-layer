"""
Semantic Resolver

Resolves natural language queries to semantic objects, versions, and logic.
This is the bridge between human language and semantic layer metadata.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from .models import (
    SemanticObject, SemanticVersion, LogicalDefinition,
    AmbiguityError, VersionNotFoundError
)
from .interfaces import MetadataStore
from .sqlite_stores import SQLiteMetadataStore

logger = logging.getLogger(__name__)


class SemanticResolver:
    """
    Resolves semantic objects and their definitions from the metadata store.

    Strategy pattern: Each resolution step is independent and testable.
    """

    def __init__(self, metadata_store: Optional[MetadataStore] = None, db_path: Optional[str] = None):
        """
        Initialize the resolver with a database connection.

        Args:
            metadata_store: Metadata store implementation
            db_path: Path to SQLite database (for sqlite default store)
        """
        if metadata_store is None:
            if not db_path:
                raise ValueError("db_path is required when metadata_store is not provided")
            metadata_store = SQLiteMetadataStore(db_path)
        self.metadata_store = metadata_store

    # ============================================================
    # RESOLUTION STEPS
    # ============================================================

    def resolve_semantic_object(self, question: str) -> SemanticObject:
        """
        Step 1: Resolve natural language to semantic object.

        Args:
            question: Natural language question

        Returns:
            Matched SemanticObject

        Raises:
            AmbiguityError: If multiple objects match
        """
        logger.info(f"=== STEP 1: RESOLVE SEMANTIC OBJECT ===")
        logger.info(f"Question: {question}")

        # Extract keywords from question
        keywords = self._extract_keywords(question)
        logger.info(f"Extracted keywords: {keywords}")

        # Search for matching semantic objects
        candidates = self._search_semantic_objects(keywords)
        logger.info(f"Found {len(candidates)} candidate(s)")

        if not candidates:
            logger.warning(f"No semantic object matched keywords: {keywords}")
            raise ValueError(f"No semantic object found for: {question}")

        if len(candidates) > 1:
            # Ambiguity detected - don't guess, ask for clarification
            logger.warning(f"Ambiguity detected: {len(candidates)} matches")
            raise AmbiguityError(
                candidates=[{"id": c.id, "name": c.name, "domain": c.domain} for c in candidates],
                message=f"Multiple semantic objects matched: {', '.join(c.name for c in candidates)}. Please clarify."
            )

        semantic_obj = candidates[0]
        logger.info(f"✓ Matched semantic object: {semantic_obj.name} (ID: {semantic_obj.id})")
        return semantic_obj

    def resolve_version(
        self,
        semantic_object_id: int,
        scenario: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ) -> SemanticVersion:
        """
        Step 2: Resolve the appropriate version based on time and scenario.

        Uses ScenarioMatcher for precise, explainable version selection.

        Args:
            semantic_object_id: ID of semantic object
            scenario: Optional scenario conditions (e.g., {"rework_enabled": true})
            timestamp: Query timestamp

        Returns:
            Selected SemanticVersion

        Raises:
            VersionNotFoundError: If no active version found
            AmbiguityError: If multiple versions match with same score and priority
        """
        logger.info(f"=== STEP 2: RESOLVE SEMANTIC VERSION ===")
        logger.info(f"Semantic Object ID: {semantic_object_id}")
        logger.info(f"Scenario: {scenario}")
        logger.info(f"Timestamp: {timestamp}")

        versions = self._get_versions_for_object(semantic_object_id)
        logger.info(f"Found {len(versions)} version(s)")

        if not versions:
            raise VersionNotFoundError(
                f"No versions found for semantic_object_id={semantic_object_id}"
            )

        # Get version priorities from SemanticVersion objects
        version_priorities = {v.id: v.priority for v in versions}

        # Import ScenarioMatcher
        from .scenario_matcher import ScenarioMatcher

        matcher = ScenarioMatcher()

        # Evaluate all versions
        match_results = []
        for version in versions:
            result = matcher.evaluate_version(
                version=version,
                scenario=scenario,
                timestamp=timestamp,
                priority=version_priorities.get(version.id, 0)
            )
            match_results.append(result)

        # Select best version
        selected_result = matcher.select_best_version(match_results, version_priorities)

        # Log evaluation results for explainability
        matcher.log_evaluation_results(match_results, selected_result)

        # Get the actual version object
        selected = next(v for v in versions if v.id == selected_result.version_id)

        logger.info(f"✓ Selected version: {selected.version_name} (ID: {selected.id})")
        logger.info(f"  Description: {selected.description}")

        return selected

    def resolve_logic(self, semantic_version_id: int) -> LogicalDefinition:
        """
        Step 3: Resolve logical definition (business formula).

        Args:
            semantic_version_id: ID of semantic version

        Returns:
            LogicalDefinition containing business formula
        """
        logger.info(f"=== STEP 3: RESOLVE LOGICAL DEFINITION ===")
        logger.info(f"Semantic Version ID: {semantic_version_id}")

        logical_def = self._get_logical_definition(semantic_version_id)

        if not logical_def:
            raise ValueError(
                f"No logical definition found for semantic_version_id={semantic_version_id}"
            )

        logger.info(f"✓ Resolved logic: {logical_def.expression}")
        logger.info(f"  Grain: {logical_def.grain}")
        logger.info(f"  Variables: {logical_def.variables}")

        return logical_def

    # ============================================================
    # DATABASE QUERIES
    # ============================================================

    def _extract_keywords(self, question: str) -> List[str]:
        """
        Extract potential semantic keywords from question.
        For POC, use known phrase matching.
        """
        import re

        # Known Chinese phrases and their English equivalents
        # Format: (chinese_phrase, english_equivalent)
        known_phrases = [
            ('一次合格率', 'FPY'),
            ('直通率', 'FPY'),
            ('良率', 'FPY'),
            ('合格率', 'FPY'),
            ('产量', 'Output'),
            ('产出数量', 'Output'),
            ('生产量', 'Output'),
            ('不良率', 'Defect'),
            ('次品率', 'Defect'),
            ('缺陷率', 'Defect'),
        ]

        keywords = []

        # Check if any known phrase appears in the question
        for chinese_phrase, english_equiv in known_phrases:
            if chinese_phrase in question:
                keywords.append(chinese_phrase)
                keywords.append(english_equiv)

        # Also extract standalone English words
        english_words = re.findall(r'\b[a-zA-Z]{2,}\b', question.lower())
        keywords.extend(english_words)

        # Term dictionary normalization (lightweight)
        try:
            term_matches = self.metadata_store.find_terms_in_text(question)
            for term in term_matches:
                keywords.append(term.term)
                keywords.append(term.normalized_term)
        except Exception:
            # Term dictionary is optional; do not block resolution
            pass

        # If nothing found, try to extract any Chinese words (3+ chars)
        if not keywords:
            chinese_words = re.findall(r'[\u4e00-\u9fff]{3,}', question)
            keywords.extend(chinese_words)

        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for kw in keywords:
            if kw not in seen:
                seen.add(kw)
                unique_keywords.append(kw)

        return unique_keywords

    def _search_semantic_objects(self, keywords: List[str]) -> List[SemanticObject]:
        """
        Search for semantic objects matching keywords.

        Returns list ordered by relevance.
        """
        candidates = []
        for obj in self.metadata_store.list_active_semantic_objects():
            score = self._calculate_relevance(obj, keywords)
            if score > 0:
                candidates.append((score, obj))

        # Sort by relevance (descending) and return objects
        candidates.sort(key=lambda x: x[0], reverse=True)
        return [obj for score, obj in candidates]

    def _calculate_relevance(self, obj: SemanticObject, keywords: List[str]) -> int:
        """
        Calculate relevance score for a semantic object against keywords.
        Higher score = better match.
        """
        score = 0

        for keyword in keywords:
            # Exact match on name (highest score)
            if keyword.lower() == obj.name.lower():
                score += 10

            # Match in aliases
            if any(keyword.lower() == alias.lower() for alias in obj.aliases):
                score += 8

            # Partial match in name
            if keyword.lower() in obj.name.lower():
                score += 3

            # Partial match in description
            if keyword.lower() in obj.description.lower():
                score += 1

            # Partial match in aliases
            if any(keyword.lower() in alias.lower() for alias in obj.aliases):
                score += 2

        return score

    def _get_versions_for_object(self, semantic_object_id: int) -> List[SemanticVersion]:
        """Get all versions for a semantic object"""
        return self.metadata_store.get_versions_for_object(semantic_object_id)

    def _get_logical_definition(self, semantic_version_id: int) -> Optional[LogicalDefinition]:
        """Get logical definition for a semantic version"""
        return self.metadata_store.get_logical_definition(semantic_version_id)

    def get_semantic_object_by_id(self, obj_id: int) -> Optional[SemanticObject]:
        """Get semantic object by ID"""
        return self.metadata_store.get_semantic_object_by_id(obj_id)

    def get_all_semantic_objects(self) -> List[SemanticObject]:
        """Get all semantic objects"""
        return self.metadata_store.list_active_semantic_objects()
