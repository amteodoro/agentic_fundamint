from fastapi import APIRouter, HTTPException
from ..data_fetcher import fetch_stock_data, get_safe_value
from ..analysis import clean_data
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
import pandas as pd
from datetime import date

# 1. Define the Pydantic Models
class StockProfile(BaseModel):
    """Pydantic model for a stock's profile information."""
    longName: Optional[str] = Field(None, description="The full name of the company.")
    sector: Optional[str] = Field(None, description="The sector the company operates in.")
    fullTimeEmployees: Optional[int] = Field(None, description="The number of full-time employees.")
    longBusinessSummary: Optional[str] = Field(None, description="A summary of the company's business.")
    country: Optional[str] = Field(None, description="The country where the company is based.")
    website: Optional[str] = Field(None, description="The company's official website.")
    sharesOutstanding: Optional[int] = Field(None, description="The number of shares outstanding.")
    dataSource: Optional[str] = Field(None, description="The data source that provided this information (yfinance, financial_modeling_prep, or mixed).")

from pydantic import BaseModel, Field, RootModel

class FinancialStatementRow(RootModel[Dict[str, Optional[str | float | int]]]):
    """
    Pydantic model for a single row of financial statement data.
    The actual keys will depend on the financial statement type (e.g., 'Date', 'Total Revenue', etc.)
    """
    pass

class FinancialStatementsResponse(BaseModel):
    """
    Pydantic model for the financial statements API response.
    """
    financials: List[FinancialStatementRow]

class PriceDataPoint(BaseModel):
    """Pydantic model for a single historical price data point."""
    Date: date
    Open: float
    High: float
    Low: float
    Close: float
    Volume: int

class StockPriceHistory(BaseModel):
    """Pydantic model for a list of historical price data points."""
    history: List[PriceDataPoint]

class SearchResult(BaseModel):
    """Pydantic model for a single stock search result."""
    symbol: str
    longName: Optional[str] = None

class StockSearchResponse(BaseModel):
    """Pydantic model for the stock search API response."""
    results: List[SearchResult]

class KeyMetric(BaseModel):
    """Pydantic model for a single key metric."""
    label: str
    value: Optional[str] = None
    rawValue: Optional[float] = Field(None, description="Raw numeric value for currency conversion")
    isCurrency: bool = Field(False, description="Whether this metric represents a currency value")

class KeyMetricsResponse(BaseModel):
    """Pydantic model for the key metrics API response."""
    metrics: List[KeyMetric]
    dataSource: Optional[str] = Field(None, description="The data source that provided this information.")


class StockQuote(BaseModel):
    """Pydantic model for a quick stock quote."""
    ticker: str
    price: float
    change: float
    changePercent: float
    previousClose: Optional[float] = None
    dayHigh: Optional[float] = None
    dayLow: Optional[float] = None
    volume: Optional[int] = None
    dataSource: Optional[str] = Field(None, description="The data source that provided this information.")


# Create a new router to organize stock-related endpoints
router = APIRouter()

# 2. Create the API Endpoints
@router.get("/stock/{ticker}/profile", response_model=StockProfile)
async def get_stock_profile(ticker: str, source: Optional[str] = None):
    """
    Retrieves profile information for a given stock ticker.
    
    Args:
        ticker: Stock ticker symbol
        source: Data source preference ("yfinance" or "fmp")
    """
    stock_data = fetch_stock_data(ticker, source=source)
    info = stock_data.get("info", {})

    if not info or info.get('longName') is None:
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found or no profile information available.")

    try:
        
        profile_data = StockProfile(
            longName=info.get('longName'),
            sector=info.get('sector'),
            fullTimeEmployees=info.get('fullTimeEmployees'),
            longBusinessSummary=info.get('longBusinessSummary'),
            country=info.get('country'),
            website=info.get('website'),
            sharesOutstanding=info.get('sharesOutstanding'),
            dataSource=stock_data.get('data_source', 'unknown')
        )
        
        return profile_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/{ticker}/quote", response_model=StockQuote)
