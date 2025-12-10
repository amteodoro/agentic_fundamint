"""
Financial analysis tools registry for integration with the agent system.
"""

from typing import Dict, List
from langchain.tools import BaseTool
import logging

from .metric_computation import PhilTownAnalysisWithImputation, HighGrowthAnalysisWithImputation
from .data_imputation import WebDataImputationTool
from .competitor_analysis import CompetitorAnalysisTool
from .deep_dive import DeepDiveAnalysisTool
from .price_projection import PriceProjectionTool

logger = logging.getLogger(__name__)


class FinancialToolsRegistry:
    """Registry for all financial analysis tools."""
    
    def __init__(self, tavily_tool=None, llm=None):
        """Initialize the registry with external tool dependencies."""
        self.tavily_tool = tavily_tool
        self.llm = llm
        self._tools = {}
        self._initialize_tools()
    
    def _initialize_tools(self):
        """Initialize all financial analysis tools."""
        logger.info("Initializing financial analysis tools...")
        
        try:
            # Initialize core analysis tools
            self._tools['phil_town_analysis_complete'] = PhilTownAnalysisWithImputation(
                tavily_tool=self.tavily_tool
            )
            
            self._tools['high_growth_analysis_complete'] = HighGrowthAnalysisWithImputation(
                tavily_tool=self.tavily_tool
            )
            
            # Initialize standalone imputation tool
            self._tools['impute_financial_data'] = WebDataImputationTool(
                tavily_tool=self.tavily_tool
            )

            # Initialize competitor analysis tool
            if self.tavily_tool:
                self._tools['competitor_analysis'] = CompetitorAnalysisTool(
                    search_tool=self.tavily_tool,
                    llm=self.llm
                )
            else:
                logger.warning("Tavily tool not provided, skipping CompetitorAnalysisTool initialization")

            # Initialize deep dive analysis tool
            if self.llm:
                self._tools['deep_dive_analysis'] = DeepDiveAnalysisTool(
                    llm=self.llm,
                    search_tool=self.tavily_tool
                )
            else:
                logger.warning("LLM not provided, skipping DeepDiveAnalysisTool initialization")

            # Initialize price projection tool
            self._tools['price_projection_analysis'] = PriceProjectionTool()
            
            logger.info(f"Successfully initialized {len(self._tools)} financial analysis tools")
            
        except Exception as e:
            logger.error(f"Error initializing financial tools: {e}")
            raise
    
    def get_tool(self, tool_name: str) -> BaseTool:
        """Get a specific tool by name."""
        if tool_name not in self._tools:
            raise ValueError(f"Tool '{tool_name}' not found. Available tools: {list(self._tools.keys())}")
        
        return self._tools[tool_name]
    
    def get_all_tools(self) -> List[BaseTool]:
        """Get all available financial analysis tools."""
        return list(self._tools.values())
    
    def get_tool_names(self) -> List[str]:
        """Get names of all available tools."""
        return list(self._tools.keys())
    
    def get_tools_by_category(self, category: str) -> List[BaseTool]:
        """Get tools by category."""
        category_map = {
            'analysis': ['phil_town_analysis_complete', 'high_growth_analysis_complete'],
            'imputation': ['impute_financial_data'],
            'competitors': ['competitor_analysis'],
            'projection': ['price_projection_analysis'],
            'all': list(self._tools.keys())
        }
        
        tool_names = category_map.get(category, [])
        return [self._tools[name] for name in tool_names if name in self._tools]
    
    def get_tool_descriptions(self) -> Dict[str, str]:
        """Get descriptions of all tools."""
        return {name: tool.description for name, tool in self._tools.items()}


def create_financial_tools_registry(tavily_tool=None, llm=None) -> FinancialToolsRegistry:
    """Factory function to create a financial tools registry."""
    return FinancialToolsRegistry(tavily_tool=tavily_tool, llm=llm)