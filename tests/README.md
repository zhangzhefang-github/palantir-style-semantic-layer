# Semantic Layer Test Suite

Complete test suite for the Palantir-Style Semantic Control Layer.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py                 # Pytest configuration and fixtures
├── test_models.py              # Unit tests for data models
├── test_semantic_resolver.py   # Unit tests for semantic resolution
├── test_policy_engine.py       # Unit tests for policy engine
├── test_execution_engine.py    # Unit tests for execution engine
├── test_integration.py         # End-to-end integration tests
└── test_error_scenarios.py     # Error scenario and edge case tests
```

## Running Tests

### Install Test Dependencies

```bash
# Activate virtual environment
source .venv/bin/activate

# Install test dependencies
uv pip install -r requirements.txt
```

### Run All Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=. --cov-report=html
```

### Run Specific Test Files

```bash
# Run unit tests only
pytest tests/test_models.py
pytest tests/test_semantic_resolver.py
pytest tests/test_policy_engine.py
pytest tests/test_execution_engine.py

# Run integration tests
pytest tests/test_integration.py

# Run error scenario tests
pytest tests/test_error_scenarios.py
```

### Run Specific Tests

```bash
# Run tests matching a pattern
pytest -k "test_fpy"

# Run tests in a specific class
pytest tests/test_integration.py::TestSemanticOrchestratorIntegration

# Run a specific test method
pytest tests/test_models.py::TestSemanticObject::test_from_db_row
```

## Test Coverage

Current test coverage:

| Module | Coverage | Tests |
|--------|----------|-------|
| models.py | ~90% | 15+ tests |
| semantic_resolver.py | ~85% | 10+ tests |
| policy_engine.py | ~85% | 10+ tests |
| execution_engine.py | ~90% | 10+ tests |
| orchestrator.py | ~80% | 15+ tests |
| **Total** | **~85%** | **60+ tests** |

## Test Categories

### Unit Tests

- **test_models.py**: Data model validation and serialization
- **test_semantic_resolver.py**: Semantic object resolution and versioning
- **test_policy_engine.py**: Access control and policy evaluation
- **test_execution_engine.py**: SQL rendering and execution

### Integration Tests

- **test_integration.py**: End-to-end query workflows
  - Successful queries
  - Policy enforcement
  - Decision trace completeness
  - Audit history

### Error Scenario Tests

- **test_error_scenarios.py**: Edge cases and error handling
  - Missing parameters
  - Invalid input
  - Unauthorized access
  - Special characters
  - Concurrent queries

## Fixtures

### test_db_path
Creates a temporary database with schema and seed data for each test.

### test_context
Creates a standard operator execution context.

### admin_context
Creates an admin execution context.

### anonymous_context
Creates an anonymous execution context.

### sample_parameters
Sample query parameters for testing.

### today_parameters
Sample query parameters for today's date.

## Continuous Integration

To run tests in CI/CD:

```bash
# Run all tests with coverage
pytest --cov=. --cov-report=xml --cov-report=term

# Exit with non-zero if any test fails
set -e
pytest --cov=. --cov-report=xml
```

## Writing New Tests

### Example Test

```python
def test_my_new_feature(test_db_path):
    """Test description."""
    orchestrator = SemanticOrchestrator(test_db_path)

    context = ExecutionContext(
        user_id=1,
        role='operator',
        parameters={},
        timestamp=datetime.now()
    )

    result = orchestrator.query(
        question="My test question",
        parameters={},
        context=context
    )

    assert result['status'] == 'success'
    assert 'expected_field' in result
```

### Best Practices

1. **Use fixtures**: Always use `test_db_path` for isolated test databases
2. **Clean up**: Tests should clean up after themselves (fixtures handle this)
3. **Be specific**: Test one thing per test
4. **Use assertions**: Clear assertions with helpful messages
5. **Mock external dependencies**: Don't rely on external services

## Known Limitations

1. **Replay functionality**: Not fully tested due to parameter storage limitation
2. **Performance tests**: No performance or load tests yet
3. **Concurrent access**: Limited testing of concurrent query handling
4. **Database migrations**: No tests for schema migrations

## Future Improvements

- [ ] Add performance tests
- [ ] Add load tests for concurrent queries
- [ ] Add tests for schema migration
- [ ] Add visual regression tests for SQL generation
- [ ] Add property-based testing with Hypothesis
- [ ] Add integration tests with real data warehouse