async def get_stock_quote(ticker: str, source: Optional[str] = None):
    """
    Retrieves current quote information for a given stock ticker.
    Returns current price, change, and change percent.
    
    Args:
        ticker: Stock ticker symbol
        source: Data source preference ("yfinance" or "fmp")
    """
    stock_data = fetch_stock_data(ticker, source=source)
    info = stock_data.get("info", {})

    if not info or info.get('longName') is None:
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found or no quote available.")

    try:
        # Get price fields from yfinance info dict
        current_price = info.get('currentPrice') or info.get('regularMarketPrice') or 0
        previous_close = info.get('previousClose') or info.get('regularMarketPreviousClose') or 0
        
        # Calculate change and percent
        change = current_price - previous_close if previous_close else 0
        change_percent = (change / previous_close * 100) if previous_close else 0
        
        quote_data = StockQuote(
            ticker=ticker.upper(),
            price=round(current_price, 2),
            change=round(change, 2),
            changePercent=round(change_percent, 2),
            previousClose=round(previous_close, 2) if previous_close else None,
            dayHigh=info.get('dayHigh') or info.get('regularMarketDayHigh'),
            dayLow=info.get('dayLow') or info.get('regularMarketDayLow'),
            volume=info.get('volume') or info.get('regularMarketVolume'),
            dataSource=stock_data.get('data_source', 'unknown')
        )
        
        return quote_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/{ticker}/financials", response_model=FinancialStatementsResponse)
