# Enhanced Financial Agent Tools Implementation Plan

## Overview

This plan outlines the implementation of advanced financial analysis tools for the Fundamint AI agent, including web-based data imputation capabilities using the existing Tavily search integration.

## Current Analysis Capabilities

### Phil Town Strategy Metrics
- **ROIC (Return on Invested Capital)**: Requires EBIT, tax rates, stockholder equity, long-term debt
- **Growth Rates**: EPS, BVPS, Sales, FCF growth (CAGR calculations)
- **Management Metrics**: Debt payoff years, insider ownership
- **Margin of Safety**: Future EPS projections, PE ratios, sticker price calculations

### High-Growth Strategy Metrics  
- **Sales Growth**: Revenue CAGR analysis
- **Profitability**: Net margins, ROE, ROIC
- **Valuation**: PSR, PER, EV/EBITDA ratios
- **Financial Health**: Net debt, debt-to-EBITDA ratios
- **Capital Efficiency**: Dividend analysis, insider ownership

## Enhanced Tool Architecture with Web Imputation

### 1. Core Metric Computation Tools

#### `compute_phil_town_metrics_with_imputation`
```python
async def compute_phil_town_metrics_with_imputation(ticker: str, enable_web_search: bool = True) -> dict:
    """
    Computes Phil Town strategy metrics with intelligent data imputation.
    
    Features:
    - Primary calculation with available data
    - Identifies missing critical data points
    - Uses Tavily search to find missing financial data
    - Validates and incorporates web-sourced data
    - Provides confidence scores based on data sources
    """
```

#### `compute_high_growth_metrics_with_imputation`
```python
async def compute_high_growth_metrics_with_imputation(ticker: str, enable_web_search: bool = True) -> dict:
    """
    Computes High-Growth strategy metrics with web-based data enhancement.
    
    Features:
    - Comprehensive metric calculation
    - Web-based data gap filling
    - Multi-source data validation
    - Trend analysis with imputed historical data
    """
```

### 2. Web-Based Data Imputation System

#### `intelligent_data_imputer`
```python
async def intelligent_data_imputer(ticker: str, missing_fields: list, strategy_context: str) -> dict:
    """
    Intelligently imputes missing financial data using web search.
    
    Process:
    1. Identifies critical missing data points for strategy
    2. Generates targeted search queries for each missing field
    3. Uses Tavily to search for recent financial reports/data
    4. Extracts and validates numerical data from search results
    5. Applies data quality scoring and confidence assessment
    6. Returns structured imputed data with source attribution
    
    Returns:
    - Imputed values with confidence scores
    - Source URLs and extraction methods
    - Data validation results
    - Alternative value ranges when uncertain
    """
```

#### `web_financial_data_extractor`
```python
async def web_financial_data_extractor(search_results: list, target_metrics: list, ticker: str) -> dict:
    """
    Extracts financial metrics from web search results.
    
    Features:
    - Pattern matching for financial data formats
    - Multi-source cross-validation
    - Temporal relevance assessment
    - Source reliability scoring
    - Automated data cleaning and normalization
    """
```

#### `search_query_generator`
```python
def generate_search_queries(ticker: str, missing_field: str, strategy: str) -> list:
    """
    Generates targeted search queries for missing financial data.
    
    Query Types:
    - SEC filing searches: "{ticker} 10-K EBIT operating income"
    - Financial database queries: "{ticker} return on invested capital ROIC"
    - Recent earnings queries: "{ticker} Q3 2024 earnings debt equity"
    - Analyst report searches: "{ticker} financial metrics analysis 2024"
    - Investor relations searches: "{ticker} investor presentation financial data"
    """
```

### 3. Data Quality and Validation Enhancement

#### `web_data_validator`
```python
async def web_data_validator(ticker: str, field: str, web_value: float, existing_data: dict) -> dict:
    """
    Validates web-sourced financial data against existing information.
    
    Validation Methods:
    - Cross-reference with existing ratios/relationships
    - Temporal consistency checks
    - Industry benchmark comparisons
    - Source credibility assessment
    - Statistical outlier detection
    
    Returns:
    - Validation score (0-1)
    - Confidence level assessment
    - Recommended usage guidelines
    - Alternative values if validation fails
    """
```

#### `data_source_credibility_scorer`
```python
def score_data_source_credibility(url: str, content: str, data_point: str) -> float:
    """
    Scores the credibility of web-sourced financial data.
    
    Scoring Factors:
    - Source authority (SEC > Bloomberg > Yahoo Finance > Forums)
    - Recency of data
    - Data presentation format (structured > unstructured)
    - Cross-reference availability
    - Content context relevance
    """
```

