from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
import yfinance as yf

class CompetitorAnalysisInput(BaseModel):
    ticker: str = Field(description="The ticker symbol of the company to analyze")
    industry: Optional[str] = Field(default=None, description="The industry of the company (optional)")

class CompetitorAnalysisTool(BaseTool):
    name: str = "competitor_analysis"
    description: str = "Identifies competitors and compares key financial metrics."
    search_tool: Optional[BaseTool] = None
    llm: Optional[Any] = Field(default=None, exclude=True)

    def __init__(self, search_tool=None, llm=None, **kwargs):
        super().__init__(search_tool=search_tool, llm=llm, **kwargs)

    def _run(self, ticker: str, industry: Optional[str] = None) -> Dict[str, Any]:
        raise NotImplementedError("Use _arun instead")

    async def _arun(self, ticker: str, industry: Optional[str] = None) -> Dict[str, Any]:
        main_stock = yf.Ticker(ticker)
        main_info = main_stock.info
        
        if not industry:
            industry = main_info.get('industry', '')
            sector = main_info.get('sector', '')
        
        # 1. Find competitors using Tavily (if available)
        search_results = None
        competitors = []
        
        if self.search_tool:
            search_query = f"top competitors of {ticker} {main_info.get('longName', '')} in {industry} stock tickers"
            search_results = await self.search_tool.ainvoke({"query": search_query})
            
            # Use LLM to extract tickers if available
            if self.llm and search_results:
                try:
                    prompt = f"""
                    Identify the top 5 direct public competitor stock tickers for {ticker} ({main_info.get('longName', '')}) from the following search results.
                    Return ONLY a comma-separated list of tickers (e.g., AAPL, MSFT, GOOGL). Do not include the target ticker {ticker}.
                    
                    Search Results:
                    {search_results}
                    """
                    response = await self.llm.ainvoke(prompt)
                    content = response.content.strip()
                    # Clean up response to get just tickers
                    import re
                    tickers = re.findall(r'\b[A-Z]{1,5}\b', content.upper())
                    # Filter out the target ticker and common non-tickers
                    competitors = [t for t in tickers if t != ticker.upper() and t not in ['NYSE', 'NASDAQ', 'STOCK', 'INC', 'CORP']]
                    competitors = list(set(competitors))[:5] # Top 5 unique
                except Exception as e:
                    print(f"Error extraction competitors with LLM: {e}")

        # Fallback if no competitors found or no LLM
        if not competitors:
            if ticker.upper() in ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META']:
                 competitors = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META']
                 if ticker.upper() in competitors: competitors.remove(ticker.upper())
        
        # If we have competitors, fetch their data
        comparison_data = []
        
        # Add main ticker
        metrics = self._get_key_metrics(ticker)
        if metrics:
            metrics['is_target'] = True
            comparison_data.append(metrics)
            
        for comp_ticker in competitors:
            comp_metrics = self._get_key_metrics(comp_ticker)
            if comp_metrics:
                comp_metrics['is_target'] = False
                comparison_data.append(comp_metrics)
                
        return {
            "ticker": ticker,
            "industry": industry,
            "competitors_analyzed": competitors,
            "comparison_data": comparison_data,
            "search_context": search_results
        }

    def _get_key_metrics(self, ticker: str) -> Optional[Dict[str, Any]]:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            return {
                "ticker": ticker,
                "name": info.get('shortName'),
                "market_cap": info.get('marketCap'),
                "pe_ratio": info.get('trailingPE'),
                "ps_ratio": info.get('priceToSalesTrailing12Months'),
                "pb_ratio": info.get('priceToBook'),
                "gross_margins": info.get('grossMargins'),
                "operating_margins": info.get('operatingMargins'),
                "return_on_equity": info.get('returnOnEquity'),
                "revenue_growth": info.get('revenueGrowth'),
                "current_price": info.get('currentPrice') or info.get('regularMarketPrice'),
                "earnings_growth": info.get('earningsGrowth'),
                "target_price": info.get('targetMeanPrice'),
            }
        except Exception:
            return None