async def get_stock_financials(ticker: str, statement_type: str = "annual", source: Optional[str] = None):
    """
    Retrieves the annual income statement for a given stock ticker.
    """
    stock_data = fetch_stock_data(ticker, source=source)
    info = stock_data.get("info", {})

    if not info or info.get('longName') is None:
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found or no financial information available.")

    try:
        financials_df = stock_data.get("financials")
        if statement_type == "quarterly":
            # Note: fetch_stock_data currently only fetches annual financials.
            # If quarterly is needed, data_fetcher.py would need to be extended.
            raise HTTPException(status_code=400, detail="Quarterly financials not yet supported by data_fetcher.")

        

        if financials_df.empty:
            raise HTTPException(status_code=404, detail=f"Financials not found for ticker '{ticker}'.")

        financials_df = financials_df.where(pd.notna(financials_df), None)
        financials_df.columns = financials_df.columns.strftime('%Y-%m-%d')

        # Transpose the DataFrame so metrics are rows and dates are columns
        financials_df = financials_df.T
        financials_df.index.name = "Date"
        financials_df = financials_df.reset_index()

        # Convert to a list of dictionaries
        financials_list = financials_df.to_dict(orient='records')
        
        return {"financials": clean_data(financials_list)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stock/{ticker}/price-history", response_model=StockPriceHistory)
async def get_stock_price_history(ticker: str, period: str = "1y"):
    """
    Retrieves historical price data for a given stock ticker.
    Default period is 1 year.
    """
    stock_data = fetch_stock_data(ticker)
    info = stock_data.get("info", {})

    if not info or info.get('longName') is None:
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found or no price history available.")

    try:
        history_df = stock_data.get("history")

        if history_df.empty:
            raise HTTPException(status_code=404, detail=f"Price history not found for ticker '{ticker}' for period '{period}'.")

        # Reset index to make 'Date' a column
        history_df = history_df.reset_index()

        # Convert DataFrame to a list of dictionaries, suitable for Pydantic
        # Ensure column names match Pydantic model fields (case-sensitive)
        # Convert Timestamp to date object
        history_data = []
        for index, row in history_df.iterrows():
            history_data.append(PriceDataPoint(
                Date=row['Date'].date(), # Convert Timestamp to date
                Open=row['Open'],
                High=row['High'],
                Low=row['Low'],
                Close=row['Close'],
                Volume=row['Volume']
            ))

        return StockPriceHistory(history=history_data)

    except Exception as e:
        # Catch any other unexpected errors
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@router.get("/search", response_model=StockSearchResponse)
async def search_stocks(q: str, source: Optional[str] = None):
    """
    Searches for stocks based on a query string (ticker symbol or company name).
    
    Args:
        q: Search query (ticker symbol or company name, e.g., "AAPL" or "Apple")
        source: Data source preference ("yfinance" or "fmp")
    """
    if not q:  # Handle empty query string
        return StockSearchResponse(results=[])
    
    query = q.strip()
    results = []
    
    # Use FMP search if selected
    if source == "fmp":
        try:
            from ..fmp_fetcher import search_fmp
            fmp_results = search_fmp(query, limit=10)
            if fmp_results:
                for item in fmp_results:
                    results.append(SearchResult(
                        symbol=item.get("symbol", ""),
                        longName=item.get("longName", item.get("symbol", ""))
                    ))
                return StockSearchResponse(results=results)
        except Exception as e:
            print(f"FMP search error: {e}")
    
    # Default: Use yfinance search
    try:
        import yfinance as yf
        
        # Use yfinance's Search functionality
        search = yf.Search(query, max_results=10)
        
        # Get quotes (stock results)
        if hasattr(search, 'quotes') and search.quotes:
            for quote in search.quotes[:10]:
                symbol = quote.get('symbol', '')
                name = quote.get('longname') or quote.get('shortname') or quote.get('name') or symbol
                exchange = quote.get('exchange', '')
                
                if symbol:
                    display_name = name
                    if exchange and exchange not in name:
                        display_name += f" ({exchange})"
                    
                    results.append(SearchResult(
                        symbol=symbol,
                        longName=display_name
                    ))
        
        # If yfinance Search didn't find anything, fall back to direct ticker lookup
        if not results:
            stock_data = fetch_stock_data(query.upper(), source=source)
            info = stock_data.get("info", {})
            
            if info and info.get('longName'):
                results.append(SearchResult(
                    symbol=query.upper(),
                    longName=info.get('longName')
                ))
                
    except Exception as e:
        print(f"yfinance search error: {e}")
        
        # Final fallback: try direct ticker lookup
        try:
            stock_data = fetch_stock_data(query.upper(), source=source)
            info = stock_data.get("info", {})
            
            if info and info.get('longName'):
                results.append(SearchResult(
                    symbol=query.upper(),
                    longName=info.get('longName')
                ))
        except Exception:
            pass
    
    return StockSearchResponse(results=results)

@router.get("/stock/{ticker}/metrics", response_model=KeyMetricsResponse)
async def get_key_metrics(ticker: str, source: Optional[str] = None):
    """
    Retrieves key metrics for a given stock ticker.
    """
    stock_data = fetch_stock_data(ticker, source=source)
    info = stock_data.get("info", {})

    if not info or info.get('longName') is None:
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found or no key metrics available.")

    try:
        metrics_list: List[KeyMetric] = []

        # Define the metrics to extract and their display labels
        metrics_to_extract = {
            "Market Cap": "marketCap",
            "PE Ratio (TTM)": "trailingPE",
            "Forward PE": "forwardPE",
            "Dividend Yield": "dividendYield",
            "Beta": "beta",
            "Volume": "volume",
            "Average Daily Volume": "averageDailyVolume10Day",
            "52 Week High": "fiftyTwoWeekHigh",
            "52 Week Low": "fiftyTwoWeekLow",
            "Previous Close": "previousClose",
            "Open": "open",
        }

        # Currency metrics (can be converted on frontend)
        currency_metrics = {"Market Cap", "52 Week High", "52 Week Low", "Previous Close", "Open"}

        for label, key in metrics_to_extract.items():
            value = info.get(key)
            if value is not None:
                is_currency = label in currency_metrics
                raw_value = float(value) if isinstance(value, (int, float)) else None
                
                # Format percentage values
                if "Yield" in label and isinstance(value, (int, float)):
                    metrics_list.append(KeyMetric(label=label, value=f"{value:.2%}", rawValue=raw_value, isCurrency=False))
                # Format large numbers (e.g., Market Cap, Volume)
                elif "Cap" in label or "Volume" in label and isinstance(value, (int, float)):
                    metrics_list.append(KeyMetric(label=label, value=f"{value:,.0f}", rawValue=raw_value, isCurrency=is_currency))
                else:
                    metrics_list.append(KeyMetric(label=label, value=str(value), rawValue=raw_value, isCurrency=is_currency))

        if not metrics_list:
            raise HTTPException(status_code=404, detail=f"No key metrics found for ticker '{ticker}'.")

        return KeyMetricsResponse(metrics=metrics_list, dataSource=stock_data.get('data_source', 'unknown'))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


class BalanceSheetResponse(BaseModel):
    """
    Pydantic model for the balance sheet API response.
    """
    balance_sheet: List[FinancialStatementRow]

@router.get("/stock/{ticker}/balance-sheet", response_model=BalanceSheetResponse)
async def get_balance_sheet(ticker: str, statement_type: str = "annual"):
    """
    Retrieves the annual or quarterly balance sheet for a given stock ticker.
    """
    stock_data = fetch_stock_data(ticker)
    info = stock_data.get("info", {})
    
    if not info or info.get('longName') is None:
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found or no balance sheet information available.")

    try:
        balance_sheet_df = stock_data.get("balance_sheet")
        if statement_type == "quarterly":
            # Note: fetch_stock_data currently only fetches annual balance sheets.
            # If quarterly is needed, data_fetcher.py would need to be extended.
            raise HTTPException(status_code=400, detail="Quarterly balance sheets not yet supported by data_fetcher.")

        

        if balance_sheet_df.empty:
            raise HTTPException(status_code=404, detail=f"Balance sheet not found for ticker '{ticker}'.")

        balance_sheet_df = balance_sheet_df.where(pd.notna(balance_sheet_df), None)
        balance_sheet_df.columns = balance_sheet_df.columns.strftime('%Y-%m-%d')
        balance_sheet_df = balance_sheet_df.T
        balance_sheet_df.index.name = "Date"
        balance_sheet_df = balance_sheet_df.reset_index()
        balance_sheet_list = balance_sheet_df.to_dict(orient='records')
        
        
        return {"balance_sheet": clean_data(balance_sheet_list)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class CashFlowResponse(BaseModel):
    """
    Pydantic model for the cash flow API response.
    """
    cash_flow: List[FinancialStatementRow]

@router.get("/stock/{ticker}/cash-flow", response_model=CashFlowResponse)
async def get_cash_flow(ticker: str, statement_type: str = "annual"):
    """
    Retrieves the annual or quarterly cash flow statement for a given stock ticker.
    """
    stock_data = fetch_stock_data(ticker)
    info = stock_data.get("info", {})
    
    if not info or info.get('longName') is None:
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found or no cash flow information available.")

    try:
        cash_flow_df = stock_data.get("cash_flow")
        if statement_type == "quarterly":
            # Note: fetch_stock_data currently only fetches annual cash flow.
            # If quarterly is needed, data_fetcher.py would need to be extended.
            raise HTTPException(status_code=400, detail="Quarterly cash flow not yet supported by data_fetcher.")

        

        if cash_flow_df.empty:
            raise HTTPException(status_code=404, detail=f"Cash flow statement not found for ticker '{ticker}'.")

        cash_flow_df = cash_flow_df.where(pd.notna(cash_flow_df), None)
        cash_flow_df.columns = cash_flow_df.columns.strftime('%Y-%m-%d')
        cash_flow_df = cash_flow_df.T
        cash_flow_df.index.name = "Date"
        cash_flow_df = cash_flow_df.reset_index()
        cash_flow_list = cash_flow_df.to_dict(orient='records')
        
        return {"cash_flow": clean_data(cash_flow_list)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class DividendDataPoint(BaseModel):
    """Pydantic model for a single dividend data point."""
    Date: date
    Dividends: float

class DividendHistory(BaseModel):
    """Pydantic model for a list of dividend data points."""
    history: List[DividendDataPoint]

@router.get("/stock/{ticker}/dividends", response_model=DividendHistory)
async def get_dividends(ticker: str):
    """
    Retrieves the dividend history for a given stock ticker.
    """
    stock_data = fetch_stock_data(ticker)
    info = stock_data.get("info", {})
    
    if not info or info.get('longName') is None:
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found or no dividend information available.")

    try:
        dividends_df = stock_data.get("dividends")
        
        if dividends_df.empty:
            return DividendHistory(history=[])

        dividends_df = dividends_df.reset_index()
        dividends_df.columns = ['Date', 'Dividends']
        
        dividends_data = []
        for index, row in dividends_df.iterrows():
            dividends_data.append(DividendDataPoint(
                Date=row['Date'].date(),
                Dividends=row['Dividends']
            ))
        print(f"[Backend] Returning dividends for {ticker}: {len(dividends_data)} records")
        return DividendHistory(history=dividends_data)
    except Exception as e:
        print(f"[Backend] Error fetching dividends for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Exchange rate response model
class ExchangeRateResponse(BaseModel):
    """Pydantic model for exchange rate response."""
    fromCurrency: str = Field(..., description="Source currency code")
    toCurrency: str = Field(..., description="Target currency code")
    rate: float = Field(..., description="Exchange rate")
    timestamp: str = Field(..., description="Timestamp of the rate")


# Cache for exchange rate (to avoid too many API calls)
_exchange_rate_cache: Dict[str, tuple] = {}
EXCHANGE_RATE_CACHE_TTL = 60 * 5  # 5 minutes


@router.get("/exchange-rate", response_model=ExchangeRateResponse)
async def get_exchange_rate(fromCurrency: str = "USD", toCurrency: str = "EUR"):
    """
    Get the current exchange rate between two currencies.
    Uses yfinance to fetch real-time forex data.
    
    Args:
        fromCurrency: Source currency code (default: USD)
        toCurrency: Target currency code (default: EUR)
    """
    import yfinance as yf
    from datetime import datetime
    import time
    
    # Normalize currency codes
    from_code = fromCurrency.upper()
    to_code = toCurrency.upper()
    cache_key = f"{from_code}_{to_code}"
    
    # Check cache
    if cache_key in _exchange_rate_cache:
        cached_rate, cached_time = _exchange_rate_cache[cache_key]
        if time.time() - cached_time < EXCHANGE_RATE_CACHE_TTL:
            return ExchangeRateResponse(
                fromCurrency=from_code,
                toCurrency=to_code,
                rate=cached_rate,
                timestamp=datetime.fromtimestamp(cached_time).isoformat()
            )
    
    # If same currency, rate is 1.0
    if from_code == to_code:
        return ExchangeRateResponse(
            fromCurrency=from_code,
            toCurrency=to_code,
            rate=1.0,
            timestamp=datetime.now().isoformat()
        )
    
    try:
        # yfinance forex ticker format: EURUSD=X, USDEUR=X, etc.
        ticker_symbol = f"{from_code}{to_code}=X"
        
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        rate = info.get('regularMarketPrice') or info.get('previousClose')
        
        if rate:
            # Cache the result
            _exchange_rate_cache[cache_key] = (rate, time.time())
            
            return ExchangeRateResponse(
                fromCurrency=from_code,
                toCurrency=to_code,
                rate=rate,
                timestamp=datetime.now().isoformat()
            )
        
        # Fallback: try the inverse rate
        inverse_ticker_symbol = f"{to_code}{from_code}=X"
        inverse_ticker = yf.Ticker(inverse_ticker_symbol)
        inverse_info = inverse_ticker.info
        
        inverse_rate = inverse_info.get('regularMarketPrice') or inverse_info.get('previousClose')
        
        if inverse_rate and inverse_rate > 0:
            rate = 1.0 / inverse_rate
            _exchange_rate_cache[cache_key] = (rate, time.time())
            
            return ExchangeRateResponse(
                fromCurrency=from_code,
                toCurrency=to_code,
                rate=rate,
                timestamp=datetime.now().isoformat()
            )
        
        # If all else fails, return default rates for common pairs
        default_rates = {
            "USD_EUR": 0.92,
            "EUR_USD": 1.09,
        }
        
        if cache_key in default_rates:
            return ExchangeRateResponse(
                fromCurrency=from_code,
                toCurrency=to_code,
                rate=default_rates[cache_key],
                timestamp=datetime.now().isoformat()
            )
        
        raise HTTPException(status_code=404, detail=f"Exchange rate not found for {from_code}/{to_code}")
        
    except Exception as e:
        # Return default for USD/EUR if there's an error
        if from_code == "USD" and to_code == "EUR":
            return ExchangeRateResponse(
                fromCurrency=from_code,
                toCurrency=to_code,
                rate=0.92,
                timestamp=datetime.now().isoformat()
            )
        elif from_code == "EUR" and to_code == "USD":
            return ExchangeRateResponse(
                fromCurrency=from_code,
                toCurrency=to_code,
                rate=1.09,
                timestamp=datetime.now().isoformat()
            )
        
        raise HTTPException(status_code=500, detail=f"Error fetching exchange rate: {str(e)}")