## Implementation Structure

### Enhanced File Structure
```
backend/app/financial_agent/
├── tools/
│   ├── __init__.py
│   ├── metric_computation.py           # Core metric calculation tools
│   ├── data_imputation.py             # Web-based data imputation system
│   ├── web_data_extraction.py         # Financial data extraction from web
│   ├── data_validation.py             # Enhanced validation with web data
│   ├── search_strategies.py           # Query generation and search optimization
│   └── utils.py                       # Shared utilities
├── schemas/
│   ├── __init__.py
│   ├── tool_schemas.py                # Tool input/output schemas
│   ├── metric_schemas.py              # Detailed metric structures
│   └── imputation_schemas.py          # Web imputation result schemas
├── config/
│   ├── __init__.py
│   ├── search_patterns.py             # Financial data extraction patterns
│   └── source_rankings.py             # Web source credibility rankings
└── tests/
    ├── test_metric_tools.py           # Core tool tests
    ├── test_imputation.py             # Web imputation tests
    └── test_integration.py            # Full integration tests
```

## Web Imputation Workflow

### Phase 1: Data Gap Analysis
```python
class DataGapAnalyzer:
    def __init__(self, strategy: str):
        self.strategy = strategy
        self.required_fields = self._load_strategy_requirements()
    
    def analyze_gaps(self, stock_data: dict, ticker: str) -> dict:
        """
        Analyzes missing data points critical for strategy analysis.
        
        Returns:
        - Critical missing fields (analysis cannot proceed without)
        - Important missing fields (reduces analysis quality)
        - Optional missing fields (minimal impact)
        - Search priority ranking
        """
        gaps = {
            'critical': [],
            'important': [],
            'optional': [],
            'search_queries': {}
        }
        
        for field in self.required_fields['critical']:
            if not self._field_available(stock_data, field):
                gaps['critical'].append(field)
                gaps['search_queries'][field] = self._generate_search_queries(ticker, field)
        
        return gaps
```

### Phase 2: Intelligent Web Search
```python
class FinancialWebSearcher:
    def __init__(self, tavily_tool):
        self.tavily = tavily_tool
        self.extraction_patterns = FinancialDataPatterns()
    
    async def search_for_financial_data(self, ticker: str, field: str, queries: list) -> dict:
        """
        Executes targeted web searches for financial data.
        
        Process:
        1. Execute multiple search queries using Tavily
        2. Filter results for financial relevance
        3. Extract numerical data using pattern matching
        4. Cross-validate across multiple sources
        5. Rank results by credibility and recency
        """
        search_results = {}
        
        for query in queries:
            try:
                # Use existing Tavily integration
                results = await self.tavily.ainvoke({"query": query})
                search_results[query] = self._process_search_results(results, field, ticker)
            except Exception as e:
                search_results[query] = {'error': str(e), 'data': None}
        
        return self._consolidate_search_results(search_results, field)
```

### Phase 3: Data Extraction and Validation
```python
class FinancialDataPatterns:
    """Pattern matching for extracting financial data from web content"""
    
    PATTERNS = {
        'roic': [
            r'ROIC[:\s]+(\d+\.?\d*)%?',
            r'Return on Invested Capital[:\s]+(\d+\.?\d*)%?',
            r'return on invested capital[:\s]+(\d+\.?\d*)%?'
        ],
        'ebit': [
            r'EBIT[:\s]+\$?(\d+(?:,\d{3})*(?:\.\d+)?)[BMK]?',
            r'Operating Income[:\s]+\$?(\d+(?:,\d{3})*(?:\.\d+)?)[BMK]?',
            r'Earnings before interest and taxes[:\s]+\$?(\d+(?:,\d{3})*(?:\.\d+)?)[BMK]?'
        ],
        'debt': [
            r'Total Debt[:\s]+\$?(\d+(?:,\d{3})*(?:\.\d+)?)[BMK]?',
            r'Long[- ]term Debt[:\s]+\$?(\d+(?:,\d{3})*(?:\.\d+)?)[BMK]?'
        ]
    }
    
    def extract_metric(self, content: str, metric_type: str) -> list:
        """Extract financial metrics from text content using regex patterns"""
        patterns = self.PATTERNS.get(metric_type, [])
        matches = []
        
        for pattern in patterns:
            found = re.findall(pattern, content, re.IGNORECASE)
            matches.extend(found)
        
        return self._normalize_financial_values(matches)
```

## Enhanced Tool Examples

