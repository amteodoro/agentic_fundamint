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

class KeyMetricsResponse(BaseModel):
    """Pydantic model for the key metrics API response."""
    metrics: List[KeyMetric]

# Create a new router to organize stock-related endpoints
router = APIRouter()

# 2. Create the API Endpoints
@router.get("/stock/{ticker}/profile", response_model=StockProfile)
async def get_stock_profile(ticker: str):
    """
    Retrieves profile information for a given stock ticker.
    """
    stock_data = fetch_stock_data(ticker)
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
            sharesOutstanding=info.get('sharesOutstanding')
        )
        
        return profile_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/{ticker}/financials", response_model=FinancialStatementsResponse)
async def get_stock_financials(ticker: str, statement_type: str = "annual"):
    """
    Retrieves the annual income statement for a given stock ticker.
    """
    stock_data = fetch_stock_data(ticker)
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
async def search_stocks(q: str):
    """
    Searches for stocks based on a query string.
    """
    if not q:  # Handle empty query string
        return StockSearchResponse(results=[])

    # Attempt to fetch data using the new data_fetcher
    stock_data = fetch_stock_data(q.upper())
    info = stock_data.get("info", {})

    if info and info.get('longName'):
        # If valid, return it as a search result
        return StockSearchResponse(results=[SearchResult(symbol=q.upper(), longName=info.get('longName'))])
    else:
        # If not valid, return an empty list
        return StockSearchResponse(results=[])

@router.get("/stock/{ticker}/metrics", response_model=KeyMetricsResponse)
async def get_key_metrics(ticker: str):
    """
    Retrieves key metrics for a given stock ticker.
    """
    stock_data = fetch_stock_data(ticker)
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

        for label, key in metrics_to_extract.items():
            value = info.get(key)
            if value is not None:
                # Format percentage values
                if "Yield" in label and isinstance(value, (int, float)):
                    metrics_list.append(KeyMetric(label=label, value=f"{value:.2%}"))
                # Format large numbers (e.g., Market Cap, Volume)
                elif "Cap" in label or "Volume" in label and isinstance(value, (int, float)):
                    metrics_list.append(KeyMetric(label=label, value=f"{value:,.0f}"))
                else:
                    metrics_list.append(KeyMetric(label=label, value=str(value)))

        if not metrics_list:
            raise HTTPException(status_code=404, detail=f"No key metrics found for ticker '{ticker}'.")

        return KeyMetricsResponse(metrics=metrics_list)

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

