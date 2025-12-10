"""
Pydantic schemas for financial metrics and analysis results.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from enum import Enum


class MetricType(str, Enum):
    """Types of financial metrics."""
    ROIC = "roic"
    EPS_GROWTH = "eps_growth"
    SALES_GROWTH = "sales_growth"
    FCF_GROWTH = "fcf_growth"
    BVPS_GROWTH = "bvps_growth"
    NET_MARGIN = "net_margin"
    DEBT_RATIO = "debt_ratio"
    ROE = "roe"
    PE_RATIO = "pe_ratio"
    PSR_RATIO = "psr_ratio"
    EV_EBITDA = "ev_ebitda"
    INSIDER_OWNERSHIP = "insider_ownership"
    MARGIN_OF_SAFETY = "margin_of_safety"


class DataSource(str, Enum):
    """Sources of financial data."""
    YFINANCE = "yfinance"
    FINVIZ = "finviz"
    INVESTINY = "investiny"
    WEB_SEARCH = "web_search"
    SEC_FILING = "sec_filing"
    ANALYST_REPORT = "analyst_report"
    COMPANY_WEBSITE = "company_website"


class FinancialMetric(BaseModel):
    """A single financial metric with metadata."""
    name: str = Field(description="Metric name")
    type: MetricType = Field(description="Type of metric")
    value: Optional[float] = Field(description="Calculated metric value")
    historical_values: List[float] = Field(default=[], description="Historical values for trend analysis")
    confidence: float = Field(description="Confidence in the metric calculation (0-1)")
    data_sources: List[DataSource] = Field(default=[], description="Sources used for calculation")
    calculation_method: Optional[str] = Field(default=None, description="Method used for calculation")
    missing_components: List[str] = Field(default=[], description="Missing data components")
    alternative_calculations: List[Dict[str, Any]] = Field(default=[], description="Alternative calculation methods tried")
    interpretation: Optional[str] = Field(default=None, description="Interpretation of the metric value")
    benchmark_comparison: Optional[Dict[str, float]] = Field(default=None, description="Comparison to benchmarks")


class PhilTownMetrics(BaseModel):
    """Phil Town strategy specific metrics."""
    roic: FinancialMetric
    eps_growth: FinancialMetric
    sales_growth: FinancialMetric
    bvps_growth: FinancialMetric
    fcf_growth: FinancialMetric
    debt_payoff_years: FinancialMetric
    insider_ownership: FinancialMetric
    margin_of_safety: FinancialMetric
    sticker_price: Optional[float] = Field(default=None, description="Calculated sticker price")
    mos_price: Optional[float] = Field(default=None, description="Margin of safety price")
    current_price: Optional[float] = Field(default=None, description="Current market price")


class HighGrowthMetrics(BaseModel):
    """High-Growth strategy specific metrics."""
    sales_growth: FinancialMetric
    net_margin: FinancialMetric
    net_margin_trend: str = Field(description="Trend direction (expanding/contracting/stable)")
    roe: FinancialMetric
    roic: FinancialMetric
    debt_to_ebitda: FinancialMetric
    psr_ratio: FinancialMetric
    per_ratio: FinancialMetric
    ev_ebitda: FinancialMetric
    insider_ownership: FinancialMetric
    dividend_yield: Optional[FinancialMetric] = Field(default=None)
    pays_dividends: bool = Field(default=False)


class DataGapAnalysis(BaseModel):
    """Analysis of missing data points for a strategy."""
    strategy: str = Field(description="Analysis strategy")
    ticker: str = Field(description="Stock ticker")
    critical_missing: List[str] = Field(default=[], description="Critical missing fields that prevent analysis")
    important_missing: List[str] = Field(default=[], description="Important missing fields that reduce quality")
    optional_missing: List[str] = Field(default=[], description="Optional missing fields")
    search_priority: Dict[str, int] = Field(default={}, description="Search priority ranking for each field")
    impact_assessment: Dict[str, str] = Field(default={}, description="Impact of each missing field")


class TrendAnalysis(BaseModel):
    """Analysis of metric trends over time."""
    metric_name: str
    direction: str = Field(description="Trend direction (improving/declining/stable)")
    strength: float = Field(description="Strength of trend (0-1)")
    consistency: float = Field(description="Consistency of trend (0-1)")
    inflection_points: List[str] = Field(default=[], description="Dates of significant changes")
    forecast: Optional[Dict[str, float]] = Field(default=None, description="Future trend forecast")


class InvestmentRecommendation(BaseModel):
    """Investment recommendation based on analysis."""
    recommendation: str = Field(description="Buy/Hold/Sell recommendation")
    confidence: float = Field(description="Confidence in recommendation (0-1)")
    reasoning: List[str] = Field(default=[], description="Key reasons for recommendation")
    risk_factors: List[str] = Field(default=[], description="Identified risk factors")
    strengths: List[str] = Field(default=[], description="Company strengths identified")
    price_targets: Optional[Dict[str, float]] = Field(default=None, description="Price targets (conservative/optimistic)")
    time_horizon: Optional[str] = Field(default=None, description="Recommended holding period")


class ComprehensiveAnalysis(BaseModel):
    """Complete analysis results combining all strategies."""
    ticker: str
    company_name: Optional[str] = None
    analysis_date: str = Field(description="Date of analysis")
    phil_town_metrics: Optional[PhilTownMetrics] = None
    high_growth_metrics: Optional[HighGrowthMetrics] = None
    data_gap_analysis: DataGapAnalysis
    trend_analysis: List[TrendAnalysis] = Field(default=[])
    recommendation: InvestmentRecommendation
    overall_confidence: float = Field(description="Overall confidence in analysis (0-1)")
    data_quality_score: float = Field(description="Overall data quality score (0-1)")
    execution_summary: Dict[str, Any] = Field(default={}, description="Summary of analysis execution")