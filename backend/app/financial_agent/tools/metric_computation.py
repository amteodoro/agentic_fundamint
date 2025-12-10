"""
Enhanced metric computation tools with web-based data imputation capabilities.
"""

import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import logging

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from ..schemas.tool_schemas import MetricComputationInput, MetricComputationOutput, AnalysisStrategy
from ..schemas.metric_schemas import (
    FinancialMetric, PhilTownMetrics, HighGrowthMetrics, MetricType, DataSource,
    TrendAnalysis, InvestmentRecommendation, ComprehensiveAnalysis
)
from .data_analysis import DataGapAnalyzer
from .data_imputation import WebDataImputationTool
from ...data_fetcher import fetch_stock_data
from ...analysis import (
    calculate_roic_phil_town, get_growth_rates_phil_town, 
    calculate_management_metrics_phil_town, calculate_margin_of_safety_phil_town,
    analyze_high_growth_quality_strategy, clean_data
)

logger = logging.getLogger(__name__)


class EnhancedMetricCalculator:
    """Enhanced calculator that can compute metrics with imputed data."""
    
    def __init__(self, stock_data: Dict[str, Any], imputed_data: Optional[Dict[str, Any]] = None):
        self.original_data = stock_data
        self.imputed_data = imputed_data or {}
        self.enhanced_data = self._merge_data()
        self.confidence_scores = {}
        self.data_sources = {}
    
    def _merge_data(self) -> Dict[str, Any]:
        """Merge original data with imputed data."""
        enhanced = self.original_data.copy()
        
        if self.imputed_data:
            # Merge imputed values into the info dict
            if 'info' not in enhanced:
                enhanced['info'] = {}
            
            for field, imputation_result in self.imputed_data.items():
                if imputation_result.get('imputed_value') is not None:
                    enhanced['info'][field] = imputation_result['imputed_value']
                    logger.info(f"Merged imputed value for {field}: {imputation_result['imputed_value']}")
        
        return enhanced
    
    def calculate_phil_town_metrics(self) -> PhilTownMetrics:
        """Calculate Phil Town metrics with enhanced data."""
        logger.info("Calculating Phil Town metrics with enhanced data")
        
        # Calculate ROIC
        avg_roic, roic_annual = calculate_roic_phil_town(
            self.enhanced_data.get('financials', {}), 
            self.enhanced_data.get('balance_sheet', {})
        )
        
        roic_metric = FinancialMetric(
            name="Return on Invested Capital",
            type=MetricType.ROIC,
            value=avg_roic,
            historical_values=roic_annual or [],
            confidence=self._calculate_confidence('roic', avg_roic),
            data_sources=self._get_data_sources('roic'),
            calculation_method="NOPAT / Invested Capital",
            interpretation=self._interpret_roic(avg_roic)
        )
        
        # Calculate growth rates
        growth_rates = get_growth_rates_phil_town(self.enhanced_data)
        
        eps_growth_metric = FinancialMetric(
            name="EPS Growth Rate",
            type=MetricType.EPS_GROWTH,
            value=growth_rates.get('eps_cagr'),
            confidence=self._calculate_confidence('eps_growth', growth_rates.get('eps_cagr')),
            data_sources=self._get_data_sources('eps_growth'),
            calculation_method="CAGR of Diluted EPS",
            interpretation=self._interpret_growth_rate(growth_rates.get('eps_cagr'), "EPS")
        )
        
        sales_growth_metric = FinancialMetric(
            name="Sales Growth Rate",
            type=MetricType.SALES_GROWTH,
            value=growth_rates.get('sales_cagr'),
            confidence=self._calculate_confidence('sales_growth', growth_rates.get('sales_cagr')),
            data_sources=self._get_data_sources('sales_growth'),
            calculation_method="CAGR of Total Revenue",
            interpretation=self._interpret_growth_rate(growth_rates.get('sales_cagr'), "Sales")
        )
        
        bvps_growth_metric = FinancialMetric(
            name="Book Value Per Share Growth",
            type=MetricType.BVPS_GROWTH,
            value=growth_rates.get('bvps_cagr'),
            confidence=self._calculate_confidence('bvps_growth', growth_rates.get('bvps_cagr')),
            data_sources=self._get_data_sources('bvps_growth'),
            calculation_method="CAGR of BVPS (Equity/Shares)",
            interpretation=self._interpret_growth_rate(growth_rates.get('bvps_cagr'), "Book Value")
        )
        
        fcf_growth_metric = FinancialMetric(
            name="Free Cash Flow Growth",
            type=MetricType.FCF_GROWTH,
            value=growth_rates.get('fcf_cagr'),
            confidence=self._calculate_confidence('fcf_growth', growth_rates.get('fcf_cagr')),
            data_sources=self._get_data_sources('fcf_growth'),
            calculation_method="CAGR of FCF (Op Cash Flow - CapEx)",
            interpretation=self._interpret_growth_rate(growth_rates.get('fcf_cagr'), "Free Cash Flow")
        )
        
        # Management metrics
        mgmt_metrics = calculate_management_metrics_phil_town(self.enhanced_data)
        
        debt_payoff_metric = FinancialMetric(
            name="Debt Payoff Years",
            type=MetricType.DEBT_RATIO,
            value=mgmt_metrics.get('debt_payoff_years'),
            confidence=self._calculate_confidence('debt_payoff', mgmt_metrics.get('debt_payoff_years')),
            data_sources=self._get_data_sources('debt_payoff'),
            calculation_method="Long-term Debt / Free Cash Flow",
            interpretation=self._interpret_debt_payoff(mgmt_metrics.get('debt_payoff_years'))
        )
        
        insider_ownership_metric = FinancialMetric(
            name="Insider Ownership",
            type=MetricType.INSIDER_OWNERSHIP,
            value=mgmt_metrics.get('insider_ownership'),
            confidence=self._calculate_confidence('insider_ownership', mgmt_metrics.get('insider_ownership')),
            data_sources=self._get_data_sources('insider_ownership'),
            calculation_method="Percentage of shares held by insiders",
            interpretation=self._interpret_insider_ownership(mgmt_metrics.get('insider_ownership'))
        )
        
        # Margin of Safety
        mos_data = calculate_margin_of_safety_phil_town(self.enhanced_data, growth_rates)
        
        mos_metric = FinancialMetric(
            name="Margin of Safety",
            type=MetricType.MARGIN_OF_SAFETY,
            value=mos_data.get('mos_price'),
            confidence=self._calculate_confidence('margin_of_safety', mos_data.get('mos_price')),
            data_sources=self._get_data_sources('margin_of_safety'),
            calculation_method="Sticker Price * 0.5",
            interpretation=self._interpret_margin_of_safety(mos_data)
        )
        
        return PhilTownMetrics(
            roic=roic_metric,
            eps_growth=eps_growth_metric,
            sales_growth=sales_growth_metric,
            bvps_growth=bvps_growth_metric,
            fcf_growth=fcf_growth_metric,
            debt_payoff_years=debt_payoff_metric,
            insider_ownership=insider_ownership_metric,
            margin_of_safety=mos_metric,
            sticker_price=mos_data.get('sticker_price'),
            mos_price=mos_data.get('mos_price'),
            current_price=mos_data.get('current_market_price')
        )
    
    def calculate_high_growth_metrics(self, avg_roic: Optional[float] = None) -> HighGrowthMetrics:
        """Calculate High-Growth strategy metrics with enhanced data."""
        logger.info("Calculating High-Growth metrics with enhanced data")
        
        # Get high-growth analysis
        hg_analysis = analyze_high_growth_quality_strategy(self.enhanced_data, avg_roic)
        
        # Convert to structured metrics
        sales_growth_metric = FinancialMetric(
            name="Sales Growth (5Y)",
            type=MetricType.SALES_GROWTH,
            value=hg_analysis.get('sales_cagr_hg'),
            confidence=self._calculate_confidence('sales_growth_hg', hg_analysis.get('sales_cagr_hg')),
            data_sources=self._get_data_sources('sales_growth'),
            calculation_method="5-Year CAGR of Revenue",
            interpretation=self._interpret_growth_rate(hg_analysis.get('sales_cagr_hg'), "Sales")
        )
        
        net_margin_metric = FinancialMetric(
            name="Net Profit Margin",
            type=MetricType.NET_MARGIN,
            value=hg_analysis.get('current_net_margin'),
            historical_values=hg_analysis.get('net_margins_historical', []),
            confidence=self._calculate_confidence('net_margin', hg_analysis.get('current_net_margin')),
            data_sources=self._get_data_sources('net_margin'),
            calculation_method="Net Income / Total Revenue",
            interpretation=self._interpret_margin(hg_analysis.get('current_net_margin'))
        )
        
        roe_metric = FinancialMetric(
            name="Return on Equity",
            type=MetricType.ROE,
            value=hg_analysis.get('latest_roe'),
            confidence=self._calculate_confidence('roe', hg_analysis.get('latest_roe')),
            data_sources=self._get_data_sources('roe'),
            calculation_method="Net Income / Shareholder Equity",
            interpretation=self._interpret_roe(hg_analysis.get('latest_roe'))
        )
        
        roic_metric = FinancialMetric(
            name="Return on Invested Capital",
            type=MetricType.ROIC,
            value=hg_analysis.get('avg_roic'),
            confidence=self._calculate_confidence('roic', hg_analysis.get('avg_roic')),
            data_sources=self._get_data_sources('roic'),
            calculation_method="NOPAT / Invested Capital",
            interpretation=self._interpret_roic(hg_analysis.get('avg_roic'))
        )
        
        debt_to_ebitda_metric = FinancialMetric(
            name="Net Debt to EBITDA",
            type=MetricType.DEBT_RATIO,
            value=hg_analysis.get('net_debt_to_ebitda'),
            confidence=self._calculate_confidence('debt_to_ebitda', hg_analysis.get('net_debt_to_ebitda')),
            data_sources=self._get_data_sources('debt_to_ebitda'),
            calculation_method="Net Debt / EBITDA",
            interpretation=self._interpret_debt_ratio(hg_analysis.get('net_debt_to_ebitda'))
        )
        
        psr_metric = FinancialMetric(
            name="Price to Sales Ratio",
            type=MetricType.PSR_RATIO,
            value=hg_analysis.get('current_psr'),
            confidence=self._calculate_confidence('psr', hg_analysis.get('current_psr')),
            data_sources=self._get_data_sources('psr'),
            calculation_method="Market Cap / Revenue (TTM)",
            interpretation=self._interpret_valuation_ratio(hg_analysis.get('current_psr'), "PSR")
        )
        
        per_metric = FinancialMetric(
            name="Price to Earnings Ratio",
            type=MetricType.PE_RATIO,
            value=hg_analysis.get('current_per'),
            confidence=self._calculate_confidence('per', hg_analysis.get('current_per')),
            data_sources=self._get_data_sources('per'),
            calculation_method="Price / Earnings per Share (TTM)",
            interpretation=self._interpret_valuation_ratio(hg_analysis.get('current_per'), "P/E")
        )
        
        ev_ebitda_metric = FinancialMetric(
            name="EV to EBITDA",
            type=MetricType.EV_EBITDA,
            value=hg_analysis.get('ev_to_ebitda'),
            confidence=self._calculate_confidence('ev_ebitda', hg_analysis.get('ev_to_ebitda')),
            data_sources=self._get_data_sources('ev_ebitda'),
            calculation_method="Enterprise Value / EBITDA",
            interpretation=self._interpret_valuation_ratio(hg_analysis.get('ev_to_ebitda'), "EV/EBITDA")
        )
        
        insider_ownership_metric = FinancialMetric(
            name="Insider Ownership",
            type=MetricType.INSIDER_OWNERSHIP,
            value=hg_analysis.get('insider_ownership_hg'),
            confidence=self._calculate_confidence('insider_ownership', hg_analysis.get('insider_ownership_hg')),
            data_sources=self._get_data_sources('insider_ownership'),
            calculation_method="Percentage of shares held by insiders",
            interpretation=self._interpret_insider_ownership(hg_analysis.get('insider_ownership_hg'))
        )
        
        dividend_metric = None
        if hg_analysis.get('dividend_yield') is not None:
            dividend_metric = FinancialMetric(
                name="Dividend Yield",
                type=MetricType.DEBT_RATIO,  # Using DEBT_RATIO as placeholder
                value=hg_analysis.get('dividend_yield'),
                confidence=self._calculate_confidence('dividend_yield', hg_analysis.get('dividend_yield')),
                data_sources=self._get_data_sources('dividend_yield'),
                calculation_method="Annual Dividend / Stock Price",
                interpretation=self._interpret_dividend_yield(hg_analysis.get('dividend_yield'))
            )
        
        return HighGrowthMetrics(
            sales_growth=sales_growth_metric,
            net_margin=net_margin_metric,
            net_margin_trend=hg_analysis.get('net_margin_trend', 'N/A'),
            roe=roe_metric,
            roic=roic_metric,
            debt_to_ebitda=debt_to_ebitda_metric,
            psr_ratio=psr_metric,
            per_ratio=per_metric,
            ev_ebitda=ev_ebitda_metric,
            insider_ownership=insider_ownership_metric,
            dividend_yield=dividend_metric,
            pays_dividends=hg_analysis.get('pays_dividends', False)
        )
    
    def _calculate_confidence(self, metric_name: str, value: Optional[float]) -> float:
        """Calculate confidence score for a metric."""
        if value is None:
            return 0.0
        
        base_confidence = 0.8  # Base confidence for original data
        
        # Check if this metric was imputed
        if metric_name in self.imputed_data:
            imputation_confidence = self.imputed_data[metric_name].get('confidence', 0.0)
            return imputation_confidence
        
        return base_confidence
    
    def _get_data_sources(self, metric_name: str) -> List[DataSource]:
        """Get data sources used for a metric."""
        sources = [DataSource.YFINANCE]  # Default primary source
        
        if metric_name in self.imputed_data:
            sources.append(DataSource.WEB_SEARCH)
        
        return sources
    
    # Interpretation methods
    def _interpret_roic(self, value: Optional[float]) -> Optional[str]:
        """Interpret ROIC value."""
        if value is None:
            return None
        
        if value > 0.15:
            return "Excellent: Strong returns on invested capital"
        elif value > 0.10:
            return "Good: Above-average capital efficiency"
        elif value > 0.05:
            return "Fair: Moderate capital returns"
        else:
            return "Poor: Low returns on invested capital"
    
    def _interpret_growth_rate(self, value: Optional[float], metric_type: str) -> Optional[str]:
        """Interpret growth rate values."""
        if value is None:
            return None
        
        if value > 0.15:
            return f"Excellent: Strong {metric_type} growth"
        elif value > 0.08:
            return f"Good: Solid {metric_type} growth"
        elif value > 0.03:
            return f"Fair: Moderate {metric_type} growth"
        elif value > 0:
            return f"Weak: Slow {metric_type} growth"
        else:
            return f"Poor: Declining {metric_type}"
    
    def _interpret_debt_payoff(self, value: Optional[float]) -> Optional[str]:
        """Interpret debt payoff years."""
        if value is None:
            return None
        
        if value < 3:
            return "Excellent: Can pay off debt quickly"
        elif value < 5:
            return "Good: Reasonable debt payoff timeline"
        elif value < 10:
            return "Fair: Moderate debt burden"
        else:
            return "Poor: High debt burden"
    
    def _interpret_insider_ownership(self, value: Optional[float]) -> Optional[str]:
        """Interpret insider ownership percentage."""
        if value is None:
            return None
        
        if value > 0.15:
            return "Excellent: High management alignment"
        elif value > 0.05:
            return "Good: Solid insider ownership"
        elif value > 0.01:
            return "Fair: Some management ownership"
        else:
            return "Poor: Low insider ownership"
    
    def _interpret_margin_of_safety(self, mos_data: Dict[str, Any]) -> Optional[str]:
        """Interpret margin of safety calculation."""
        current_price = mos_data.get('current_market_price')
        mos_price = mos_data.get('mos_price')
        
        if current_price is None or mos_price is None:
            return None
        
        if current_price <= mos_price:
            return "Excellent: Trading at or below margin of safety"
        elif current_price <= mos_price * 1.2:
            return "Good: Close to margin of safety price"
        elif current_price <= mos_data.get('sticker_price', float('inf')):
            return "Fair: Below intrinsic value but above MOS"
        else:
            return "Poor: Trading above intrinsic value"
    
    def _interpret_margin(self, value: Optional[float]) -> Optional[str]:
        """Interpret profit margin."""
        if value is None:
            return None
        
        if value > 0.20:
            return "Excellent: High profit margins"
        elif value > 0.10:
            return "Good: Strong profitability"
        elif value > 0.05:
            return "Fair: Adequate margins"
        else:
            return "Poor: Low profit margins"
    
    def _interpret_roe(self, value: Optional[float]) -> Optional[str]:
        """Interpret Return on Equity."""
        if value is None:
            return None
        
        if value > 0.20:
            return "Excellent: High returns on equity"
        elif value > 0.15:
            return "Good: Strong equity returns"
        elif value > 0.10:
            return "Fair: Adequate returns"
        else:
            return "Poor: Low equity returns"
    
    def _interpret_debt_ratio(self, value: Optional[float]) -> Optional[str]:
        """Interpret debt-to-EBITDA ratio."""
        if value is None:
            return None
        
        if value < 2:
            return "Excellent: Low debt burden"
        elif value < 3:
            return "Good: Manageable debt levels"
        elif value < 4:
            return "Fair: Moderate debt burden"
        else:
            return "Poor: High debt burden"
    
    def _interpret_valuation_ratio(self, value: Optional[float], ratio_type: str) -> Optional[str]:
        """Interpret valuation ratios."""
        if value is None:
            return None
        
        if ratio_type == "PSR":
            if value < 1:
                return "Cheap: Low price relative to sales"
            elif value < 3:
                return "Fair: Reasonable valuation"
            else:
                return "Expensive: High price relative to sales"
        elif ratio_type == "P/E":
            if value < 15:
                return "Cheap: Low earnings multiple"
            elif value < 25:
                return "Fair: Reasonable valuation"
            else:
                return "Expensive: High earnings multiple"
        elif ratio_type == "EV/EBITDA":
            if value < 10:
                return "Cheap: Low enterprise value multiple"
            elif value < 15:
                return "Fair: Reasonable valuation"
            else:
                return "Expensive: High enterprise value multiple"
        
        return None
    
    def _interpret_dividend_yield(self, value: Optional[float]) -> Optional[str]:
        """Interpret dividend yield."""
        if value is None:
            return None
        
        if value > 0.04:
            return "High: Strong dividend income"
        elif value > 0.02:
            return "Moderate: Decent dividend yield"
        elif value > 0:
            return "Low: Small dividend yield"
        else:
            return "None: No dividend payments"


