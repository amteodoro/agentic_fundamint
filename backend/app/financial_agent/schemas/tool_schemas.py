"""
Pydantic schemas for financial analysis tool inputs and outputs.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from enum import Enum

from .imputation_schemas import ImputationResult, SearchSummary, QualityMetrics


class AnalysisStrategy(str, Enum):
    """Supported financial analysis strategies."""
    PHIL_TOWN = "phil_town"
    HIGH_GROWTH = "high_growth"


class MetricComputationInput(BaseModel):
    """Input schema for metric computation tools."""
    ticker: str = Field(description="Stock ticker symbol")
    strategy: AnalysisStrategy = Field(description="Analysis strategy to use")
    enable_web_search: bool = Field(default=True, description="Whether to enable web-based data imputation")
    years_back: Optional[int] = Field(default=10, description="Years of historical data to analyze")


class ImputationInput(BaseModel):
    """Input schema for web data imputation tool."""
    ticker: str = Field(description="Stock ticker symbol")
    missing_fields: List[str] = Field(description="List of missing financial data fields")
    strategy_context: Optional[str] = Field(default=None, description="Analysis strategy context")
    max_search_results: Optional[int] = Field(default=10, description="Maximum search results per query")


class DataQualityAssessment(BaseModel):
    """Assessment of data quality and completeness."""
    completeness_score: float = Field(description="Data completeness score (0-1)")
    reliability_score: float = Field(description="Data reliability score (0-1)")
    missing_critical_fields: List[str] = Field(default=[], description="Critical missing fields")
    missing_optional_fields: List[str] = Field(default=[], description="Optional missing fields")
    data_sources: Dict[str, str] = Field(default={}, description="Data sources used")


class ConfidenceScore(BaseModel):
    """Confidence scoring for calculated metrics."""
    overall_confidence: float = Field(description="Overall confidence in metric calculation (0-1)")
    data_quality: float = Field(description="Data quality score (0-1)")
    calculation_reliability: float = Field(description="Calculation method reliability (0-1)")
    source_credibility: float = Field(description="Source credibility score (0-1)")
    notes: Optional[str] = Field(default=None, description="Additional notes about confidence")


class MetricComputationOutput(BaseModel):
    """Output schema for metric computation tools."""
    ticker: str
    strategy: AnalysisStrategy
    primary_data_quality: DataQualityAssessment
    imputation_attempted: bool
    imputation_results: Dict[str, Any] = Field(default={})
    final_metrics: Dict[str, Any] = Field(default={})
    confidence_scores: Dict[str, ConfidenceScore] = Field(default={})
    analysis_summary: Optional[str] = Field(default=None)
    recommendations: List[str] = Field(default=[])
    data_sources: Dict[str, List[str]] = Field(default={})


class ImputationOutput(BaseModel):
    """Output schema for web data imputation tool."""
    ticker: str
    requested_fields: List[str]
    strategy_context: Optional[str]
    imputation_results: Dict[str, ImputationResult] = Field(default={})
    search_summary: Dict[str, SearchSummary] = Field(default={})
    data_quality_assessment: QualityMetrics
    overall_success_rate: float = Field(description="Percentage of fields successfully imputed")
    execution_time_ms: Optional[int] = None
