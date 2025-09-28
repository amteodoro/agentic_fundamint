"""
Source credibility ranking and validation for financial data sources.
"""

import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SourceCredibilityRanker:
    """Ranks the credibility of web sources for financial data."""
    
    # Source authority rankings (higher = more credible)
    DOMAIN_RANKINGS = {
        # SEC and Government Sources
        'sec.gov': 100,
        'edgar.sec.gov': 100,
        'treasury.gov': 95,
        'federalreserve.gov': 95,
        
        # Major Financial Data Providers
        'bloomberg.com': 90,
        'reuters.com': 88,
        'wsj.com': 87,
        'ft.com': 86,
        'marketwatch.com': 85,
        
        # Established Financial Websites
        'morningstar.com': 85,
        'finviz.com': 83,
        'finance.yahoo.com': 82,
        'yahoo.com': 80,  # General Yahoo
        'google.com/finance': 80,
        'investing.com': 78,
        
        # Company Sources
        'investor.': 85,  # Partial match for investor relations sites
        '.com/investor': 85,
        '.com/investors': 85,
        
        # Research and Analysis
        'seekingalpha.com': 75,
        'fool.com': 70,
        'zacks.com': 72,
        'gurufocus.com': 68,
        
        # Financial News
        'cnbc.com': 75,
        'cnn.com': 70,
        'foxbusiness.com': 68,
        
        # General/Lower Quality
        'reddit.com': 30,
        'quora.com': 25,
        'facebook.com': 20,
        'twitter.com': 25,
        'wikipedia.org': 60,  # Good for general info, not current data
    }
    
    # Content quality indicators
    POSITIVE_INDICATORS = [
        'annual report', '10-k', '10-q', '8-k', 'sec filing',
        'earnings report', 'financial statement', 'investor relations',
        'quarterly report', 'press release', 'earnings call',
        'analyst report', 'research note', 'financial analysis'
    ]
    
    NEGATIVE_INDICATORS = [
        'opinion', 'blog', 'forum', 'comment', 'social media',
        'unverified', 'rumor', 'speculation', 'prediction',
        'advertisement', 'promotional', 'sponsored'
    ]
    
    def score_source_credibility(self, url: str, content: str, data_point: str) -> float:
        """
        Score the credibility of a web source for financial data.
        
        Args:
            url: Source URL
            content: Text content from the source
            data_point: The financial data point being extracted
            
        Returns:
            Credibility score from 0.0 to 1.0
        """
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            
            # Start with domain-based credibility
            domain_score = self._get_domain_score(domain)
            
            # Adjust based on content quality
            content_score = self._analyze_content_quality(content, data_point)
            
            # Check for recency indicators
            recency_score = self._assess_data_recency(content)
            
            # Check for data presentation quality
            presentation_score = self._assess_presentation_quality(content)
            
            # Weighted final score
            final_score = (
                domain_score * 0.4 +
                content_score * 0.3 +
                recency_score * 0.15 +
                presentation_score * 0.15
            )
            
            # Normalize to 0-1 range
            return min(1.0, max(0.0, final_score / 100.0))
            
        except Exception as e:
            logger.error(f"Error scoring source credibility for {url}: {e}")
            return 0.5  # Default middle score on error
    
    def _get_domain_score(self, domain: str) -> float:
        """Get credibility score based on domain."""
        # Direct match
        if domain in self.DOMAIN_RANKINGS:
            return float(self.DOMAIN_RANKINGS[domain])
        
        # Partial matches
        for pattern, score in self.DOMAIN_RANKINGS.items():
            if pattern in domain:
                return float(score)
        
        # Check for common patterns
        if domain.endswith('.edu'):
            return 75.0  # Academic institutions
        elif domain.endswith('.gov'):
            return 90.0  # Government sources
        elif 'investor' in domain:
            return 80.0  # Likely investor relations
        elif domain.count('.') == 1 and len(domain.split('.')[0]) > 3:
            return 50.0  # Simple company domain
        else:
            return 40.0  # Unknown domain
    
    def _analyze_content_quality(self, content: str, data_point: str) -> float:
        """Analyze content quality for financial data."""
        content_lower = content.lower()
        score = 50.0  # Base score
        
        # Check for positive indicators
        positive_count = sum(1 for indicator in self.POSITIVE_INDICATORS 
                           if indicator in content_lower)
        score += min(30, positive_count * 5)
        
        # Check for negative indicators
        negative_count = sum(1 for indicator in self.NEGATIVE_INDICATORS 
                           if indicator in content_lower)
        score -= min(25, negative_count * 5)
        
        # Check for structured data indicators
        if self._has_structured_data(content):
            score += 15
        
        # Check for multiple data points (suggests comprehensive source)
        if self._has_multiple_metrics(content):
            score += 10
        
        return max(0, min(100, score))
    
    def _assess_data_recency(self, content: str) -> float:
        """Assess how recent the data appears to be."""
        score = 50.0  # Base score
        content_lower = content.lower()
        
        # Look for recent year indicators
        import datetime
        current_year = datetime.datetime.now().year
        
        # Check for current and recent years
        for year in range(current_year - 2, current_year + 1):
            if str(year) in content:
                score += 20
                break
        
        # Check for recency keywords
        recency_keywords = [
            'latest', 'recent', 'current', 'updated', 'q1 2024', 'q2 2024', 
            'q3 2024', 'q4 2024', 'fiscal 2024', 'ttm', 'trailing twelve'
        ]
        
        for keyword in recency_keywords:
            if keyword in content_lower:
                score += 10
                break
        
        return max(0, min(100, score))
    
    def _assess_presentation_quality(self, content: str) -> float:
        """Assess the quality of data presentation."""
        score = 50.0  # Base score
        
        # Look for structured formats
        if self._has_tables(content):
            score += 20
        
        if self._has_clear_labels(content):
            score += 15
        
        if self._has_consistent_formatting(content):
            score += 10
        
        # Penalize very short content
        if len(content) < 100:
            score -= 15
        
        return max(0, min(100, score))
    
    def _has_structured_data(self, content: str) -> bool:
        """Check if content has structured financial data."""
        patterns = [
            r'\$\d+(?:,\d{3})*(?:\.\d+)?[BMK]?',  # Currency with multipliers
            r'\d+\.\d+%',  # Percentages
            r':\s*\$?\d+(?:,\d{3})*',  # Labeled values
            r'\|\s*\d+',  # Table-like formatting
        ]
        
        for pattern in patterns:
            if re.search(pattern, content):
                return True
        return False
    
    def _has_multiple_metrics(self, content: str) -> bool:
        """Check if content contains multiple financial metrics."""
        metrics = [
            'roic', 'roe', 'eps', 'revenue', 'debt', 'margin',
            'cash flow', 'ebitda', 'p/e', 'p/s'
        ]
        
        found_metrics = sum(1 for metric in metrics 
                           if metric in content.lower())
        return found_metrics >= 3
    
    def _has_tables(self, content: str) -> bool:
        """Check if content appears to contain tabular data."""
        table_indicators = [
            '|', '\t', '    ', 'TABLE', 'th>', 'td>',
            'Year', 'Quarter', 'Metric', 'Value'
        ]
        
        return any(indicator in content for indicator in table_indicators)
    
    def _has_clear_labels(self, content: str) -> bool:
        """Check if financial data has clear labels."""
        label_patterns = [
            r'[A-Za-z\s]+:\s*\$?\d+',
            r'[A-Za-z\s]+\s+\$?\d+(?:,\d{3})*',
            r'\w+\s+Ratio:\s*\d+',
        ]
        
        return any(re.search(pattern, content) for pattern in label_patterns)
    
    def _has_consistent_formatting(self, content: str) -> bool:
        """Check for consistent number formatting."""
        # Look for consistent use of commas, decimals, currency symbols
        comma_count = content.count(',')
        dollar_count = content.count('$')
        percent_count = content.count('%')
        
        # If we have multiple numbers, check for consistency
        numbers = re.findall(r'\d+(?:,\d{3})*(?:\.\d+)?', content)
        if len(numbers) > 3:
            # Check if most numbers follow similar formatting
            comma_numbers = [n for n in numbers if ',' in n]
            return len(comma_numbers) >= len(numbers) * 0.7
        
        return True  # Default to true for small amounts of data
    
    def get_source_type_from_url(self, url: str) -> str:
        """Determine the type of source from URL."""
        domain = urlparse(url).netloc.lower()
        
        if 'sec.gov' in domain or 'edgar' in domain:
            return 'sec_filing'
        elif any(x in domain for x in ['bloomberg', 'reuters', 'wsj', 'ft']):
            return 'financial_news'
        elif any(x in domain for x in ['morningstar', 'finviz', 'yahoo']):
            return 'financial_website'
        elif 'investor' in domain or 'ir.' in domain:
            return 'company_presentation'
        elif any(x in domain for x in ['seekingalpha', 'fool', 'zacks']):
            return 'analyst_report'
        elif any(x in domain for x in ['reddit', 'quora', 'facebook']):
            return 'forum_discussion'
        else:
            return 'financial_website'  # Default