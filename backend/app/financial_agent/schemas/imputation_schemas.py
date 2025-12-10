"""
Pydantic schemas for web-based data imputation results and processes.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union, Any
from enum import Enum
from datetime import datetime


class ExtractionMethod(str, Enum):
    """Methods used for data extraction from web sources."""
    REGEX_PATTERN = "regex_pattern"
    HTML_TABLE = "html_table"
    JSON_API = "json_api"
    PDF_PARSING = "pdf_parsing"
    MANUAL_REVIEW = "manual_review"


class SourceType(str, Enum):
    """Types of web sources for financial data."""
    SEC_FILING = "sec_filing"
    FINANCIAL_WEBSITE = "financial_website"
    NEWS_ARTICLE = "news_article"
    ANALYST_REPORT = "analyst_report"
    COMPANY_PRESENTATION = "company_presentation"
    FORUM_DISCUSSION = "forum_discussion"
    ACADEMIC_PAPER = "academic_paper"
    GOVERNMENT_DATA = "government_data"


class SearchResult(BaseModel):
    """A single search result from web search."""
    url: str = Field(description="URL of the source")
    title: str = Field(description="Title of the web page")
    content: str = Field(description="Relevant text content")
    source_type: Optional[SourceType] = None
    credibility_score: Optional[float] = Field(default=None, description="Source credibility (0-1)")
    relevance_score: Optional[float] = Field(default=None, description="Relevance to query (0-1)")
    publish_date: Optional[datetime] = None
    extracted_values: List[Union[float, str]] = Field(default=[], description="Financial values extracted")
    extraction_confidence: Optional[float] = Field(default=None, description="Confidence in extraction (0-1)")


class ValidationResult(BaseModel):
    """Result of validating an imputed data point."""
    is_valid: bool = Field(description="Whether the data point passed validation")
    validation_score: float = Field(description="Validation confidence score (0-1)")
    validation_methods: List[str] = Field(default=[], description="Validation methods applied")
    cross_references: List[str] = Field(default=[], description="Cross-reference sources used")
    outlier_analysis: Optional[Dict[str, Any]] = None
    temporal_consistency: Optional[bool] = None
    industry_benchmark_check: Optional[Dict[str, Any]] = None
    validation_notes: Optional[str] = None


class ExtractedDataPoint(BaseModel):
    """A financial data point extracted from web content."""
    field_name: str = Field(description="Name of the financial field")
    raw_value: Union[str, float] = Field(description="Raw extracted value")
    normalized_value: Optional[float] = Field(description="Normalized numerical value")
    extraction_method: ExtractionMethod = Field(description="Method used for extraction")
    source_url: str = Field(description="URL of the source")
    source_context: str = Field(description="Surrounding text context")
    extraction_confidence: float = Field(description="Confidence in extraction (0-1)")
    validation_result: Optional[ValidationResult] = None
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")


class ImputationAttempt(BaseModel):
    """Record of an imputation attempt for a single field."""
    field_name: str
    ticker: str
    search_queries: List[str] = Field(description="Queries used for search")
    search_results: List[SearchResult] = Field(default=[])
    extracted_data_points: List[ExtractedDataPoint] = Field(default=[])
    final_value: Optional[Union[float, str]] = None
    confidence: float = Field(description="Overall confidence in imputed value (0-1)")
    success: bool = Field(description="Whether imputation was successful")
    failure_reasons: List[str] = Field(default=[], description="Reasons for failure if unsuccessful")
    processing_time_ms: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.now)


class FieldRequirement(BaseModel):
    """Requirement specification for a financial field."""
    field_name: str
    display_name: str
    required_for_strategies: List[str] = Field(description="Strategies that require this field")
    data_type: str = Field(description="Expected data type (float, percentage, currency, etc.)")
    typical_range: Optional[Dict[str, float]] = Field(description="Typical value range for validation")
    calculation_dependencies: List[str] = Field(default=[], description="Other fields needed for calculation")
    search_keywords: List[str] = Field(default=[], description="Keywords for web search")
    validation_rules: List[str] = Field(default=[], description="Validation rules to apply")
    criticality: str = Field(description="Critical/Important/Optional")


class ImputationStrategy(BaseModel):
    """Strategy configuration for data imputation."""
    name: str = Field(description="Strategy name")
    required_fields: List[FieldRequirement] = Field(description="Fields required by this strategy")
    field_priorities: Dict[str, int] = Field(description="Priority ranking of fields")
    fallback_calculations: Dict[str, str] = Field(default={}, description="Alternative calculation methods")
    quality_thresholds: Dict[str, float] = Field(default={}, description="Minimum quality thresholds")


class ImputationSession(BaseModel):
    """Complete imputation session for a ticker."""
    session_id: str = Field(description="Unique session identifier")
    ticker: str
    strategy: str
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    attempts: List[ImputationAttempt] = Field(default=[])
    overall_success_rate: float = Field(default=0.0)
    total_fields_requested: int = Field(default=0)
    successful_imputations: int = Field(default=0)
    session_summary: Optional[str] = None
    performance_metrics: Dict[str, Any] = Field(default={})


class ImputationResult(BaseModel):
    """Result of imputing a single data field."""
    field_name: str
    imputed_value: Optional[Union[float, str]] = None
    confidence: float = Field(description="Confidence in imputed value (0-1)")
    sources: List[str] = Field(default=[], description="URLs of data sources")
    alternative_values: List[Union[float, str]] = Field(default=[], description="Alternative values found")
    validation_notes: Optional[str] = Field(default=None)
    extraction_method: Optional[str] = Field(default=None)


class SearchSummary(BaseModel):
    """Summary of web search execution for a field."""
    field_name: str
    queries_executed: int
    sources_found: int
    extraction_success: bool
    search_duration_ms: Optional[int] = None
    errors: List[str] = Field(default=[])


class QualityMetrics(BaseModel):
    """Metrics for assessing imputation quality."""
    completeness: float = Field(description="Percentage of fields successfully imputed")
    accuracy: float = Field(description="Estimated accuracy of imputed values")
    reliability: float = Field(description="Reliability of data sources used")
    timeliness: float = Field(description="Recency of data sources")
    consistency: float = Field(description="Consistency across multiple sources")
    overall_quality: float = Field(description="Overall quality score")
    quality_notes: List[str] = Field(default=[], description="Notes about quality assessment")
