# Financial Agent Tools Testing

## Overview
This directory contains tests for the financial analysis tools with web-based data imputation capabilities.

## Docker Testing Instructions

All tests must be run within the Docker container environment to ensure proper dependency management and isolation.

### Setup
```bash
# Start the Docker containers
docker-compose up --build

# Access the backend container
docker-compose exec backend bash
```

### Running Tests

#### Unit Tests
```bash
# Run all financial agent tests
pytest app/financial_agent/tests/ -v

# Run specific test file
pytest app/financial_agent/tests/test_integration.py -v

# Run with coverage
pytest app/financial_agent/tests/ --cov=app.financial_agent
```

#### Integration Tests
```bash
# Run integration tests (requires environment variables)
pytest app/financial_agent/tests/test_integration.py -m integration -v

# Skip integration tests (for quick testing)
pytest app/financial_agent/tests/test_integration.py -m "not integration" -v
```

### Environment Variables Required

For full testing including web imputation:
```bash
export OPENROUTER_API_KEY="your_key"
export TAVILY_API_KEY="your_key"
export OPENROUTER_MODEL="google/gemini-flash-1.5:free"
```

### Test Coverage

The test suite covers:

1. **Tool Registry Integration**
   - Tool initialization and registration
   - Tool categorization and retrieval
   - Dependency injection with Tavily

2. **Data Gap Analysis**
   - Strategy-specific field requirements
   - Data completeness assessment
   - Search query generation

3. **Web Data Imputation**
   - Search execution and result processing
   - Financial data extraction patterns
   - Source credibility scoring
   - Data validation and quality metrics

4. **Enhanced Metric Computation**
   - Phil Town analysis with imputation
   - High-Growth analysis with imputation
   - Confidence scoring and interpretation
   - Analysis summaries and recommendations

### Manual Testing

To manually test the tools:

```bash
# Access Python shell in container
docker-compose exec backend python

# Test tool initialization
from app.financial_agent.tools.registry import FinancialToolsRegistry
registry = FinancialToolsRegistry()
print(registry.get_tool_names())

# Test data gap analysis
from app.financial_agent.tools.data_analysis import DataGapAnalyzer
from app.data_fetcher import fetch_stock_data

analyzer = DataGapAnalyzer()
stock_data = fetch_stock_data("AAPL")
gaps = analyzer.analyze_gaps(stock_data, "AAPL", "phil_town")
print(f"Critical missing: {gaps.critical_missing}")
```

### Debugging

Enable debug logging:
```bash
export PYTHONPATH=/app
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from app.financial_agent.tools.registry import FinancialToolsRegistry
registry = FinancialToolsRegistry()
"
```

## Test Structure

- `test_integration.py`: Integration tests for tool coordination
- `README.md`: This file with testing instructions

## Notes

- Tests are designed to work with mock data when external APIs are unavailable
- Integration tests require actual API keys and are marked with `@pytest.mark.integration`
- All file paths and imports assume execution within the Docker container environment