"""
Web-based data imputation tools using Tavily search for missing financial data.
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Union
import logging
from datetime import datetime
import uuid

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from ..schemas.tool_schemas import ImputationInput, ImputationOutput
from ..schemas.imputation_schemas import (
    ImputationAttempt, SearchResult, ExtractedDataPoint, ValidationResult,
    ExtractionMethod, SourceType, ImputationResult, SearchSummary,
    QualityMetrics
)
from ..config.search_patterns import FinancialDataPatterns, SearchQueryGenerator
from ..config.source_rankings import SourceCredibilityRanker
from .data_analysis import DataGapAnalyzer

logger = logging.getLogger(__name__)


class WebDataImputationTool(BaseTool):
    """
    Intelligently imputes missing financial data using web search.
    Searches SEC filings, financial databases, and analyst reports.
    """
    
    name: str = "impute_financial_data"
    description: str = """
    Intelligently imputes missing financial data using web search.
    Searches SEC filings, financial databases, and analyst reports for missing 
    financial metrics required by investment analysis strategies.
    
    Input: ticker symbol, list of missing fields, strategy context
    Output: Imputed values with confidence scores, sources, and validation results
    """
    args_schema: type = ImputationInput
    tavily_tool: Optional[Any] = Field(default=None, exclude=True)
    data_patterns: Optional[Any] = Field(default=None, exclude=True)
    query_generator: Optional[Any] = Field(default=None, exclude=True)
    credibility_ranker: Optional[Any] = Field(default=None, exclude=True)
    
    def __init__(self, tavily_tool=None, **kwargs):
        super().__init__(**kwargs)
        self.tavily_tool = tavily_tool
        self.data_patterns = FinancialDataPatterns()
        self.query_generator = SearchQueryGenerator()
        self.credibility_ranker = SourceCredibilityRanker()
    
    async def _arun(self, ticker: str, missing_fields: List[str], 
                   strategy_context: Optional[str] = None,
                   max_search_results: Optional[int] = 10) -> Dict[str, Any]:
        """Execute the web data imputation process."""
        start_time = time.time()
        session_id = str(uuid.uuid4())
        
        logger.info(f"Starting imputation session {session_id} for {ticker}")
        logger.info(f"Missing fields: {missing_fields}")
        logger.info(f"Strategy context: {strategy_context}")
        
        result = ImputationOutput(
            ticker=ticker,
            requested_fields=missing_fields,
            strategy_context=strategy_context,
            imputation_results={},
            search_summary={},
            data_quality_assessment=QualityMetrics(
                completeness=0.0,
                accuracy=0.0,
                reliability=0.0,
                timeliness=0.8,
                consistency=0.0,
                overall_quality=0.0
            ),
            overall_success_rate=0.0
        )
        
        successful_imputations = 0
        
        # Process each missing field
        for field in missing_fields:
            try:
                logger.info(f"Processing field: {field}")
                
                # Generate search queries for this field
                queries = self.query_generator.generate_queries(
                    ticker, field, strategy_context or "general"
                )[:max_search_results]  # Limit queries
                
                # Execute imputation attempt
                attempt = await self._attempt_field_imputation(
                    ticker, field, queries, strategy_context
                )
                
                # Convert attempt to result format
                imputation_result = ImputationResult(
                    field_name=field,
                    imputed_value=attempt.final_value,
                    confidence=attempt.confidence,
                    sources=[dp.source_url for dp in attempt.extracted_data_points],
                    alternative_values=[dp.normalized_value for dp in attempt.extracted_data_points[1:5]],
                    validation_notes=self._generate_validation_notes(attempt),
                    extraction_method=self._get_primary_extraction_method(attempt)
                )
                
                search_summary = SearchSummary(
                    field_name=field,
                    queries_executed=len(attempt.search_queries),
                    sources_found=len(attempt.search_results),
                    extraction_success=attempt.success,
                    search_duration_ms=attempt.processing_time_ms,
                    errors=attempt.failure_reasons
                )
                
                result.imputation_results[field] = imputation_result
                result.search_summary[field] = search_summary
                
                if attempt.success:
                    successful_imputations += 1
                    logger.info(f"Successfully imputed {field}: {attempt.final_value}")
                else:
                    logger.warning(f"Failed to impute {field}: {attempt.failure_reasons}")
                    
            except Exception as e:
                logger.error(f"Error processing field {field}: {e}")
                result.imputation_results[field] = ImputationResult(
                    field_name=field,
                    confidence=0.0,
                    validation_notes=f"Processing error: {str(e)}"
                )
                result.search_summary[field] = SearchSummary(
                    field_name=field,
                    queries_executed=0,
                    sources_found=0,
                    extraction_success=False,
                    errors=[str(e)]
                )
        
        # Calculate overall metrics
        result.overall_success_rate = (successful_imputations / len(missing_fields)) * 100 if missing_fields else 0
        result.execution_time_ms = int((time.time() - start_time) * 1000)
        
        # Assess overall data quality
        result.data_quality_assessment = self._assess_overall_quality(result.imputation_results)
        
        logger.info(f"Imputation session {session_id} completed. Success rate: {result.overall_success_rate:.1f}%")
        
        return result.model_dump()
    
    def _run(self, *args, **kwargs):
        """Synchronous wrapper for the async implementation."""
        return asyncio.run(self._arun(*args, **kwargs))
    
    async def _attempt_field_imputation(self, ticker: str, field: str, 
                                      queries: List[str], strategy_context: Optional[str]) -> ImputationAttempt:
        """Attempt to impute a single field using web search."""
        start_time = time.time()
        
        attempt = ImputationAttempt(
            field_name=field,
            ticker=ticker,
            search_queries=queries,
            search_results=[],
            extracted_data_points=[],
            confidence=0.0,
            success=False
        )
        
        # Execute searches
        for query in queries:
            try:
                logger.debug(f"Executing search query: {query}")
                
                if self.tavily_tool is None:
                    logger.warning("Tavily tool not available, skipping web search")
                    attempt.failure_reasons.append("Web search tool not available")
                    continue
                
                # Use Tavily to search
                search_response = await self.tavily_tool.ainvoke({"query": query})
                
                # Process search results
                if isinstance(search_response, str):
                    # If response is a string, parse it as best we can
                    search_result = SearchResult(
                        url="tavily_search",
                        title=f"Search for: {query}",
                        content=search_response,
                        source_type=SourceType.FINANCIAL_WEBSITE,
                        relevance_score=0.7
                    )
                    attempt.search_results.append(search_result)
                    
                    # Extract data from the content
                    extracted_points = await self._extract_data_from_content(
                        search_response, field, "tavily_search"
                    )
                    attempt.extracted_data_points.extend(extracted_points)
                    
                elif isinstance(search_response, dict):
                    # Handle structured response
                    results = search_response.get('results', [])
                    for result_item in results[:3]:  # Limit to top 3 results
                        content = result_item.get('content', result_item.get('snippet', ''))
                        url = result_item.get('url', 'unknown')
                        title = result_item.get('title', 'Unknown')
                        
                        search_result = SearchResult(
                            url=url,
                            title=title,
                            content=content,
                            source_type=self.credibility_ranker.get_source_type_from_url(url),
                            credibility_score=self.credibility_ranker.score_source_credibility(url, content, field),
                            relevance_score=0.8
                        )
                        attempt.search_results.append(search_result)
                        
                        # Extract data from this result
                        extracted_points = await self._extract_data_from_content(
                            content, field, url
                        )
                        attempt.extracted_data_points.extend(extracted_points)
                
            except Exception as e:
                logger.error(f"Error executing search query '{query}': {e}")
                attempt.failure_reasons.append(f"Search error for '{query}': {str(e)}")
        
        # Validate and select best value
        if attempt.extracted_data_points:
            attempt = await self._validate_and_select_best_value(attempt)
        else:
            attempt.failure_reasons.append("No data points extracted from search results")
        
        attempt.processing_time_ms = int((time.time() - start_time) * 1000)
        
        return attempt
    
    async def _extract_data_from_content(self, content: str, field: str, source_url: str) -> List[ExtractedDataPoint]:
        """Extract financial data points from content."""
        extracted_points = []
        
        try:
            # Use pattern matching to find values
            matches = self.data_patterns.extract_metric(content, field)
            
            for normalized_value, raw_value, confidence in matches:
                data_point = ExtractedDataPoint(
                    field_name=field,
                    raw_value=raw_value,
                    normalized_value=normalized_value,
                    extraction_method=ExtractionMethod.REGEX_PATTERN,
                    source_url=source_url,
                    source_context=self._extract_context(content, raw_value),
                    extraction_confidence=confidence / 100.0  # Convert to 0-1 scale
                )
                
                extracted_points.append(data_point)
                
        except Exception as e:
            logger.error(f"Error extracting data from content: {e}")
        
        return extracted_points
    
    def _extract_context(self, content: str, raw_value: str) -> str:
        """Extract surrounding context for a value."""
        try:
            pos = content.find(str(raw_value))
            if pos == -1:
                return content[:100]  # Return first 100 chars if value not found
            
            start = max(0, pos - 50)
            end = min(len(content), pos + len(str(raw_value)) + 50)
            return content[start:end].strip()
        except:
            return content[:100]
    
    async def _validate_and_select_best_value(self, attempt: ImputationAttempt) -> ImputationAttempt:
        """Validate extracted data points and select the best value."""
        if not attempt.extracted_data_points:
            return attempt
        
        # Score each data point
        scored_points = []
        for point in attempt.extracted_data_points:
            # Calculate overall score based on multiple factors
            credibility_score = self.credibility_ranker.score_source_credibility(
                point.source_url, point.source_context, point.field_name
            )
            
            # Combine scores
            overall_score = (
                point.extraction_confidence * 0.4 +
                credibility_score * 0.4 +
                0.2  # Base score for having any value
            )
            
            scored_points.append((point, overall_score))
        
        # Sort by score
        scored_points.sort(key=lambda x: x[1], reverse=True)
        
        if scored_points:
            best_point, best_score = scored_points[0]
            attempt.final_value = best_point.normalized_value
            attempt.confidence = min(1.0, best_score)
            attempt.success = best_score > 0.3  # Minimum confidence threshold
            
            # Validate the best value
            validation_result = await self._validate_data_point(best_point, attempt.ticker)
            best_point.validation_result = validation_result
            
            # Adjust confidence based on validation
            if validation_result and validation_result.is_valid:
                attempt.confidence = min(1.0, attempt.confidence * 1.1)
            else:
                attempt.confidence = max(0.0, attempt.confidence * 0.8)
        
        return attempt
    
    async def _validate_data_point(self, data_point: ExtractedDataPoint, ticker: str) -> Optional[ValidationResult]:
        """Validate a single data point."""
        try:
            validation = ValidationResult(
                is_valid=True,
                validation_score=0.5,  # Default score
                validation_methods=['pattern_match']
            )
            
            # Basic validation checks
            if data_point.normalized_value is not None:
                # Check for reasonable ranges
                value = float(data_point.normalized_value)
                
                # Field-specific validation
                if data_point.field_name == 'roic' and (value < -1 or value > 2):
                    validation.is_valid = False
                    validation.validation_notes = "ROIC value outside reasonable range"
                elif data_point.field_name in ['eps_growth', 'sales_growth'] and (value < -1 or value > 5):
                    validation.is_valid = False
                    validation.validation_notes = "Growth rate outside reasonable range"
                elif data_point.field_name == 'pe_ratio' and (value < 0 or value > 1000):
                    validation.is_valid = False
                    validation.validation_notes = "P/E ratio outside reasonable range"
                
                if validation.is_valid:
                    validation.validation_score = 0.8
            else:
                validation.is_valid = False
                validation.validation_notes = "No numeric value extracted"
            
            return validation
            
        except Exception as e:
            logger.error(f"Error validating data point: {e}")
            return ValidationResult(
                is_valid=False,
                validation_score=0.0,
                validation_notes=f"Validation error: {str(e)}"
            )
    
    def _generate_validation_notes(self, attempt: ImputationAttempt) -> Optional[str]:
        """Generate validation notes for the imputation attempt."""
        notes = []
        
        if attempt.success:
            notes.append(f"Successfully extracted from {len(attempt.search_results)} search results")
            if attempt.confidence > 0.8:
                notes.append("High confidence extraction")
            elif attempt.confidence > 0.5:
                notes.append("Medium confidence extraction")
            else:
                notes.append("Low confidence extraction - use with caution")
        else:
            notes.append("Failed to extract reliable value")
            if attempt.failure_reasons:
                notes.extend(attempt.failure_reasons)
        
        return "; ".join(notes) if notes else None
    
    def _get_primary_extraction_method(self, attempt: ImputationAttempt) -> Optional[str]:
        """Get the primary extraction method used."""
        if attempt.extracted_data_points:
            return attempt.extracted_data_points[0].extraction_method
        return None
    
    def _assess_overall_quality(self, results: Dict[str, ImputationResult]) -> QualityMetrics:
        """Assess overall quality of imputation results."""
        if not results:
            return QualityMetrics(
                completeness=0.0,
                accuracy=0.0,
                reliability=0.0,
                timeliness=0.8,  # Web data is typically recent
                consistency=0.0,
                overall_quality=0.0
            )
        
        # Calculate metrics
        successful_fields = [r for r in results.values() if r.imputed_value is not None]
        completeness = len(successful_fields) / len(results) if results else 0.0
        
        if successful_fields:
            avg_confidence = sum(r.confidence for r in successful_fields) / len(successful_fields)
            accuracy = avg_confidence
            reliability = avg_confidence * 0.9  # Slightly lower than confidence
        else:
            accuracy = 0.0
            reliability = 0.0
        
        # Consistency based on number of sources
        has_multiple_sources = any(len(r.sources) > 1 for r in successful_fields)
        consistency = 0.8 if has_multiple_sources else 0.6
        
        # Overall quality
        overall_quality = (completeness * 0.3 + accuracy * 0.3 + reliability * 0.2 + 
                          consistency * 0.1 + 0.8 * 0.1)  # timeliness weight
        
        quality_notes = []
        if completeness < 0.5:
            quality_notes.append("Low completion rate - many fields could not be imputed")
        if accuracy < 0.6:
            quality_notes.append("Low confidence in extracted values")
        if not has_multiple_sources:
            quality_notes.append("Limited cross-validation due to single sources")
        
        return QualityMetrics(
            completeness=completeness,
            accuracy=accuracy,
            reliability=reliability,
            timeliness=0.8,  # Web data is generally recent
            consistency=consistency,
            overall_quality=overall_quality,
            quality_notes=quality_notes
        )