class PhilTownAnalysisWithImputation(BaseTool):
    """Performs comprehensive Phil Town analysis with intelligent data imputation."""
    
    name: str = "phil_town_analysis_complete"
    description: str = """
    Performs comprehensive Phil Town analysis with intelligent data imputation.
    Uses web search to fill critical data gaps when local data is insufficient.
    
    Analyzes: ROIC, growth rates (EPS, Sales, FCF, BVPS), debt payoff years,
    insider ownership, and margin of safety calculations.
    """
    args_schema: type = MetricComputationInput
    imputation_tool: Optional[Any] = Field(default=None, exclude=True)
    gap_analyzer: Optional[Any] = Field(default=None, exclude=True)
    
    def __init__(self, tavily_tool=None, **kwargs):
        super().__init__(**kwargs)
        self.imputation_tool = WebDataImputationTool(tavily_tool)
        self.gap_analyzer = DataGapAnalyzer()
    
    async def _arun(self, ticker: str, strategy: AnalysisStrategy = AnalysisStrategy.PHIL_TOWN,
                   enable_web_search: bool = True, years_back: Optional[int] = 10) -> Dict[str, Any]:
        """Execute Phil Town analysis with imputation."""
        logger.info(f"Starting Phil Town analysis for {ticker}")
        
        # Step 1: Fetch primary data
        stock_data = fetch_stock_data(ticker)
        
        # Step 2: Analyze data completeness
        gap_analysis = self.gap_analyzer.analyze_gaps(stock_data, ticker, strategy.value)
        data_quality = self.gap_analyzer.assess_data_quality(stock_data, gap_analysis)
        
        result = MetricComputationOutput(
            ticker=ticker,
            strategy=strategy,
            primary_data_quality=data_quality,
            imputation_attempted=False,
            data_sources={'primary': ['yfinance']}
        )
        
        # Step 3: Web imputation if enabled and needed
        imputed_data = {}
        if enable_web_search and gap_analysis.critical_missing:
            result.imputation_attempted = True
            logger.info(f"Attempting imputation for critical fields: {gap_analysis.critical_missing}")
            
            try:
                imputation_response = await self.imputation_tool._arun(
                    ticker=ticker,
                    missing_fields=gap_analysis.critical_missing,
                    strategy_context="phil_town"
                )
                result.imputation_results = imputation_response
                
                # Extract successful imputations
                for field, imputation_result in imputation_response.get('imputation_results', {}).items():
                    if imputation_result.get('imputed_value') is not None:
                        imputed_data[field] = imputation_result
                        result.data_sources.setdefault('web', []).extend(imputation_result.get('sources', []))
                
                logger.info(f"Successfully imputed {len(imputed_data)} fields")
                
            except Exception as e:
                logger.error(f"Error during imputation: {e}")
                result.imputation_results = {'error': str(e)}
        
        # Step 4: Calculate metrics with enhanced data
        try:
            calculator = EnhancedMetricCalculator(stock_data, imputed_data)
            phil_town_metrics = calculator.calculate_phil_town_metrics()
            
            result.final_metrics = {
                'phil_town': phil_town_metrics.model_dump()
            }
            
            # Generate confidence scores
            for metric_name, metric in phil_town_metrics.model_dump().items():
                if isinstance(metric, dict) and 'confidence' in metric:
                    result.confidence_scores[metric_name] = {
                        'overall_confidence': metric['confidence'],
                        'data_quality': data_quality.completeness_score,
                        'calculation_reliability': 0.9,  # High for established calculations
                        'source_credibility': data_quality.reliability_score
                    }
            
            # Generate analysis summary
            result.analysis_summary = self._generate_phil_town_summary(phil_town_metrics, gap_analysis)
            
            # Generate recommendations
            result.recommendations = self._generate_phil_town_recommendations(phil_town_metrics)
            
            logger.info("Phil Town analysis completed successfully")
            
        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")
            result.final_metrics = {'error': str(e)}
        
        return result.model_dump()
    
    def _run(self, *args, **kwargs):
        """Synchronous wrapper for the async implementation."""
        return asyncio.run(self._arun(*args, **kwargs))
    
    def _generate_phil_town_summary(self, metrics: PhilTownMetrics, gap_analysis) -> str:
        """Generate analysis summary."""
        summary_parts = []
        
        # ROIC assessment
        if metrics.roic.value is not None:
            roic_pct = metrics.roic.value * 100
            summary_parts.append(f"ROIC: {roic_pct:.1f}% - {metrics.roic.interpretation}")
        
        # Growth assessment
        growth_metrics = [
            (metrics.eps_growth, "EPS"),
            (metrics.sales_growth, "Sales"),
            (metrics.fcf_growth, "FCF")
        ]
        
        growth_summary = []
        for metric, name in growth_metrics:
            if metric.value is not None:
                growth_pct = metric.value * 100
                growth_summary.append(f"{name}: {growth_pct:.1f}%")
        
        if growth_summary:
            summary_parts.append(f"Growth rates - {', '.join(growth_summary)}")
        
        # Margin of Safety
        if metrics.margin_of_safety.value is not None:
            summary_parts.append(f"MOS Price: ${metrics.margin_of_safety.value:.2f} - {metrics.margin_of_safety.interpretation}")
        
        # Data quality note
        if gap_analysis.critical_missing:
            missing_fields = ", ".join(gap_analysis.critical_missing)
            summary_parts.append(f"Note: {len(gap_analysis.critical_missing)} critical fields required web imputation ({missing_fields})")
        
        return ". ".join(summary_parts)
    
    def _generate_phil_town_recommendations(self, metrics: PhilTownMetrics) -> List[str]:
        """Generate investment recommendations."""
        recommendations = []
        
        # ROIC recommendation
        if metrics.roic.value and metrics.roic.value > 0.15:
            recommendations.append("Strong ROIC indicates excellent capital efficiency")
        elif metrics.roic.value and metrics.roic.value < 0.08:
            recommendations.append("Low ROIC suggests poor capital allocation - investigate further")
        
        # Growth recommendation
        growth_values = [m.value for m in [metrics.eps_growth, metrics.sales_growth] if m.value is not None]
        if growth_values:
            avg_growth = sum(growth_values) / len(growth_values)
            if avg_growth > 0.10:
                recommendations.append("Strong growth rates support long-term value creation")
            elif avg_growth < 0.03:
                recommendations.append("Weak growth rates may limit future returns")
        
        # Margin of Safety
        if metrics.margin_of_safety.value and metrics.current_price:
            if metrics.current_price <= metrics.margin_of_safety.value:
                recommendations.append("Trading at attractive margin of safety - consider buying")
            else:
                recommendations.append("Current price above margin of safety - wait for better entry")
        
        # Management quality
        if metrics.insider_ownership.value and metrics.insider_ownership.value > 0.10:
            recommendations.append("High insider ownership indicates strong management alignment")
        
        return recommendations


