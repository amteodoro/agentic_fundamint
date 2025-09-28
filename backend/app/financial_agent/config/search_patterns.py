"""
Financial data extraction patterns and search query generation.
"""

import re
from typing import Dict, List, Union, Optional, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class FinancialDataPatterns:
    """Pattern matching for extracting financial data from web content."""
    
    # Regex patterns for different financial metrics
    PATTERNS = {
        'roic': [
            r'ROIC[:\s]+(\d+\.?\d*)%?',
            r'Return on Invested Capital[:\s]+(\d+\.?\d*)%?',
            r'return on invested capital[:\s]+(\d+\.?\d*)%?',
            r'ROIC:\s*(\d+\.?\d*)%',
            r'ROIC\s+of\s+(\d+\.?\d*)%',
            r'Return\s+on\s+Invested\s+Capital[:\s]+(\d+\.?\d*)%?',
        ],
        'ebit': [
            r'EBIT[:\s]+\$?(\d+(?:,\d{3})*(?:\.\d+)?)[BMK]?',
            r'Operating Income[:\s]+\$?(\d+(?:,\d{3})*(?:\.\d+)?)[BMK]?',
            r'Earnings before interest and taxes[:\s]+\$?(\d+(?:,\d{3})*(?:\.\d+)?)[BMK]?',
            r'EBIT:\s*\$?(\d+(?:,\d{3})*(?:\.\d+)?)[BMK]?',
            r'Operating\s+Income:\s*\$?(\d+(?:,\d{3})*(?:\.\d+)?)[BMK]?',
        ],
        'debt': [
            r'Total Debt[:\s]+\$?(\d+(?:,\d{3})*(?:\.\d+)?)[BMK]?',
            r'Long[- ]term Debt[:\s]+\$?(\d+(?:,\d{3})*(?:\.\d+)?)[BMK]?',
            r'Total\s+Debt:\s*\$?(\d+(?:,\d{3})*(?:\.\d+)?)[BMK]?',
            r'Long[- ]Term\s+Debt:\s*\$?(\d+(?:,\d{3})*(?:\.\d+)?)[BMK]?',
            r'Net\s+Debt[:\s]+\$?(\d+(?:,\d{3})*(?:\.\d+)?)[BMK]?',
        ],
        'eps_growth': [
            r'EPS Growth[:\s]+(\d+\.?\d*)%?',
            r'Earnings per share growth[:\s]+(\d+\.?\d*)%?',
            r'EPS\s+CAGR[:\s]+(\d+\.?\d*)%?',
            r'EPS\s+growth\s+rate[:\s]+(\d+\.?\d*)%?',
            r'Diluted\s+EPS\s+growth[:\s]+(\d+\.?\d*)%?',
        ],
        'sales_growth': [
            r'Revenue Growth[:\s]+(\d+\.?\d*)%?',
            r'Sales Growth[:\s]+(\d+\.?\d*)%?',
            r'Revenue\s+CAGR[:\s]+(\d+\.?\d*)%?',
            r'Top[- ]line\s+growth[:\s]+(\d+\.?\d*)%?',
            r'Sales\s+growth\s+rate[:\s]+(\d+\.?\d*)%?',
        ],
        'net_margin': [
            r'Net Margin[:\s]+(\d+\.?\d*)%?',
            r'Net Profit Margin[:\s]+(\d+\.?\d*)%?',
            r'Net\s+margin:\s*(\d+\.?\d*)%?',
            r'Profit\s+margin[:\s]+(\d+\.?\d*)%?',
        ],
        'pe_ratio': [
            r'P/E Ratio[:\s]+(\d+\.?\d*)',
            r'PE[:\s]+(\d+\.?\d*)',
            r'Price[- ]to[- ]Earnings[:\s]+(\d+\.?\d*)',
            r'Trailing\s+P/E[:\s]+(\d+\.?\d*)',
            r'Forward\s+P/E[:\s]+(\d+\.?\d*)',
        ],
        'psr_ratio': [
            r'P/S Ratio[:\s]+(\d+\.?\d*)',
            r'PSR[:\s]+(\d+\.?\d*)',
            r'Price[- ]to[- ]Sales[:\s]+(\d+\.?\d*)',
            r'Price/Sales[:\s]+(\d+\.?\d*)',
        ],
        'roe': [
            r'ROE[:\s]+(\d+\.?\d*)%?',
            r'Return on Equity[:\s]+(\d+\.?\d*)%?',
            r'ROE:\s*(\d+\.?\d*)%?',
            r'Return\s+on\s+Equity:\s*(\d+\.?\d*)%?',
        ],
        'insider_ownership': [
            r'Insider Ownership[:\s]+(\d+\.?\d*)%?',
            r'Insiders\s+Own[:\s]+(\d+\.?\d*)%?',
            r'Management\s+Ownership[:\s]+(\d+\.?\d*)%?',
            r'Insider\s+Owned:\s*(\d+\.?\d*)%?',
        ],
        'dividend_yield': [
            r'Dividend Yield[:\s]+(\d+\.?\d*)%?',
            r'Dividend\s+Yield:\s*(\d+\.?\d*)%?',
            r'Yield[:\s]+(\d+\.?\d*)%?',
            r'Annual\s+Yield[:\s]+(\d+\.?\d*)%?',
        ],
        'market_cap': [
            r'Market Cap[:\s]+\$?(\d+(?:,\d{3})*(?:\.\d+)?)[BMK]?',
            r'Market\s+Capitalization[:\s]+\$?(\d+(?:,\d{3})*(?:\.\d+)?)[BMK]?',
            r'Mkt\s+Cap[:\s]+\$?(\d+(?:,\d{3})*(?:\.\d+)?)[BMK]?',
        ],
    }
    
    # Multipliers for financial shorthand notation
    MULTIPLIERS = {
        'K': 1000,
        'M': 1000000,
        'B': 1000000000,
        'T': 1000000000000,
    }
    
    def extract_metric(self, content: str, metric_type: str) -> List[Tuple[float, str, int]]:
        """
        Extract financial metrics from text content using regex patterns.
        
        Returns:
            List of tuples: (normalized_value, raw_match, confidence_score)
        """
        patterns = self.PATTERNS.get(metric_type, [])
        matches = []
        
        if not patterns:
            logger.warning(f"No patterns defined for metric type: {metric_type}")
            return matches
        
        for pattern in patterns:
            try:
                found = re.findall(pattern, content, re.IGNORECASE)
                for match in found:
                    normalized_value = self._normalize_financial_value(match)
                    if normalized_value is not None:
                        # Calculate confidence based on pattern specificity and context
                        confidence = self._calculate_extraction_confidence(pattern, match, content)
                        matches.append((normalized_value, match, confidence))
            except re.error as e:
                logger.error(f"Regex error with pattern '{pattern}': {e}")
        
        # Sort by confidence and remove duplicates
        matches = sorted(set(matches), key=lambda x: x[2], reverse=True)
        return matches
    
    def _normalize_financial_value(self, value_str: Union[str, float]) -> Optional[float]:
        """Normalize financial value string to float."""
        if isinstance(value_str, (int, float)):
            return float(value_str)
        
        if not isinstance(value_str, str):
            return None
        
        # Clean the string
        value_str = value_str.replace(',', '').strip()
        
        if not value_str or value_str.lower() == 'n/a' or value_str == '-':
            return None
        
        # Handle percentage notation
        is_percentage = value_str.endswith('%')
        if is_percentage:
            value_str = value_str[:-1]
        
        # Handle multiplier notation
        multiplier = 1.0
        if value_str and value_str[-1].upper() in self.MULTIPLIERS:
            multiplier = self.MULTIPLIERS[value_str[-1].upper()]
            value_str = value_str[:-1]
        
        try:
            numeric_val = float(value_str)
            
            # Apply multiplier
            numeric_val *= multiplier
            
            # Convert percentage to decimal
            if is_percentage:
                numeric_val /= 100.0
            
            return numeric_val
            
        except ValueError:
            logger.debug(f"Could not convert to float: {value_str}")
            return None
    
    def _calculate_extraction_confidence(self, pattern: str, match: str, content: str) -> int:
        """Calculate confidence score for extracted value based on context."""
        confidence = 50  # Base confidence
        
        # Higher confidence for more specific patterns
        if 'ROIC:' in pattern or 'ROE:' in pattern:
            confidence += 20
        
        # Check for surrounding context that indicates financial data
        context_window = 100
        match_pos = content.find(match)
        if match_pos != -1:
            start = max(0, match_pos - context_window)
            end = min(len(content), match_pos + len(match) + context_window)
            context = content[start:end].lower()
            
            # Positive context indicators
            positive_indicators = [
                'financial', 'earnings', 'annual report', 'sec filing',
                'income statement', 'balance sheet', 'cash flow',
                'investor relations', 'quarterly', 'fiscal year'
            ]
            
            for indicator in positive_indicators:
                if indicator in context:
                    confidence += 10
                    break
            
            # Negative context indicators
            negative_indicators = [
                'target', 'estimate', 'projected', 'expected',
                'forecast', 'guidance', 'outlook', 'consensus'
            ]
            
            for indicator in negative_indicators:
                if indicator in context:
                    confidence -= 15
                    break
        
        return min(100, max(10, confidence))  # Clamp between 10-100


