"""
Integration tests for financial analysis tools.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from ..tools.registry import FinancialToolsRegistry
from ..tools.data_analysis import DataGapAnalyzer
from ..tools.data_imputation import WebDataImputationTool
from ..tools.metric_computation import PhilTownAnalysisWithImputation, HighGrowthAnalysisWithImputation
from ..schemas.tool_schemas import AnalysisStrategy


class TestFinancialToolsIntegration:
    """Test integration of financial analysis tools."""
    
    def test_tools_registry_initialization(self):
        """Test that the tools registry initializes correctly."""
        # Mock Tavily tool
        mock_tavily = Mock()
        mock_tavily.name = "tavily_search"
        mock_tavily.description = "Web search tool"
        
        # Initialize registry
        registry = FinancialToolsRegistry(tavily_tool=mock_tavily)
        
        # Check all tools are registered
        tool_names = registry.get_tool_names()
        expected_tools = [
            'phil_town_analysis_complete',
            'high_growth_analysis_complete',
            'impute_financial_data'
        ]
        
        for tool_name in expected_tools:
            assert tool_name in tool_names
        
        # Check tools can be retrieved
        phil_town_tool = registry.get_tool('phil_town_analysis_complete')
        assert isinstance(phil_town_tool, PhilTownAnalysisWithImputation)
        
        high_growth_tool = registry.get_tool('high_growth_analysis_complete')
        assert isinstance(high_growth_tool, HighGrowthAnalysisWithImputation)
        
        imputation_tool = registry.get_tool('impute_financial_data')
        assert isinstance(imputation_tool, WebDataImputationTool)
    
    def test_tool_categories(self):
        """Test tool categorization."""
        registry = FinancialToolsRegistry()
        
        analysis_tools = registry.get_tools_by_category('analysis')
        assert len(analysis_tools) == 2
        
        imputation_tools = registry.get_tools_by_category('imputation')
        assert len(imputation_tools) == 1
        
        all_tools = registry.get_tools_by_category('all')
        assert len(all_tools) == 3
    
    def test_tool_descriptions(self):
        """Test that all tools have descriptions."""
        registry = FinancialToolsRegistry()
        descriptions = registry.get_tool_descriptions()
        
        assert len(descriptions) == 3
        for tool_name, description in descriptions.items():
            assert description is not None
            assert len(description) > 10  # Should have meaningful descriptions
    
    def test_data_gap_analyzer(self):
        """Test data gap analyzer functionality."""
        analyzer = DataGapAnalyzer()
        
        # Mock stock data with some missing fields
        mock_stock_data = {
            'info': {
                'trailingEps': 5.0,
                'marketCap': 1000000000
            },
            'financials': MockDataFrame(),
            'balance_sheet': MockDataFrame(),
            'cash_flow': MockDataFrame()
        }
        
        # Analyze gaps for Phil Town strategy
        gap_analysis = analyzer.analyze_gaps(mock_stock_data, 'AAPL', 'phil_town')
        
        assert gap_analysis.strategy == 'phil_town'
        assert gap_analysis.ticker == 'AAPL'
        assert isinstance(gap_analysis.critical_missing, list)
        assert isinstance(gap_analysis.important_missing, list)
        assert isinstance(gap_analysis.optional_missing, list)
    
    @pytest.mark.asyncio
    async def test_imputation_tool_structure(self):
        """Test imputation tool structure without actual web calls."""
        mock_tavily = AsyncMock()
        mock_tavily.ainvoke = AsyncMock(return_value="Mock search result")
        
        tool = WebDataImputationTool(tavily_tool=mock_tavily)
        
        # Test that tool has required attributes
        assert tool.name == "impute_financial_data"
        assert tool.description is not None
        assert hasattr(tool, '_arun')
        assert hasattr(tool, '_run')
    
    def test_metric_computation_tools_structure(self):
        """Test that metric computation tools are properly structured."""
        phil_town_tool = PhilTownAnalysisWithImputation()
        high_growth_tool = HighGrowthAnalysisWithImputation()
        
        # Check tool attributes
        assert phil_town_tool.name == "phil_town_analysis_complete"
        assert phil_town_tool.description is not None
        assert hasattr(phil_town_tool, '_arun')
        assert hasattr(phil_town_tool, '_run')
        
        assert high_growth_tool.name == "high_growth_analysis_complete"
        assert high_growth_tool.description is not None
        assert hasattr(high_growth_tool, '_arun')
        assert hasattr(high_growth_tool, '_run')
    
    def test_analysis_strategies_enum(self):
        """Test that analysis strategy enum is properly defined."""
        assert AnalysisStrategy.PHIL_TOWN == "phil_town"
        assert AnalysisStrategy.HIGH_GROWTH == "high_growth"


class MockDataFrame:
    """Mock pandas DataFrame for testing."""
    
    def __init__(self, empty=True):
        self.empty = empty
        self.index = []
        self.columns = []
    
    def get(self, key, default=None):
        return default
    
    def __contains__(self, key):
        return False


@pytest.mark.integration
class TestFullWorkflow:
    """Test full workflow integration (requires actual dependencies)."""
    
    @pytest.mark.skip(reason="Requires external dependencies")
    @pytest.mark.asyncio
    async def test_complete_phil_town_workflow(self):
        """Test complete Phil Town analysis workflow."""
        # This test would require actual stock data and Tavily API
        # Skip by default, can be enabled for full integration testing
        pass
    
    @pytest.mark.skip(reason="Requires external dependencies") 
    @pytest.mark.asyncio
    async def test_complete_high_growth_workflow(self):
        """Test complete High-Growth analysis workflow."""
        # This test would require actual stock data and Tavily API
        # Skip by default, can be enabled for full integration testing
        pass


if __name__ == "__main__":
    # Run basic tests
    test_class = TestFinancialToolsIntegration()
    
    print("Running financial tools integration tests...")
    
    test_class.test_tools_registry_initialization()
    print("[PASS] Tools registry initialization test passed")
    
    test_class.test_tool_categories()
    print("[PASS] Tool categories test passed")
    
    test_class.test_tool_descriptions()
    print("[PASS] Tool descriptions test passed")
    
    test_class.test_data_gap_analyzer()
    print("[PASS] Data gap analyzer test passed")
    
    # Run async test
    async def run_async_tests():
        await test_class.test_imputation_tool_structure()
        print("[PASS] Imputation tool structure test passed")
    
    asyncio.run(run_async_tests())
    
    test_class.test_metric_computation_tools_structure()
    print("[PASS] Metric computation tools structure test passed")
    
    test_class.test_analysis_strategies_enum()
    print("[PASS] Analysis strategies enum test passed")
    
    print("\n[SUCCESS] All integration tests passed!")