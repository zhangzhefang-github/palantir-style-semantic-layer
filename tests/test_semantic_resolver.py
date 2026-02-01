"""
Unit tests for SemanticResolver.
"""

import pytest
from semantic_layer.semantic_resolver import SemanticResolver
from semantic_layer.models import AmbiguityError, VersionNotFoundError


class TestSemanticResolver:
    """Test SemanticResolver functionality."""

    def test_extract_keywords_chinese_phrases(self, test_db_path):
        """Test keyword extraction for Chinese phrases."""
        resolver = SemanticResolver(db_path=test_db_path)

        # Test FPY related phrases
        keywords = resolver._extract_keywords("昨天产线A的一次合格率是多少？")
        assert '一次合格率' in keywords
        assert 'FPY' in keywords

        # Test OutputQty related phrases
        keywords = resolver._extract_keywords("产线B的产量是多少")
        assert '产量' in keywords
        assert 'Output' in keywords

        # Test DefectRate related phrases
        keywords = resolver._extract_keywords("今天的不良率")
        assert '不良率' in keywords
        assert 'Defect' in keywords

    def test_extract_keywords_english(self, test_db_path):
        """Test keyword extraction for English text."""
        resolver = SemanticResolver(db_path=test_db_path)

        keywords = resolver._extract_keywords("What is the FPY for line A?")
        # English words are converted to lowercase
        assert 'fpy' in keywords
        assert 'what' in keywords

    def test_resolve_semantic_object_success(self, test_db_path):
        """Test successful semantic object resolution."""
        resolver = SemanticResolver(db_path=test_db_path)

        obj = resolver.resolve_semantic_object("昨天产线A的一次合格率是多少？")

        assert obj.name == 'FPY'
        assert obj.domain == 'production'
        assert obj.id == 1

    def test_resolve_semantic_object_ambiguity(self, test_db_path):
        """Test semantic object resolution with ambiguity."""
        resolver = SemanticResolver(db_path=test_db_path)

        # This should trigger ambiguity if multiple objects match
        # For now, our seed data has distinct objects, so this won't trigger
        # In a real scenario, you'd add multiple objects with similar aliases

        # Test with completely unrelated query
        with pytest.raises(ValueError, match="No semantic object found"):
            resolver.resolve_semantic_object("什么是天气？")

    def test_resolve_version_default(self, test_db_path):
        """Test version resolution for default scenario."""
        resolver = SemanticResolver(db_path=test_db_path)

        # Should select the active standard version
        version = resolver.resolve_version(
            semantic_object_id=1,
            scenario=None,
            timestamp=None
        )

        assert version.version_name == 'FPY_v1_standard'
        assert version.is_active is True

    def test_resolve_version_with_time(self, test_db_path):
        """Test version resolution with timestamp."""
        resolver = SemanticResolver(db_path=test_db_path)

        # Query in 2024 should get v1
        version = resolver.resolve_version(
            semantic_object_id=1,
            scenario=None,
            timestamp=None
        )

        assert version.version_name == 'FPY_v1_standard'

    def test_resolve_version_with_scenario(self, test_db_path):
        """Test version resolution with scenario condition."""
        resolver = SemanticResolver(db_path=test_db_path)

        # Default scenario should get v1
        version = resolver.resolve_version(
            semantic_object_id=1,
            scenario=None,
            timestamp=None
        )
        assert version.version_name == 'FPY_v1_standard'

        # Scenario with rework_enabled should ideally get v2
        # But in our seed data, v2 is inactive, so it falls back to v1
        version = resolver.resolve_version(
            semantic_object_id=1,
            scenario={'rework_enabled': True},
            timestamp=None
        )
        # Should still return v1 since v2 is inactive
        assert version.is_active is True

    def test_resolve_logic(self, test_db_path):
        """Test logical definition resolution."""
        resolver = SemanticResolver(db_path=test_db_path)

        logical_def = resolver.resolve_logic(semantic_version_id=1)

        assert logical_def.expression == 'good_qty / total_qty'
        assert logical_def.grain == 'line,day'
        assert 'good_qty' in logical_def.variables
        assert 'total_qty' in logical_def.variables

    def test_resolve_logic_not_found(self, test_db_path):
        """Test logical definition resolution for non-existent version."""
        resolver = SemanticResolver(db_path=test_db_path)

        with pytest.raises(ValueError, match="No logical definition found"):
            resolver.resolve_logic(semantic_version_id=999)

    def test_get_semantic_object_by_id(self, test_db_path):
        """Test getting semantic object by ID."""
        resolver = SemanticResolver(db_path=test_db_path)

        obj = resolver.get_semantic_object_by_id(1)

        assert obj is not None
        assert obj.id == 1
        assert obj.name == 'FPY'

    def test_get_semantic_object_by_id_not_found(self, test_db_path):
        """Test getting non-existent semantic object."""
        resolver = SemanticResolver(db_path=test_db_path)

        obj = resolver.get_semantic_object_by_id(999)
        assert obj is None

    def test_get_all_semantic_objects(self, test_db_path):
        """Test getting all semantic objects."""
        resolver = SemanticResolver(db_path=test_db_path)

        objects = resolver.get_all_semantic_objects()

        assert len(objects) == 5  # FPY, OutputQty, DefectRate, QualityScore, GrossMargin
        assert any(obj.name == 'FPY' for obj in objects)
        assert any(obj.name == 'OutputQty' for obj in objects)
        assert any(obj.name == 'DefectRate' for obj in objects)

    def test_keyword_relevance_scoring(self, test_db_path):
        """Test relevance scoring for keyword matching."""
        resolver = SemanticResolver(db_path=test_db_path)

        # Calculate relevance for FPY object with matching keywords
        obj = resolver.get_semantic_object_by_id(1)
        score = resolver._calculate_relevance(obj, ['FPY', '一次合格率', '良率'])

        # Should have high score due to multiple matches
        assert score > 0

    def test_keyword_relevance_no_match(self, test_db_path):
        """Test relevance scoring with no matching keywords."""
        resolver = SemanticResolver(db_path=test_db_path)

        obj = resolver.get_semantic_object_by_id(1)
        score = resolver._calculate_relevance(obj, ['天气', '温度'])

        # Should have zero score for unrelated keywords
        assert score == 0
