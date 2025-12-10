"""
Data gap analysis and completeness assessment for financial analysis strategies.
"""

import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging

from ..schemas.metric_schemas import DataGapAnalysis
from ..schemas.tool_schemas import DataQualityAssessment
from ..config.search_patterns import SearchQueryGenerator

logger = logging.getLogger(__name__)


class DataGapAnalyzer:
    """Analyzes missing data points critical for financial analysis strategies."""
    
    # Define required fields for each strategy
    STRATEGY_REQUIREMENTS = {
        'phil_town': {
            'critical': {
                # ROIC calculation requirements
                'ebit': {
                    'sources': ['Operating Income', 'EBIT'],
                    'fallbacks': ['Net Income', 'Interest Expense', 'Tax Provision'],
                    'description': 'Earnings before interest and taxes',
                    'impact': 'Cannot calculate ROIC without EBIT or components'
                },
                'total_stockholder_equity': {
                    'sources': ['Stockholders Equity', 'Common Stock Equity', 'Total Equity Gross Minority Interest'],
                    'fallbacks': [],
                    'description': 'Total shareholder equity',
                    'impact': 'Required for ROIC invested capital calculation'
                },
                'diluted_eps': {
                    'sources': ['Diluted EPS', 'Basic EPS'],
                    'fallbacks': ['Net Income', 'Diluted Average Shares'],
                    'description': 'Earnings per share',
                    'impact': 'Required for EPS growth and margin of safety'
                },
                'total_revenue': {
                    'sources': ['Total Revenue', 'Revenue', 'Sales'],
                    'fallbacks': [],
                    'description': 'Total company revenue',
                    'impact': 'Required for sales growth calculation'
                },
            },
            'important': {
                'long_term_debt': {
                    'sources': ['Long Term Debt', 'Total Debt'],
                    'fallbacks': ['Current Debt'],
                    'description': 'Long-term debt obligations',
                    'impact': 'Affects ROIC and debt payoff calculations'
                },
                'operating_cash_flow': {
                    'sources': ['Operating Cash Flow', 'Cash Flow From Operations'],
                    'fallbacks': [],
                    'description': 'Operating cash flow',
                    'impact': 'Required for FCF growth calculation'
                },
                'capital_expenditure': {
                    'sources': ['Capital Expenditure', 'CapEx'],
                    'fallbacks': [],
                    'description': 'Capital expenditures',
                    'impact': 'Required for free cash flow calculation'
                },
                'insider_ownership': {
                    'sources': ['heldPercentInsiders'],
                    'fallbacks': [],
                    'description': 'Insider ownership percentage',
                    'impact': 'Management quality indicator'
                },
            },
            'optional': {
                'dividend_yield': {
                    'sources': ['dividendYield'],
                    'fallbacks': [],
                    'description': 'Dividend yield',
                    'impact': 'Additional return component'
                },
            }
        },
        'high_growth': {
            'critical': {
                'total_revenue': {
                    'sources': ['Total Revenue', 'Revenue', 'Sales'],
                    'fallbacks': [],
                    'description': 'Total company revenue',
                    'impact': 'Required for sales growth analysis'
                },
                'net_income': {
                    'sources': ['Net Income', 'Net Income Common Stockholders', 'Net Income Continuous Operations'],
                    'fallbacks': [],
                    'description': 'Net income',
                    'impact': 'Required for net margin calculation'
                },
                'total_stockholder_equity': {
                    'sources': ['Stockholders Equity', 'Common Stock Equity', 'Total Equity Gross Minority Interest'],
                    'fallbacks': [],
                    'description': 'Total shareholder equity',
                    'impact': 'Required for ROE calculation'
                },
            },
            'important': {
                'ebitda': {
                    'sources': ['EBITDA', 'ebitda', 'Normalized EBITDA'],
                    'fallbacks': [],
                    'description': 'EBITDA',
                    'impact': 'Required for EV/EBITDA and debt ratios'
                },
                'total_debt': {
                    'sources': ['Total Debt', 'Long Term Debt'],
                    'fallbacks': [],
                    'description': 'Total debt',
                    'impact': 'Required for debt-to-EBITDA calculation'
                },
                'cash_and_cash_equivalents': {
                    'sources': ['Cash And Cash Equivalents', 'Cash'],
                    'fallbacks': [],
                    'description': 'Cash and equivalents',
                    'impact': 'Required for net debt calculation'
                },
                'market_cap': {
                    'sources': ['marketCap'],
                    'fallbacks': [],
                    'description': 'Market capitalization',
                    'impact': 'Required for valuation ratios'
                },
            },
            'optional': {
                'shares_outstanding': {
                    'sources': ['sharesOutstanding'],
                    'fallbacks': [],
                    'description': 'Shares outstanding',
                    'impact': 'Used for per-share calculations'
                },
                'insider_ownership': {
                    'sources': ['heldPercentInsiders'],
                    'fallbacks': [],
                    'description': 'Insider ownership percentage',
                    'impact': 'Management alignment indicator'
                },
            }
        }
    }
    
    def __init__(self):
        self.query_generator = SearchQueryGenerator()
    
    def analyze_gaps(self, stock_data: Dict[str, Any], ticker: str, strategy: str) -> DataGapAnalysis:
        """
        Analyze missing data points critical for strategy analysis.
        
        Args:
            stock_data: Stock data from data_fetcher
            ticker: Stock ticker symbol
            strategy: Analysis strategy (phil_town, high_growth)
            
        Returns:
            DataGapAnalysis object with missing fields categorized by importance
        """
        requirements = self.STRATEGY_REQUIREMENTS.get(strategy, {})
        
        analysis = DataGapAnalysis(
            strategy=strategy,
            ticker=ticker,
            critical_missing=[],
            important_missing=[],
            optional_missing=[],
            search_priority={},
            impact_assessment={}
        )
        
        # Check each category of requirements
        for category in ['critical', 'important', 'optional']:
            fields = requirements.get(category, {})
            missing_fields = getattr(analysis, f'{category}_missing')
            
            for field_name, field_info in fields.items():
                if not self._is_field_available(stock_data, field_info['sources'], field_info['fallbacks']):
                    missing_fields.append(field_name)
                    
                    # Set search priority based on category and field importance
                    priority = self.query_generator.get_search_priority(field_name, strategy)
                    if category == 'critical':
                        priority += 30
                    elif category == 'important':
                        priority += 15
                    
                    analysis.search_priority[field_name] = priority
                    analysis.impact_assessment[field_name] = field_info['impact']
        
        return analysis
    
    def assess_data_quality(self, stock_data: Dict[str, Any], gap_analysis: DataGapAnalysis) -> DataQualityAssessment:
        """
        Assess overall data quality and completeness.
        
        Args:
            stock_data: Stock data from data_fetcher
            gap_analysis: Data gap analysis results
            
        Returns:
            DataQualityAssessment with quality scores
        """
        # Calculate completeness score
        total_fields = (
            len(gap_analysis.critical_missing) + 
            len(gap_analysis.important_missing) + 
            len(gap_analysis.optional_missing)
        )
        
        strategy_requirements = self.STRATEGY_REQUIREMENTS.get(gap_analysis.strategy, {})
        total_required = sum(len(fields) for fields in strategy_requirements.values())
        
        if total_required == 0:
            completeness_score = 1.0
        else:
            available_fields = total_required - total_fields
            completeness_score = max(0.0, available_fields / total_required)
        
        # Adjust completeness based on critical vs optional missing
        critical_penalty = len(gap_analysis.critical_missing) * 0.15
        important_penalty = len(gap_analysis.important_missing) * 0.08
        optional_penalty = len(gap_analysis.optional_missing) * 0.03
        
        completeness_score = max(0.0, completeness_score - critical_penalty - important_penalty - optional_penalty)
        
        # Assess data source reliability
        reliability_score = self._assess_source_reliability(stock_data)
        
        # Determine data sources used
        data_sources = self._identify_data_sources(stock_data)
        
        return DataQualityAssessment(
            completeness_score=completeness_score,
            reliability_score=reliability_score,
            missing_critical_fields=gap_analysis.critical_missing,
            missing_optional_fields=gap_analysis.important_missing + gap_analysis.optional_missing,
            data_sources=data_sources
        )
    
    def _is_field_available(self, stock_data: Dict[str, Any], primary_sources: List[str], fallbacks: List[str]) -> bool:
        """Check if a field is available in the stock data."""
        all_sources = primary_sources + fallbacks
        
        # Check in info dict
        info = stock_data.get('info', {})
        for source in all_sources:
            if source in info and info[source] is not None:
                return True
        
        # Check in financial statements
        for statement in ['financials', 'balance_sheet', 'cash_flow']:
            df = stock_data.get(statement, pd.DataFrame())
            if not df.empty:
                for source in all_sources:
                    if source in df.index:
                        # Check if there's any non-null data
                        series = df.loc[source]
                        if series.notna().any():
                            return True
        
        return False
    
    def _assess_source_reliability(self, stock_data: Dict[str, Any]) -> float:
        """Assess the reliability of data sources."""
        base_score = 0.7  # Base reliability for primary sources
        
        # Check data freshness (newer data is more reliable)
        freshness_score = self._assess_data_freshness(stock_data)
        
        # Check data consistency across statements
        consistency_score = self._assess_data_consistency(stock_data)
        
        # Weight the factors
        reliability = (base_score * 0.5 + freshness_score * 0.3 + consistency_score * 0.2)
        
        return min(1.0, max(0.0, reliability))
    
    def _assess_data_freshness(self, stock_data: Dict[str, Any]) -> float:
        """Assess how fresh/recent the data is."""
        current_year = datetime.now().year
        freshness_score = 0.5  # Default score
        
        # Check financial statement dates
        for statement in ['financials', 'balance_sheet', 'cash_flow']:
            df = stock_data.get(statement, pd.DataFrame())
            if not df.empty and not df.columns.empty:
                try:
                    # Get the most recent date
                    latest_date = pd.to_datetime(df.columns[0])
                    years_old = current_year - latest_date.year
                    
                    if years_old == 0:
                        freshness_score = max(freshness_score, 1.0)
                    elif years_old == 1:
                        freshness_score = max(freshness_score, 0.8)
                    elif years_old == 2:
                        freshness_score = max(freshness_score, 0.6)
                    else:
                        freshness_score = max(freshness_score, 0.3)
                        
                except (ValueError, TypeError):
                    continue
        
        return freshness_score
    
    def _assess_data_consistency(self, stock_data: Dict[str, Any]) -> float:
        """Assess consistency of data across different sources."""
        consistency_score = 0.7  # Default score
        
        # Check if we have data from multiple statements
        available_statements = []
        for statement in ['financials', 'balance_sheet', 'cash_flow']:
            df = stock_data.get(statement, pd.DataFrame())
            if not df.empty:
                available_statements.append(statement)
        
        # More statements generally means more consistent data
        if len(available_statements) >= 3:
            consistency_score = 0.9
        elif len(available_statements) == 2:
            consistency_score = 0.8
        else:
            consistency_score = 0.6
        
        return consistency_score
    
    def _identify_data_sources(self, stock_data: Dict[str, Any]) -> Dict[str, str]:
        """Identify which data sources were used."""
        sources = {}
        
        # Primary data source is always yfinance
        sources['primary'] = 'yfinance'
        
        # Check if info dict has data (could be from fallback sources)
        info = stock_data.get('info', {})
        if info:
            sources['info'] = 'yfinance/finviz/investiny'
        
        # Check financial statements
        for statement in ['financials', 'balance_sheet', 'cash_flow']:
            df = stock_data.get(statement, pd.DataFrame())
            if not df.empty:
                sources[statement] = 'yfinance'
        
        return sources
    
    def get_search_recommendations(self, gap_analysis: DataGapAnalysis) -> Dict[str, List[str]]:
        """Get search query recommendations for missing fields."""
        recommendations = {}
        
        # Sort fields by priority
        all_missing = (
            gap_analysis.critical_missing + 
            gap_analysis.important_missing + 
            gap_analysis.optional_missing
        )
        
        sorted_fields = sorted(all_missing, 
                             key=lambda f: gap_analysis.search_priority.get(f, 0), 
                             reverse=True)
        
        for field in sorted_fields:
            queries = self.query_generator.generate_queries(
                gap_analysis.ticker, field, gap_analysis.strategy
            )
            recommendations[field] = queries[:3]  # Top 3 queries per field
        
        return recommendations