class HighGrowthAnalysisWithImputation(BaseTool):
    """Performs comprehensive High-Growth analysis with intelligent data imputation."""
    
    name: str = "high_growth_analysis_complete"
    description: str = """
    Performs comprehensive High-Growth analysis with intelligent data imputation.
    Uses web search to fill critical data gaps when local data is insufficient.
    
    Analyzes: sales growth, net margins, ROE/ROIC, debt ratios, valuation metrics,
    and dividend policies for growth-oriented investments.
    """
    args_schema: type = MetricComputationInput
    imputation_tool: Optional[Any] = Field(default=None, exclude=True)
    gap_analyzer: Optional[Any] = Field(default=None, exclude=True)
    
    def __init__(self, tavily_tool=None, **kwargs):
        super().__init__(**kwargs)
        self.imputation_tool = WebDataImputationTool(tavily_tool)
        self.gap_analyzer = DataGapAnalyzer()
    
    async def _arun(self, ticker: str, strategy: AnalysisStrategy = AnalysisStrategy.HIGH_GROWTH,
                   enable_web_search: bool = True, years_back: Optional[int] = 10) -> Dict[str, Any]:
        """Execute High-Growth analysis with imputation."""
        logger.info(f"Starting High-Growth analysis for {ticker}")
        
        # Step 1: Fetch primary data
        stock_data = fetch_stock_data(ticker)
        
        # Step 2: Analyze data completeness
        gap_analysis = self.gap_analyzer.analyze_gaps(stock_data, ticker, strategy.value)
        data_quality = self.gap_analyzer.assess_data_quality(stock_data, gap_analysis)
        
        result = MetricComputationOutput(
            ticker=ticker,
            strategy=strategy,
            primary_data_quality=data_quality,
            imputation_attempted=False,
            data_sources={'primary': ['yfinance']}
        )
        
        # Step 3: Web imputation if enabled and needed
        imputed_data = {}
        if enable_web_search and gap_analysis.critical_missing:
            result.imputation_attempted = True
            logger.info(f"Attempting imputation for critical fields: {gap_analysis.critical_missing}")
            
            try:
                imputation_response = await self.imputation_tool._arun(
                    ticker=ticker,
                    missing_fields=gap_analysis.critical_missing,
                    strategy_context="high_growth"
                )
                result.imputation_results = imputation_response
                
                # Extract successful imputations
                for field, imputation_result in imputation_response.get('imputation_results', {}).items():
                    if imputation_result.get('imputed_value') is not None:
                        imputed_data[field] = imputation_result
                        result.data_sources.setdefault('web', []).extend(imputation_result.get('sources', []))
                
                logger.info(f"Successfully imputed {len(imputed_data)} fields")
                
            except Exception as e:
                logger.error(f"Error during imputation: {e}")
                result.imputation_results = {'error': str(e)}
        
        # Step 4: Calculate metrics with enhanced data
        try:
            calculator = EnhancedMetricCalculator(stock_data, imputed_data)
            
            # First calculate any needed ROIC for high-growth analysis
            phil_town_metrics = calculator.calculate_phil_town_metrics()
            avg_roic = phil_town_metrics.roic.value
            
            # Then calculate high-growth specific metrics
            high_growth_metrics = calculator.calculate_high_growth_metrics(avg_roic)
            
            result.final_metrics = {
                'high_growth': high_growth_metrics.model_dump()
            }
            
            # Generate confidence scores
            for metric_name, metric in high_growth_metrics.model_dump().items():
                if isinstance(metric, dict) and 'confidence' in metric:
                    result.confidence_scores[metric_name] = {
                        'overall_confidence': metric['confidence'],
                        'data_quality': data_quality.completeness_score,
                        'calculation_reliability': 0.9,
                        'source_credibility': data_quality.reliability_score
                    }
            
            # Generate analysis summary
            result.analysis_summary = self._generate_high_growth_summary(high_growth_metrics, gap_analysis)
            
            # Generate recommendations
            result.recommendations = self._generate_high_growth_recommendations(high_growth_metrics)
            
            logger.info("High-Growth analysis completed successfully")
            
        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")
            result.final_metrics = {'error': str(e)}
        
        return result.model_dump()
    
    def _run(self, *args, **kwargs):
        """Synchronous wrapper for the async implementation."""
        return asyncio.run(self._arun(*args, **kwargs))
    
    def _generate_high_growth_summary(self, metrics: HighGrowthMetrics, gap_analysis) -> str:
        """Generate analysis summary."""
        summary_parts = []
        
        # Sales growth assessment
        if metrics.sales_growth.value is not None:
            growth_pct = metrics.sales_growth.value * 100
            summary_parts.append(f"Sales Growth: {growth_pct:.1f}% - {metrics.sales_growth.interpretation}")
        
        # Profitability assessment
        if metrics.net_margin.value is not None:
            margin_pct = metrics.net_margin.value * 100
            summary_parts.append(f"Net Margin: {margin_pct:.1f}% ({metrics.net_margin_trend}) - {metrics.net_margin.interpretation}")
        
        # Returns assessment
        if metrics.roe.value is not None:
            roe_pct = metrics.roe.value * 100
            summary_parts.append(f"ROE: {roe_pct:.1f}% - {metrics.roe.interpretation}")
        
        # Valuation assessment
        if metrics.per_ratio.value is not None:
            summary_parts.append(f"P/E: {metrics.per_ratio.value:.1f} - {metrics.per_ratio.interpretation}")
        
        # Data quality note
        if gap_analysis.critical_missing:
            missing_fields = ", ".join(gap_analysis.critical_missing)
            summary_parts.append(f"Note: {len(gap_analysis.critical_missing)} critical fields required web imputation ({missing_fields})")
        
        return ". ".join(summary_parts)
    
    def _generate_high_growth_recommendations(self, metrics: HighGrowthMetrics) -> List[str]:
        """Generate investment recommendations."""
        recommendations = []
        
        # Growth recommendation
        if metrics.sales_growth.value and metrics.sales_growth.value > 0.15:
            recommendations.append("Strong sales growth indicates expanding market share")
        elif metrics.sales_growth.value and metrics.sales_growth.value < 0.05:
            recommendations.append("Weak sales growth raises concerns about competitive position")
        
        # Profitability trend
        if metrics.net_margin_trend == "Expanding":
            recommendations.append("Expanding margins show improving operational efficiency")
        elif metrics.net_margin_trend == "Contracting":
            recommendations.append("Contracting margins warrant investigation into cost management")
        
        # Financial health
        if metrics.debt_to_ebitda.value and metrics.debt_to_ebitda.value < 2:
            recommendations.append("Low debt levels provide financial flexibility for growth")
        elif metrics.debt_to_ebitda.value and metrics.debt_to_ebitda.value > 4:
            recommendations.append("High debt levels may constrain growth investments")
        
        # Valuation
        if metrics.psr_ratio.value and metrics.psr_ratio.value < 2:
            recommendations.append("Reasonable valuation relative to sales")
        elif metrics.psr_ratio.value and metrics.psr_ratio.value > 5:
            recommendations.append("High valuation requires strong execution to justify")
        
        return recommendations