### Complete Phil Town Analysis with Web Imputation
```python
class PhilTownAnalysisWithImputation(BaseTool):
    name = "phil_town_analysis_complete"
    description = """
    Performs comprehensive Phil Town analysis with intelligent data imputation.
    Uses web search to fill critical data gaps when local data is insufficient.
    """
    
    async def _arun(self, ticker: str, enable_web_search: bool = True) -> dict:
        # Step 1: Fetch primary data
        stock_data = fetch_stock_data(ticker)
        
        # Step 2: Analyze data completeness
        gap_analyzer = DataGapAnalyzer('phil_town')
        data_gaps = gap_analyzer.analyze_gaps(stock_data, ticker)
        
        result = {
            'ticker': ticker,
            'primary_data_quality': self._assess_primary_data(stock_data),
            'missing_critical_fields': data_gaps['critical'],
            'imputation_attempted': False,
            'imputation_results': {},
            'final_metrics': {},
            'confidence_scores': {},
            'data_sources': {'primary': 'yfinance/finviz/investiny', 'web': []}
        }
        
        # Step 3: Web imputation if enabled and needed
        if enable_web_search and data_gaps['critical']:
            result['imputation_attempted'] = True
            
            imputer = IntelligentDataImputer()
            imputation_results = await imputer.impute_missing_data(
                ticker, data_gaps['critical'], 'phil_town'
            )
            
            result['imputation_results'] = imputation_results
            
            # Merge imputed data with original data
            enhanced_data = self._merge_imputed_data(stock_data, imputation_results)
        else:
            enhanced_data = stock_data
        
        # Step 4: Calculate metrics with enhanced data
        phil_town_calculator = EnhancedPhilTownCalculator(enhanced_data)
        metrics = await phil_town_calculator.calculate_all_metrics()
        
        result.update({
            'final_metrics': metrics,
            'confidence_scores': phil_town_calculator.get_confidence_scores(),
            'analysis_summary': phil_town_calculator.generate_summary(),
            'recommendations': phil_town_calculator.generate_recommendations()
        })
        
        return result
```

### Web Data Imputation Tool
```python
class WebDataImputationTool(BaseTool):
    name = "impute_financial_data"
    description = """
    Intelligently imputes missing financial data using web search.
    Searches SEC filings, financial databases, and analyst reports.
    """
    
    async def _arun(self, ticker: str, missing_fields: list, strategy_context: str = None) -> dict:
        imputer = IntelligentDataImputer()
        
        result = {
            'ticker': ticker,
            'requested_fields': missing_fields,
            'strategy_context': strategy_context,
            'imputation_results': {},
            'search_summary': {},
            'data_quality_assessment': {}
        }
        
        for field in missing_fields:
            try:
                # Generate targeted search queries
                queries = generate_search_queries(ticker, field, strategy_context)
                
                # Execute web searches
                searcher = FinancialWebSearcher(self.tavily_tool)
                search_results = await searcher.search_for_financial_data(ticker, field, queries)
                
                # Validate and score results
                validator = WebDataValidator()
                validation_results = await validator.validate_extracted_data(
                    ticker, field, search_results
                )
                
                result['imputation_results'][field] = {
                    'imputed_value': validation_results.get('best_value'),
                    'confidence': validation_results.get('confidence', 0.0),
                    'sources': validation_results.get('sources', []),
                    'alternative_values': validation_results.get('alternatives', []),
                    'validation_notes': validation_results.get('notes', '')
                }
                
                result['search_summary'][field] = {
                    'queries_executed': len(queries),
                    'sources_found': len(search_results),
                    'extraction_success': validation_results.get('success', False)
                }
                
            except Exception as e:
                result['imputation_results'][field] = {
                    'error': str(e),
                    'imputed_value': None,
                    'confidence': 0.0
                }
        
        # Overall assessment
        result['data_quality_assessment'] = self._assess_overall_quality(
            result['imputation_results']
        )
        
        return result
```

## Search Query Strategies

