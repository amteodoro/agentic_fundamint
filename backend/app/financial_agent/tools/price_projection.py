"""
Price Projection Tool - Implements the "Recipe" framework for future stock price calculation.

Based on the 4-variable projection model:
1. Revenue Growth Rate
2. Net Profit Margin
3. Target P/E Ratio
4. Share Count Change

Calculates future stock price and expected CAGR to determine BUY/HOLD/REJECT.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
import yfinance as yf
import logging
import numpy as np

logger = logging.getLogger(__name__)


class PriceProjectionInput(BaseModel):
    ticker: str = Field(description="The ticker symbol of the company to analyze")


class PriceProjectionTool(BaseTool):
    name: str = "price_projection_analysis"
    description: str = "Calculates future stock price based on revenue growth, margins, P/E, and share count projections."

    def _run(self, ticker: str) -> Dict[str, Any]:
        raise NotImplementedError("Use _arun instead")

    async def _arun(self, ticker: str) -> Dict[str, Any]:
        logger.info(f"Starting Price Projection analysis for {ticker}")
        
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Get current price and shares
            current_price = info.get('currentPrice') or info.get('regularMarketPrice')
            current_shares = info.get('sharesOutstanding')
            market_cap = info.get('marketCap')
            
            if not current_price:
                return {"error": "Cannot retrieve current stock price"}
            
            # Get financial data for calculations
            financials = stock.financials
            income_stmt = stock.income_stmt
            
            # Calculate defaults
            defaults = self._calculate_defaults(stock, info, financials, income_stmt)
            historical_context = self._get_historical_context(stock, info, financials)
            historical_averages = self._calculate_historical_averages(stock, info, financials, income_stmt)
            data_quality = self._assess_data_quality(defaults, info)
            
            # Analyze negative values (new methodology)
            negative_analysis = self._analyze_negative_values(stock, info, financials, income_stmt, defaults, historical_averages)
            
            # Get current metrics for display
            current_revenue = self._get_current_revenue(financials, info)
            current_net_income = self._get_current_net_income(income_stmt, info)
            
            return {
                "ticker": ticker,
                "company_name": info.get('longName', ticker),
                "current_price": current_price,
                "current_revenue": current_revenue,
                "current_net_income": current_net_income,
                "current_shares": current_shares,
                "market_cap": market_cap,
                "current_pe": info.get('trailingPE'),
                "current_margin": info.get('profitMargins', 0) * 100 if info.get('profitMargins') else None,
                "defaults": defaults,
                "historical_averages": historical_averages,
                "historical_context": historical_context,
                "data_quality": data_quality,
                "negative_analysis": negative_analysis,
                "hurdle_rate": 15.0  # The 15% minimum threshold from the strategy
            }
            
        except Exception as e:
            logger.error(f"Error during Price Projection analysis: {e}", exc_info=True)
            return {"error": str(e)}

    def _calculate_defaults(self, stock, info: Dict, financials, income_stmt) -> Dict[str, Any]:
        """Calculate default values for all projection parameters."""
        
        # 1. Revenue Growth Rate (historical 5-year CAGR)
        revenue_growth = self._calculate_revenue_growth(financials, info)
        
        # 2. Net Margin (current TTM or calculated)
        net_margin = self._calculate_net_margin(info, income_stmt, financials)
        
        # 3. Target P/E (historical average)
        target_pe = self._calculate_target_pe(info)
        
        # 4. Share Count Change (historical trend)
        share_change = self._calculate_share_change(stock, info)
        
        # 5. Target P/S (Price-to-Sales) - used when margins are negative
        target_ps = self._calculate_target_ps(info)
        
        return {
            "revenue_growth_pct": round(revenue_growth, 2),
            "net_margin_pct": round(net_margin, 2),
            "target_pe": round(target_pe, 2),
            "target_ps": round(target_ps, 2),
            "share_change_pct": round(share_change, 2),
            "projection_years": 10
        }

    def _calculate_revenue_growth(self, financials, info: Dict) -> float:
        """Calculate historical revenue CAGR."""
        try:
            if financials is not None and not financials.empty:
                # Try to get Total Revenue row
                if 'Total Revenue' in financials.index:
                    revenues = financials.loc['Total Revenue'].dropna().values
                    if len(revenues) >= 2:
                        # Calculate CAGR
                        latest = revenues[0]
                        oldest = revenues[-1]
                        years = len(revenues) - 1
                        if oldest > 0 and latest > 0:
                            cagr = ((latest / oldest) ** (1 / years) - 1) * 100
                            return max(min(cagr, 50), -20)  # Cap at reasonable bounds
            
            # Fallback to info
            revenue_growth = info.get('revenueGrowth')
            if revenue_growth:
                return revenue_growth * 100
            
            # Default to conservative estimate
            return 5.0
        except Exception as e:
            logger.warning(f"Error calculating revenue growth: {e}")
            return 5.0

    def _calculate_net_margin(self, info: Dict, income_stmt, financials) -> float:
        """Calculate net profit margin."""
        try:
            # First try direct from info
            if info.get('profitMargins'):
                return info['profitMargins'] * 100
            
            # Try calculating from income statement
            if income_stmt is not None and not income_stmt.empty:
                if 'Net Income' in income_stmt.index and financials is not None and 'Total Revenue' in financials.index:
                    net_income = income_stmt.loc['Net Income'].dropna().values
                    revenue = financials.loc['Total Revenue'].dropna().values
                    if len(net_income) > 0 and len(revenue) > 0:
                        margin = (net_income[0] / revenue[0]) * 100
                        return max(min(margin, 50), -20)
            
            # Default to conservative estimate
            return 10.0
        except Exception as e:
            logger.warning(f"Error calculating net margin: {e}")
            return 10.0

    def _calculate_target_pe(self, info: Dict) -> float:
        """Calculate target P/E based on historical data."""
        try:
            # Use trailing P/E as baseline
            trailing_pe = info.get('trailingPE')
            forward_pe = info.get('forwardPE')
            
            if trailing_pe and forward_pe:
                # Average of trailing and forward
                return (trailing_pe + forward_pe) / 2
            elif trailing_pe:
                return trailing_pe
            elif forward_pe:
                return forward_pe
            
            # Default to market average
            return 15.0
        except Exception as e:
            logger.warning(f"Error calculating target P/E: {e}")
            return 15.0

    def _calculate_target_ps(self, info: Dict) -> float:
        """Calculate target Price-to-Sales ratio (used when margins are negative)."""
        try:
            # Try to get current P/S from yfinance
            current_ps = info.get('priceToSalesTrailing12Months')
            
            if current_ps and current_ps > 0:
                return current_ps
            
            # Calculate P/S from market cap and revenue if available
            market_cap = info.get('marketCap')
            total_revenue = info.get('totalRevenue')
            
            if market_cap and total_revenue and total_revenue > 0:
                return market_cap / total_revenue
            
            # Default P/S based on sector averages (conservative default)
            sector = info.get('sector', '').lower()
            sector_ps_defaults = {
                'technology': 5.0,
                'healthcare': 3.0,
                'consumer cyclical': 1.5,
                'consumer defensive': 1.2,
                'financial services': 2.0,
                'industrials': 1.5,
                'energy': 1.0,
                'utilities': 2.0,
                'real estate': 5.0,
                'communication services': 3.0,
                'basic materials': 1.5,
            }
            
            return sector_ps_defaults.get(sector, 2.0)  # Default to 2x P/S
        except Exception as e:
            logger.warning(f"Error calculating target P/S: {e}")
            return 2.0

    def _calculate_share_change(self, stock, info: Dict) -> float:
        """Calculate historical share count change rate."""
        try:
            # Try to get historical share data
            shares_outstanding = info.get('sharesOutstanding')
            
            # Get historical data if available from balance sheet
            balance_sheet = stock.balance_sheet
            if balance_sheet is not None and not balance_sheet.empty:
                if 'Ordinary Shares Number' in balance_sheet.index:
                    shares = balance_sheet.loc['Ordinary Shares Number'].dropna().values
                    if len(shares) >= 2:
                        latest = shares[0]
                        oldest = shares[-1]
                        years = len(shares) - 1
                        if oldest > 0:
                            annual_change = ((latest / oldest) ** (1 / years) - 1) * 100
                            return max(min(annual_change, 10), -10)
            
            # Default to 0 (stable share count)
            return 0.0
        except Exception as e:
            logger.warning(f"Error calculating share change: {e}")
            return 0.0

    def _get_current_revenue(self, financials, info: Dict) -> Optional[float]:
        """Get current annual revenue."""
        try:
            if financials is not None and not financials.empty:
                if 'Total Revenue' in financials.index:
                    revenues = financials.loc['Total Revenue'].dropna().values
                    if len(revenues) > 0:
                        return float(revenues[0])
            
            return info.get('totalRevenue')
        except Exception as e:
            logger.warning(f"Error getting current revenue: {e}")
            return None

    def _get_current_net_income(self, income_stmt, info: Dict) -> Optional[float]:
        """Get current annual net income."""
        try:
            if income_stmt is not None and not income_stmt.empty:
                if 'Net Income' in income_stmt.index:
                    net_income = income_stmt.loc['Net Income'].dropna().values
                    if len(net_income) > 0:
                        return float(net_income[0])
            
            return info.get('netIncomeToCommon')
        except Exception as e:
            logger.warning(f"Error getting current net income: {e}")
            return None

    def _get_historical_context(self, stock, info: Dict, financials) -> Dict[str, Any]:
        """Get historical data for context charts."""
        context = {
            "revenue_history": [],
            "margin_history": [],
            "pe_range": {"min": None, "avg": None, "max": None},
            "shares_history": []
        }
        
        try:
            # Revenue history
            if financials is not None and not financials.empty and 'Total Revenue' in financials.index:
                revenues = financials.loc['Total Revenue'].dropna()
                context["revenue_history"] = [
                    {"year": str(date.year), "value": float(val)}
                    for date, val in revenues.items()
                ][::-1]  # Reverse to chronological order
            
            # Margin history
            income_stmt = stock.income_stmt
            if (income_stmt is not None and not income_stmt.empty and 
                financials is not None and 'Net Income' in income_stmt.index and 'Total Revenue' in financials.index):
                net_incomes = income_stmt.loc['Net Income'].dropna()
                revenues = financials.loc['Total Revenue'].dropna()
                margins = []
                for date in net_incomes.index:
                    if date in revenues.index:
                        margin = (net_incomes[date] / revenues[date]) * 100
                        margins.append({"year": str(date.year), "value": round(margin, 2)})
                context["margin_history"] = margins[::-1]
            
            # P/E range estimation
            trailing_pe = info.get('trailingPE')
            if trailing_pe:
                # Estimate range based on typical volatility
                context["pe_range"] = {
                    "min": round(trailing_pe * 0.6, 1),
                    "avg": round(trailing_pe, 1),
                    "max": round(trailing_pe * 1.5, 1)
                }
            
            # Share count history
            balance_sheet = stock.balance_sheet
            if balance_sheet is not None and not balance_sheet.empty and 'Ordinary Shares Number' in balance_sheet.index:
                shares = balance_sheet.loc['Ordinary Shares Number'].dropna()
                context["shares_history"] = [
                    {"year": str(date.year), "value": float(val)}
                    for date, val in shares.items()
                ][::-1]
                
        except Exception as e:
            logger.warning(f"Error getting historical context: {e}")
        
        return context

    def _calculate_historical_averages(self, stock, info: Dict, financials, income_stmt) -> Dict[str, Any]:
        """Calculate historical averages for each metric."""
        averages = {
            "revenue_growth_pct": None,
            "net_margin_pct": None,
            "target_pe": None,
            "share_change_pct": None
        }
        
        try:
            # Revenue Growth - Calculate year-over-year growth rates and average them
            if financials is not None and not financials.empty and 'Total Revenue' in financials.index:
                revenues = financials.loc['Total Revenue'].dropna().values
                if len(revenues) >= 2:
                    yoy_growth_rates = []
                    for i in range(len(revenues) - 1):
                        if revenues[i+1] > 0:
                            growth = ((revenues[i] / revenues[i+1]) - 1) * 100
                            yoy_growth_rates.append(growth)
                    if yoy_growth_rates:
                        averages["revenue_growth_pct"] = round(sum(yoy_growth_rates) / len(yoy_growth_rates), 2)
            
            # Net Margin - Average of historical margins
            if (income_stmt is not None and not income_stmt.empty and 
                financials is not None and 'Net Income' in income_stmt.index and 'Total Revenue' in financials.index):
                net_incomes = income_stmt.loc['Net Income'].dropna()
                revenues = financials.loc['Total Revenue'].dropna()
                margins = []
                for date in net_incomes.index:
                    if date in revenues.index and revenues[date] != 0:
                        margin = (net_incomes[date] / revenues[date]) * 100
                        margins.append(margin)
                if margins:
                    averages["net_margin_pct"] = round(sum(margins) / len(margins), 2)
            
            # P/E - Use trailing P/E as the historical average proxy
            # Note: yfinance doesn't provide historical P/E, so we estimate
            trailing_pe = info.get('trailingPE')
            forward_pe = info.get('forwardPE')
            if trailing_pe and forward_pe:
                averages["target_pe"] = round((trailing_pe + forward_pe) / 2, 2)
            elif trailing_pe:
                averages["target_pe"] = round(trailing_pe, 2)
            elif forward_pe:
                averages["target_pe"] = round(forward_pe, 2)
            
            # Share Count Change - Average annual change
            balance_sheet = stock.balance_sheet
            if balance_sheet is not None and not balance_sheet.empty and 'Ordinary Shares Number' in balance_sheet.index:
                shares = balance_sheet.loc['Ordinary Shares Number'].dropna().values
                if len(shares) >= 2:
                    yoy_changes = []
                    for i in range(len(shares) - 1):
                        if shares[i+1] > 0:
                            change = ((shares[i] / shares[i+1]) - 1) * 100
                            yoy_changes.append(change)
                    if yoy_changes:
                        averages["share_change_pct"] = round(sum(yoy_changes) / len(yoy_changes), 2)
                        
        except Exception as e:
            logger.warning(f"Error calculating historical averages: {e}")
        
        return averages

    def _assess_data_quality(self, defaults: Dict, info: Dict) -> Dict[str, Dict[str, Any]]:
        """Assess the quality/source of each default value."""
        quality = {}
        
        # Revenue growth quality
        if info.get('revenueGrowth') or defaults['revenue_growth_pct'] != 5.0:
            quality['revenue_growth'] = {"source": "calculated", "confidence": 0.90}
        else:
            quality['revenue_growth'] = {"source": "default", "confidence": 0.50}
        
        # Net margin quality
        if info.get('profitMargins'):
            quality['net_margin'] = {"source": "yfinance", "confidence": 0.95}
        elif defaults['net_margin_pct'] != 10.0:
            quality['net_margin'] = {"source": "calculated", "confidence": 0.80}
        else:
            quality['net_margin'] = {"source": "default", "confidence": 0.50}
        
        # P/E quality
        if info.get('trailingPE') or info.get('forwardPE'):
            quality['target_pe'] = {"source": "yfinance", "confidence": 0.90}
        else:
            quality['target_pe'] = {"source": "market_average", "confidence": 0.60}
        
        # Share change quality
        if defaults['share_change_pct'] != 0.0:
            quality['share_change'] = {"source": "calculated", "confidence": 0.85}
        else:
            quality['share_change'] = {"source": "assumed_stable", "confidence": 0.70}
        
        return quality

    def _analyze_negative_values(self, stock, info: Dict, financials, income_stmt, defaults: Dict, historical_averages: Dict) -> Dict[str, Any]:
        """
        Analyze negative revenue growth and margins according to the Recipe methodology.
        
        Returns analysis with:
        - revenue_status: 'positive', 'negative', 'declining'
        - margin_status: 'positive', 'negative'
        - margin_category: 'cyclical', 'turnaround', 'structural', None
        - red_flags: list of warning messages
        - opportunities: list of potential opportunity signals
        - recommendation: overall guidance based on analysis
        """
        analysis = {
            "revenue_status": "positive",
            "revenue_trend": "growing",
            "margin_status": "positive", 
            "margin_category": None,
            "is_cyclical": False,
            "has_operating_leverage": False,
            "red_flags": [],
            "opportunities": [],
            "recommendation": None,
            "use_price_to_sales": False
        }
        
        try:
            # Analyze Revenue Growth
            revenue_growth = defaults.get('revenue_growth_pct', 0)
            hist_revenue_growth = historical_averages.get('revenue_growth_pct')
            
            if revenue_growth < 0:
                analysis["revenue_status"] = "negative"
                analysis["revenue_trend"] = "shrinking"
                analysis["red_flags"].append(
                    f"[STOP] SHRINKING REVENUE: Revenue declining at {revenue_growth:.1f}% annually. "
                    "Like a leaking hull - the business is shrinking."
                )
                analysis["recommendation"] = "REJECT"
            elif revenue_growth < 2:
                analysis["revenue_trend"] = "stagnant"
                analysis["red_flags"].append(
                    f"[WARNING] Stagnant revenue growth ({revenue_growth:.1f}%). Looking for >5% growth."
                )
            
            # Analyze Net Margin
            current_margin = defaults.get('net_margin_pct', 0)
            hist_margin = historical_averages.get('net_margin_pct')
            
            if current_margin < 0:
                analysis["margin_status"] = "negative"
                analysis["use_price_to_sales"] = True  # P/E is meaningless with losses
                
                # Determine margin category
                margin_category = self._categorize_negative_margin(
                    stock, info, financials, income_stmt, current_margin, hist_margin
                )
                analysis["margin_category"] = margin_category
                
                if margin_category == "cyclical":
                    analysis["is_cyclical"] = True
                    analysis["opportunities"].append(
                        f"Cyclical Opportunity: Company showing losses but has cyclical pattern. "
                        "Current margin: {:.1f}%, Historical avg: {:.1f}%. "
                        "Best time to buy cyclicals is often during losses.".format(
                            current_margin, hist_margin or 0
                        )
                    )
                    if analysis["recommendation"] != "REJECT":
                        analysis["recommendation"] = "CYCLICAL_BUY"
                        
                elif margin_category == "turnaround":
                    analysis["has_operating_leverage"] = True
                    analysis["opportunities"].append(
                        f"Turnaround Potential: Current margin {current_margin:.1f}% but "
                        f"historical average {hist_margin:.1f}% suggests recovery potential. "
                        "High operating leverage could mean margin expansion."
                    )
                    if analysis["recommendation"] != "REJECT":
                        analysis["recommendation"] = "TURNAROUND_BUY"
                        
                elif margin_category == "structural":
                    analysis["red_flags"].append(
                        f"Structural Losses: Losing money ({current_margin:.1f}% margin) "
                        "even in favorable conditions. No cyclical pattern detected."
                    )
                    analysis["recommendation"] = "REJECT"
            
            # Check for margin trends (is margin improving or deteriorating?)
            margin_history = self._get_margin_trend(income_stmt, financials)
            if margin_history and len(margin_history) >= 3:
                recent_trend = margin_history[-1] - margin_history[-3] if len(margin_history) >= 3 else 0
                if recent_trend > 2:
                    analysis["opportunities"].append(
                        f"Margins improving: +{recent_trend:.1f}pp over recent periods"
                    )
                elif recent_trend < -2:
                    analysis["red_flags"].append(
                        f"Margins deteriorating: {recent_trend:.1f}pp decline over recent periods"
                    )
            
            # Set final recommendation if not already set
            if not analysis["recommendation"]:
                if analysis["revenue_status"] == "negative":
                    analysis["recommendation"] = "REJECT"
                elif current_margin < 0 and analysis["margin_category"] == "structural":
                    analysis["recommendation"] = "REJECT"
                else:
                    analysis["recommendation"] = "PROCEED"  # Continue with normal analysis
                    
        except Exception as e:
            logger.warning(f"Error analyzing negative values: {e}")
            
        return analysis

    def _categorize_negative_margin(self, stock, info: Dict, financials, income_stmt, 
                                     current_margin: float, hist_margin: float) -> str:
        """
        Categorize negative margins into: cyclical, turnaround, or structural.
        """
        try:
            # Get historical margin data to check for cyclicality
            margins = []
            if income_stmt is not None and not income_stmt.empty and financials is not None:
                if 'Net Income' in income_stmt.index and 'Total Revenue' in financials.index:
                    net_incomes = income_stmt.loc['Net Income'].dropna()
                    revenues = financials.loc['Total Revenue'].dropna()
                    for date in net_incomes.index:
                        if date in revenues.index and revenues[date] != 0:
                            margin = (net_incomes[date] / revenues[date]) * 100
                            margins.append(margin)
            
            if len(margins) >= 3:
                # Check for cyclical pattern (alternating positive/negative or high variance)
                has_positive = any(m > 0 for m in margins)
                has_negative = any(m < 0 for m in margins)
                variance = max(margins) - min(margins) if margins else 0
                
                # Cyclical: Has both positive and negative periods OR high variance
                if has_positive and has_negative:
                    return "cyclical"
                
                # Turnaround: Currently negative but historical average is positive
                if hist_margin and hist_margin > 5 and current_margin < 0:
                    return "turnaround"
                
                # Check for high operating leverage (large fixed costs)
                # Proxy: If historical margins varied significantly with revenue changes
                if variance > 10:  # >10 percentage point swing suggests operating leverage
                    return "turnaround"
            
            # Default to structural if we can't identify a pattern
            return "structural"
            
        except Exception as e:
            logger.warning(f"Error categorizing margin: {e}")
            return "structural"

    def _get_margin_trend(self, income_stmt, financials) -> List[float]:
        """Get list of historical margins for trend analysis."""
        margins = []
        try:
            if income_stmt is not None and not income_stmt.empty and financials is not None:
                if 'Net Income' in income_stmt.index and 'Total Revenue' in financials.index:
                    net_incomes = income_stmt.loc['Net Income'].dropna()
                    revenues = financials.loc['Total Revenue'].dropna()
                    for date in sorted(net_incomes.index):
                        if date in revenues.index and revenues[date] != 0:
                            margin = (net_incomes[date] / revenues[date]) * 100
                            margins.append(margin)
        except Exception as e:
            logger.warning(f"Error getting margin trend: {e}")
        return margins