class SearchQueryGenerator:
    """Generate targeted search queries for missing financial data."""
    
    QUERY_TEMPLATES = {
        'phil_town': {
            'roic': [
                "{ticker} return on invested capital ROIC 2024",
                "{ticker} 10-K SEC filing ROIC operating income",
                "{ticker} NOPAT invested capital calculation",
                "site:sec.gov {ticker} annual report ROIC",
                "{ticker} financial metrics ROIC analysis"
            ],
            'eps_growth': [
                "{ticker} earnings per share growth rate historical",
                "{ticker} EPS CAGR 5 year 10 year analysis",
                "site:finance.yahoo.com {ticker} earnings growth",
                "{ticker} analyst EPS growth estimates",
                "{ticker} diluted EPS historical trend"
            ],
            'sales_growth': [
                "{ticker} revenue growth CAGR historical",
                "{ticker} sales growth rate annual quarterly",
                "{ticker} top line growth analysis",
                "site:morningstar.com {ticker} revenue trend"
            ],
            'debt_payoff': [
                "{ticker} long term debt free cash flow ratio",
                "{ticker} balance sheet debt cash flow statement",
                "{ticker} debt payoff capability years FCF",
                "site:morningstar.com {ticker} debt analysis"
            ],
            'insider_ownership': [
                "{ticker} insider ownership percentage management",
                "{ticker} insider trading ownership stake",
                "site:finviz.com {ticker} insider ownership",
                "{ticker} management ownership shares"
            ],
            'margin_of_safety': [
                "{ticker} intrinsic value sticker price calculation",
                "{ticker} Phil Town margin of safety analysis",
                "{ticker} fair value vs market price",
                "{ticker} discounted cash flow valuation"
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
            ],
            'roe': [
                "{ticker} return on equity ROE trend",
                "{ticker} ROE historical analysis",
                "{ticker} equity returns profitability",
                "site:morningstar.com {ticker} ROE metrics"
            ],
            'debt_to_ebitda': [
                "{ticker} debt to EBITDA ratio",
                "{ticker} net debt EBITDA coverage",
                "{ticker} leverage ratio debt analysis",
                "{ticker} financial leverage metrics"
            ],
            'psr_ratio': [
                "{ticker} price to sales ratio PSR",
                "{ticker} P/S ratio valuation metric",
                "{ticker} sales multiple valuation",
                "site:finviz.com {ticker} PSR ratio"
            ],
            'dividend_yield': [
                "{ticker} dividend yield percentage annual",
                "{ticker} dividend payments yield analysis",
                "{ticker} dividend history yield trend",
                "site:dividend.com {ticker} yield"
            ]
        }
    }
    
    def generate_queries(self, ticker: str, field: str, strategy: str) -> List[str]:
        """Generate contextual search queries based on strategy and field."""
        templates = self.QUERY_TEMPLATES.get(strategy, {}).get(field, [])
        
        if not templates:
            # Generate generic queries if no specific templates exist
            templates = self._generate_generic_queries(field)
        
        queries = [template.format(ticker=ticker.upper()) for template in templates]
        
        # Add some generic fallback queries
        queries.extend([
            f"{ticker.upper()} {field} financial data",
            f"{ticker.upper()} annual report {field}",
            f"{ticker.upper()} 10-K {field} SEC filing"
        ])
        
        return queries
    
    def _generate_generic_queries(self, field: str) -> List[str]:
        """Generate generic search queries for unknown fields."""
        field_clean = field.replace('_', ' ')
        return [
            "{ticker} " + field_clean + " financial metric",
            "{ticker} " + field_clean + " calculation",
            "{ticker} " + field_clean + " annual report",
            "{ticker} " + field_clean + " SEC filing"
        ]
    
    def get_search_priority(self, field: str, strategy: str) -> int:
        """Get search priority for a field within a strategy (1-10, higher is more important)."""
        priority_map = {
            'phil_town': {
                'roic': 10,
                'eps_growth': 9,
                'sales_growth': 8,
                'margin_of_safety': 8,
                'debt_payoff': 7,
                'insider_ownership': 6,
                'fcf_growth': 7,
                'bvps_growth': 6
            },
            'high_growth': {
                'sales_growth': 10,
                'net_margin_trend': 9,
                'roe': 8,
                'roic': 8,
                'debt_to_ebitda': 7,
                'psr_ratio': 6,
                'per_ratio': 6,
                'dividend_yield': 5
            }
        }
        
        return priority_map.get(strategy, {}).get(field, 5)  # Default priority: 5