### Dynamic Query Generation
```python
class SearchQueryGenerator:
    QUERY_TEMPLATES = {
        'phil_town': {
            'roic': [
                "{ticker} return on invested capital ROIC 2024",
                "{ticker} 10-K SEC filing ROIC operating income",
                "{ticker} NOPAT invested capital calculation",
                "site:sec.gov {ticker} annual report ROIC"
            ],
            'eps_growth': [
                "{ticker} earnings per share growth rate historical",
                "{ticker} EPS CAGR 5 year 10 year analysis",
                "site:finance.yahoo.com {ticker} earnings growth",
                "{ticker} analyst EPS growth estimates"
            ],
            'debt_payoff': [
                "{ticker} long term debt free cash flow ratio",
                "{ticker} balance sheet debt cash flow statement",
                "{ticker} debt payoff capability years FCF",
                "site:morningstar.com {ticker} debt analysis"
            ]
        },
        'high_growth': {
            'net_margin_trend': [
                "{ticker} net profit margin trend 5 years",
                "{ticker} profitability margins expanding contracting",
                "{ticker} quarterly earnings margin analysis",
                "site:bloomberg.com {ticker} margin expansion"
            ],
            'sales_growth': [
                "{ticker} revenue growth CAGR compound annual",
                "{ticker} sales growth rate quarterly annual",
                "{ticker} top line growth acceleration",
                "site:seekingalpha.com {ticker} revenue growth"
            ]
        }
    }
    
    def generate_queries(self, ticker: str, field: str, strategy: str) -> list:
        """Generate contextual search queries based on strategy and field"""
        templates = self.QUERY_TEMPLATES.get(strategy, {}).get(field, [])
        return [template.format(ticker=ticker.upper()) for template in templates]
```

## Integration with Existing Tavily Tool

### Enhanced MCP Configuration
```json
{
  "mcpServers": {
    "brave-search": {
      "command": "npx",
      "args": ["-y", "tavily-mcp@latest"],
      "env": {
        "TAVILY_API_KEY": "${TAVILY_API_KEY}"
      }
    },
    "financial-tools": {
      "command": "python",
      "args": ["-m", "app.financial_agent.tools.mcp_server"],
      "env": {
        "OPENAI_API_KEY": "${OPENAI_API_KEY}",
        "TAVILY_API_KEY": "${TAVILY_API_KEY}"
      }
    }
  }
}
```

### Tool Registration Enhancement
```python
# In dependencies.py
async def get_enhanced_agent_dependencies() -> AgentDependencies:
    # Load existing MCP tools (including Tavily)
    external_tools = await load_mcp_tools()
    
    # Initialize internal financial tools with Tavily access
    financial_tools = FinancialToolsRegistry(tavily_tool=external_tools['tavily'])
    internal_tools = financial_tools.get_all_tools()
    
    # Combine external and internal tools
    all_tools = external_tools + internal_tools
    
    return AgentDependencies(
        llm=llm,
        tools_for_llm=[convert_to_openai_tool(tool) for tool in all_tools],
        tools_map={tool.name: tool for tool in all_tools}
    )
```

## Testing Strategy for Web Imputation

### Unit Tests
```python
class TestWebImputation:
    @pytest.mark.asyncio
    async def test_search_query_generation(self):
        generator = SearchQueryGenerator()
        queries = generator.generate_queries("AAPL", "roic", "phil_town")
        assert len(queries) >= 3
        assert "AAPL" in queries[0]
        assert "ROIC" in queries[0].upper()
    
    @pytest.mark.asyncio 
    async def test_financial_data_extraction(self):
        content = "Apple Inc. reported ROIC of 25.2% for fiscal 2024"
        extractor = FinancialDataPatterns()
        values = extractor.extract_metric(content, 'roic')
        assert 25.2 in values
    
    @pytest.mark.asyncio
    async def test_data_validation_logic(self):
        validator = WebDataValidator()
        result = await validator.validate_extracted_data(
            "AAPL", "roic", [{'value': 25.2, 'source': 'sec.gov'}]
        )
        assert result['confidence'] > 0.5
```

### Integration Tests with Real Web Data
```python
@pytest.mark.integration
class TestWebImputationIntegration:
    @pytest.mark.asyncio
    async def test_complete_imputation_workflow(self):
        """Test full imputation workflow with real web search"""
        tool = WebDataImputationTool()
        result = await tool._arun("AAPL", ["roic"], "phil_town")
        
        assert 'imputation_results' in result
        assert 'roic' in result['imputation_results']
        assert result['imputation_results']['roic']['confidence'] > 0
```

## Benefits of Web Imputation Feature

### Enhanced Analysis Coverage
- **Increased Success Rate**: Analysis possible even with incomplete primary data
- **Real-time Updates**: Access to most recent financial information
- **Comprehensive Coverage**: Multiple data sources reduce analysis gaps

### Intelligent Data Quality
- **Source Attribution**: Clear tracking of data origins
- **Confidence Scoring**: Quantified reliability assessment  
- **Cross-validation**: Multiple source verification
- **Temporal Relevance**: Prioritization of recent data

### User Experience
- **Transparent Process**: Clear explanation of data sources and imputation
- **Quality Indicators**: Visual confidence scores and data quality metrics
- **Fallback Options**: Graceful degradation when imputation fails
- **Source Links**: Direct access to original data sources

This enhanced implementation plan provides a robust framework for web-based financial data imputation while maintaining data quality and user trust through comprehensive validation and transparency features.