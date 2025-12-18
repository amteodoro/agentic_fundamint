"""
Financial Modeling Prep API Client

This module provides a fallback data source when yfinance fails to fetch stock data.
API Documentation: https://site.financialmodelingprep.com/developer/docs
"""

import os
import requests
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from functools import lru_cache

# FMP API Configuration
FMP_API_KEY = os.environ.get("FMP_API_KEY", "")
FMP_BASE_URL = "https://financialmodelingprep.com/stable"


def _make_fmp_request(endpoint: str, params: Optional[Dict] = None) -> Optional[Dict | List]:
    """Make a request to the FMP API with error handling."""
    if not FMP_API_KEY:
        # API key not configured
        return None
    
    try:
        url = f"{FMP_BASE_URL}/{endpoint}"
        request_params = {"apikey": FMP_API_KEY}
        if params:
            request_params.update(params)
        
        response = requests.get(url, params=request_params, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        return None


def fetch_fmp_profile(ticker: str) -> Dict[str, Any]:
    """Fetch company profile from FMP API and map to yfinance-compatible format."""
    result = _make_fmp_request("profile", {"symbol": ticker.upper()})
    
    if not result or not isinstance(result, list) or len(result) == 0:
        return {}
    
    profile = result[0]
    
    # Map FMP fields to yfinance-compatible field names
    mapped_info = {
        "symbol": profile.get("symbol"),
        "longName": profile.get("companyName"),
        "sector": profile.get("sector"),
        "industry": profile.get("industry"),
        "longBusinessSummary": profile.get("description"),
        "website": profile.get("website"),
        "country": profile.get("country"),
        "fullTimeEmployees": profile.get("fullTimeEmployees"),
        "marketCap": profile.get("mktCap"),
        "currentPrice": profile.get("price"),
        "regularMarketPrice": profile.get("price"),
        "previousClose": profile.get("price"),  # FMP profile doesn't have previous close
        "beta": profile.get("beta"),
        "dividendYield": profile.get("lastDiv") / profile.get("price") if profile.get("lastDiv") and profile.get("price") else None,
        "exchange": profile.get("exchangeShortName"),
        "currency": profile.get("currency"),
        "ipoDate": profile.get("ipoDate"),
        "cik": profile.get("cik"),
        "isin": profile.get("isin"),
        "cusip": profile.get("cusip"),
    }
    
    return {k: v for k, v in mapped_info.items() if v is not None}


def fetch_fmp_quote(ticker: str) -> Dict[str, Any]:
    """Fetch real-time quote from FMP API and map to yfinance-compatible format."""
    result = _make_fmp_request("quote", {"symbol": ticker.upper()})
    
    if not result or not isinstance(result, list) or len(result) == 0:
        return {}
    
    quote = result[0]
    
    # Map FMP quote fields to yfinance-compatible field names
    mapped_quote = {
        "symbol": quote.get("symbol"),
        "longName": quote.get("name"),
        "currentPrice": quote.get("price"),
        "regularMarketPrice": quote.get("price"),
        "previousClose": quote.get("previousClose"),
        "open": quote.get("open"),
        "dayHigh": quote.get("dayHigh"),
        "dayLow": quote.get("dayLow"),
        "volume": quote.get("volume"),
        "regularMarketVolume": quote.get("volume"),
        "averageVolume": quote.get("avgVolume"),
        "averageDailyVolume10Day": quote.get("avgVolume"),
        "marketCap": quote.get("marketCap"),
        "fiftyTwoWeekHigh": quote.get("yearHigh"),
        "fiftyTwoWeekLow": quote.get("yearLow"),
        "trailingPE": quote.get("pe"),
        "forwardPE": quote.get("priceAvg50") / quote.get("eps") if quote.get("priceAvg50") and quote.get("eps") and quote.get("eps") > 0 else None,
        "trailingEps": quote.get("eps"),
        "sharesOutstanding": quote.get("sharesOutstanding"),
        "exchange": quote.get("exchange"),
        "earningsAnnouncement": quote.get("earningsAnnouncement"),
    }
    
    return {k: v for k, v in mapped_quote.items() if v is not None}


def fetch_fmp_key_metrics(ticker: str) -> Dict[str, Any]:
    """Fetch key metrics from FMP API."""
    result = _make_fmp_request("key-metrics", {"symbol": ticker.upper()})
    
    if not result or not isinstance(result, list) or len(result) == 0:
        return {}
    
    metrics = result[0]  # Get the most recent metrics
    
    # Map to yfinance-compatible field names
    mapped_metrics = {
        "revenuePerShare": metrics.get("revenuePerShare"),
        "netIncomePerShare": metrics.get("netIncomePerShare"),
        "operatingCashFlowPerShare": metrics.get("operatingCashFlowPerShare"),
        "freeCashFlowPerShare": metrics.get("freeCashFlowPerShare"),
        "bookValue": metrics.get("bookValuePerShare"),
        "tangibleBookValue": metrics.get("tangibleBookValuePerShare"),
        "interestDebtPerShare": metrics.get("interestDebtPerShare"),
        "trailingPE": metrics.get("peRatio"),
        "priceToSalesTrailing12Months": metrics.get("priceToSalesRatio"),
        "priceToBook": metrics.get("pbRatio"),
        "enterpriseValue": metrics.get("enterpriseValue"),
        "enterpriseToRevenue": metrics.get("evToSales"),
        "enterpriseToEbitda": metrics.get("evToEbitda"),
        "returnOnEquity": metrics.get("roe"),
        "returnOnAssets": metrics.get("roa"),
        "returnOnCapitalEmployed": metrics.get("roic"),
        "debtToEquity": metrics.get("debtToEquity"),
        "currentRatio": metrics.get("currentRatio"),
        "quickRatio": metrics.get("quickRatio"),
        "dividendYield": metrics.get("dividendYield"),
        "payoutRatio": metrics.get("payoutRatio"),
        "heldPercentInsiders": metrics.get("insiderOwnership"),
        "heldPercentInstitutions": metrics.get("institutionalOwnership"),
    }
    
    return {k: v for k, v in mapped_metrics.items() if v is not None}


def _parse_fmp_statement_to_df(statements: List[Dict], index_field: str = "date") -> pd.DataFrame:
    """Convert FMP statement list to a pandas DataFrame indexed by date, with metrics as rows."""
    if not statements:
        return pd.DataFrame()
    
    try:
        df = pd.DataFrame(statements)
        
        if index_field not in df.columns:
            return pd.DataFrame()
        
        # Set date as column names (transposed format like yfinance)
        df[index_field] = pd.to_datetime(df[index_field], errors='coerce')
        df = df.dropna(subset=[index_field])
        df = df.set_index(index_field)
        df = df.T  # Transpose so dates are columns and metrics are rows
        
        # Rename columns to datetime format
        df.columns = pd.to_datetime(df.columns)
        
        # Remove non-numeric rows
        numeric_df = df.apply(pd.to_numeric, errors='coerce')
        
        # Filter only rows with at least some numeric data
        valid_rows = numeric_df.dropna(how='all').index
        result_df = df.loc[valid_rows]
        
        return result_df
    except Exception as e:
        return pd.DataFrame()


def fetch_fmp_income_statement(ticker: str, limit: int = 10) -> pd.DataFrame:
    """Fetch income statement from FMP API."""
    result = _make_fmp_request("income-statement", {"symbol": ticker.upper(), "limit": limit})
    
    if not result or not isinstance(result, list):
        return pd.DataFrame()
    
    df = _parse_fmp_statement_to_df(result)
    
    if df.empty:
        return df
    
    # Map FMP field names to yfinance-compatible field names
    field_mapping = {
        "revenue": "Total Revenue",
        "costOfRevenue": "Cost Of Revenue",
        "grossProfit": "Gross Profit",
        "grossProfitRatio": "Gross Profit Ratio",
        "researchAndDevelopmentExpenses": "Research And Development",
        "generalAndAdministrativeExpenses": "General And Administrative Expenses",
        "sellingAndMarketingExpenses": "Selling And Marketing Expenses",
        "sellingGeneralAndAdministrativeExpenses": "Selling General And Administrative",
        "otherExpenses": "Other Operating Expenses",
        "operatingExpenses": "Operating Expenses",
        "costAndExpenses": "Cost And Expenses",
        "interestIncome": "Interest Income",
        "interestExpense": "Interest Expense",
        "depreciationAndAmortization": "Depreciation And Amortization",
        "ebitda": "EBITDA",
        "operatingIncome": "Operating Income",
        "incomeBeforeTax": "Pretax Income",
        "incomeTaxExpense": "Tax Provision",
        "netIncome": "Net Income",
        "eps": "Basic EPS",
        "epsdiluted": "Diluted EPS",
        "weightedAverageShsOut": "Basic Average Shares",
        "weightedAverageShsOutDil": "Diluted Average Shares",
    }
    
    df = df.rename(index={k: v for k, v in field_mapping.items() if k in df.index})
    
    return df


def fetch_fmp_balance_sheet(ticker: str, limit: int = 10) -> pd.DataFrame:
    """Fetch balance sheet from FMP API."""
    result = _make_fmp_request("balance-sheet-statement", {"symbol": ticker.upper(), "limit": limit})
    
    if not result or not isinstance(result, list):
        return pd.DataFrame()
    
    df = _parse_fmp_statement_to_df(result)
    
    if df.empty:
        return df
    
    # Map FMP field names to yfinance-compatible field names
    field_mapping = {
        "cashAndCashEquivalents": "Cash And Cash Equivalents",
        "shortTermInvestments": "Short Term Investments",
        "cashAndShortTermInvestments": "Cash Cash Equivalents And Short Term Investments",
        "netReceivables": "Net Receivables",
        "inventory": "Inventory",
        "otherCurrentAssets": "Other Current Assets",
        "totalCurrentAssets": "Total Current Assets",
        "propertyPlantEquipmentNet": "Net PPE",
        "goodwill": "Goodwill",
        "intangibleAssets": "Intangible Assets",
        "goodwillAndIntangibleAssets": "Goodwill And Intangible Assets",
        "longTermInvestments": "Long Term Investments",
        "otherNonCurrentAssets": "Other Non Current Assets",
        "totalNonCurrentAssets": "Total Non Current Assets",
        "totalAssets": "Total Assets",
        "accountPayables": "Current Accrued Expenses",
        "shortTermDebt": "Current Debt",
        "taxPayables": "Tax Payables",
        "deferredRevenue": "Deferred Revenue",
        "otherCurrentLiabilities": "Other Current Liabilities",
        "totalCurrentLiabilities": "Total Current Liabilities",
        "longTermDebt": "Long Term Debt",
        "deferredRevenueNonCurrent": "Deferred Revenue Non Current",
        "deferredTaxLiabilitiesNonCurrent": "Deferred Tax Liabilities Non Current",
        "otherNonCurrentLiabilities": "Other Non Current Liabilities",
        "totalNonCurrentLiabilities": "Total Non Current Liabilities",
        "otherLiabilities": "Other Liabilities",
        "capitalLeaseObligations": "Capital Lease Obligations",
        "totalLiabilities": "Total Liabilities",
        "preferredStock": "Preferred Stock",
        "commonStock": "Common Stock",
        "retainedEarnings": "Retained Earnings",
        "accumulatedOtherComprehensiveIncomeLoss": "Accumulated Other Comprehensive Income",
        "othertotalStockholdersEquity": "Other Stockholders Equity",
        "totalStockholdersEquity": "Stockholders Equity",
        "totalEquity": "Total Equity",
        "totalLiabilitiesAndStockholdersEquity": "Total Liabilities And Equity",
        "minorityInterest": "Minority Interest",
        "totalLiabilitiesAndTotalEquity": "Total Liabilities And Total Equity",
        "totalInvestments": "Total Investments",
        "totalDebt": "Total Debt",
        "netDebt": "Net Debt",
    }
    
    df = df.rename(index={k: v for k, v in field_mapping.items() if k in df.index})
    
    return df


def fetch_fmp_cash_flow(ticker: str, limit: int = 10) -> pd.DataFrame:
    """Fetch cash flow statement from FMP API."""
    result = _make_fmp_request("cash-flow-statement", {"symbol": ticker.upper(), "limit": limit})
    
    if not result or not isinstance(result, list):
        return pd.DataFrame()
    
    df = _parse_fmp_statement_to_df(result)
    
    if df.empty:
        return df
    
    # Map FMP field names to yfinance-compatible field names
    field_mapping = {
        "netIncome": "Net Income",
        "depreciationAndAmortization": "Depreciation And Amortization",
        "deferredIncomeTax": "Deferred Income Tax",
        "stockBasedCompensation": "Stock Based Compensation",
        "changeInWorkingCapital": "Change In Working Capital",
        "accountsReceivables": "Change In Receivables",
        "inventory": "Change In Inventory",
        "accountsPayables": "Change In Payables",
        "otherWorkingCapital": "Other Working Capital",
        "otherNonCashItems": "Other Non Cash Items",
        "netCashProvidedByOperatingActivities": "Operating Cash Flow",
        "investmentsInPropertyPlantAndEquipment": "Capital Expenditure",
        "acquisitionsNet": "Net Acquisitions",
        "purchasesOfInvestments": "Purchase Of Investments",
        "salesMaturitiesOfInvestments": "Sale Of Investments",
        "otherInvestingActivites": "Other Investing Activities",
        "netCashUsedForInvestingActivites": "Investing Cash Flow",
        "debtRepayment": "Debt Repayment",
        "commonStockIssued": "Common Stock Issued",
        "commonStockRepurchased": "Common Stock Repurchased",
        "dividendsPaid": "Cash Dividends Paid",
        "otherFinancingActivites": "Other Financing Activities",
        "netCashUsedProvidedByFinancingActivities": "Financing Cash Flow",
        "effectOfForexChangesOnCash": "Effect Of Forex Changes On Cash",
        "netChangeInCash": "Net Change In Cash",
        "cashAtEndOfPeriod": "End Cash Position",
        "cashAtBeginningOfPeriod": "Beginning Cash Position",
        "operatingCashFlow": "Operating Cash Flow",
        "capitalExpenditure": "Capital Expenditure",
        "freeCashFlow": "Free Cash Flow",
    }
    
    df = df.rename(index={k: v for k, v in field_mapping.items() if k in df.index})
    
    return df


def fetch_fmp_historical_prices(ticker: str, years: int = 11) -> pd.DataFrame:
    """Fetch historical price data from FMP API."""
    result = _make_fmp_request(f"historical-price-eod/full", {"symbol": ticker.upper()})
    
    if not result or not isinstance(result, dict):
        return pd.DataFrame()
    
    historical = result.get("historical", [])
    
    if not historical:
        return pd.DataFrame()
    
    try:
        df = pd.DataFrame(historical)
        
        # Convert date column
        df['Date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['Date'])
        df = df.set_index('Date')
        
        # Rename columns to match yfinance format
        column_mapping = {
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "adjClose": "Adj Close",
            "volume": "Volume",
        }
        
        df = df.rename(columns=column_mapping)
        
        # Keep only the columns we need
        required_cols = ["Open", "High", "Low", "Close", "Volume"]
        available_cols = [col for col in required_cols if col in df.columns]
        df = df[available_cols]
        
        # Sort by date ascending
        df = df.sort_index(ascending=True)
        
        # Filter to requested years
        cutoff_date = datetime.now() - timedelta(days=years * 365)
        df = df[df.index >= cutoff_date]
        
        return df
    except Exception as e:
        return pd.DataFrame()


def fetch_fmp_dividends(ticker: str) -> pd.Series:
    """Fetch dividend history from FMP API."""
    # FMP doesn't have a direct dividends endpoint in the stable API
    # We'll try to get it from the historical-price-full endpoint with dividends data
    result = _make_fmp_request("historical-price-eod/dividend-adjusted", {"symbol": ticker.upper()})
    
    if not result or not isinstance(result, dict):
        return pd.Series(dtype=float)
    
    historical = result.get("historical", [])
    
    if not historical:
        return pd.Series(dtype=float)
    
    try:
        # FMP dividend-adjusted prices don't directly provide dividend amounts
        # This is a limitation - we return an empty series for now
        return pd.Series(dtype=float)
    except Exception as e:
        return pd.Series(dtype=float)


def fetch_stock_data_fmp(ticker_symbol: str) -> Dict[str, Any]:
    """
    Fetch complete stock data from Financial Modeling Prep API.
    Returns data in a format compatible with the yfinance data structure.
    """
    data: Dict[str, Any] = {
        "info": {},
        "financials": pd.DataFrame(),
        "balance_sheet": pd.DataFrame(),
        "cash_flow": pd.DataFrame(),
        "major_holders": pd.DataFrame(),
        "dividends": pd.Series(dtype=float),
        "actions": pd.DataFrame(),
        "history": pd.DataFrame(),
        "data_source": "financial_modeling_prep"
    }
    
    # 1. Fetch profile and quote data for info
    profile_info = fetch_fmp_profile(ticker_symbol)
    quote_info = fetch_fmp_quote(ticker_symbol)
    key_metrics = fetch_fmp_key_metrics(ticker_symbol)
    
    # Merge all info data (quote takes priority over profile)
    data["info"] = {**profile_info, **key_metrics, **quote_info}
    
    if not data["info"].get("symbol"):
        # If we couldn't get basic info, FMP likely doesn't have this ticker
        return data
    
    # 2. Fetch financial statements
    data["financials"] = fetch_fmp_income_statement(ticker_symbol)
    data["balance_sheet"] = fetch_fmp_balance_sheet(ticker_symbol)
    data["cash_flow"] = fetch_fmp_cash_flow(ticker_symbol)
    
    # 3. Fetch historical prices
    data["history"] = fetch_fmp_historical_prices(ticker_symbol)
    
    # 4. Fetch dividends
    data["dividends"] = fetch_fmp_dividends(ticker_symbol)
    
    return data


def is_fmp_available() -> bool:
    """Check if FMP API key is configured and API is accessible."""
    if not FMP_API_KEY:
        return False
    
    # Quick connectivity check
    try:
        result = _make_fmp_request("profile", {"symbol": "AAPL"})
        return result is not None and len(result) > 0
    except Exception:
        return False


def search_fmp(query: str, limit: int = 10) -> List[Dict[str, str]]:
    """
    Search for stocks by company name or ticker symbol using FMP API.
    
    Args:
        query: Search query (company name or ticker)
        limit: Maximum number of results to return
        
    Returns:
        List of dictionaries with 'symbol' and 'longName' keys
    """
    if not FMP_API_KEY:
        return []
    
    # Try the search-name endpoint first (for company name search)
    try:
        url = f"{FMP_BASE_URL}/search-name"
        params = {
            "query": query,
            "limit": limit,
            "apikey": FMP_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            results = response.json()
            
            if results and isinstance(results, list):
                search_results = []
                for item in results[:limit]:
                    # FMP search returns different field names
                    symbol = item.get("symbol", "")
                    name = item.get("name", "") or item.get("companyName", "")
                    exchange = item.get("exchangeShortName", "") or item.get("exchange", "")
                    
                    if symbol and name:
                        search_results.append({
                            "symbol": symbol,
                            "longName": f"{name}" + (f" ({exchange})" if exchange else "")
                        })
                
                return search_results
                
    except Exception as e:
        print(f"FMP search error: {e}")
    
    # If search-name fails, try the ticker search as fallback
    try:
        url = f"{FMP_BASE_URL}/search"
        params = {
            "query": query,
            "limit": limit,
            "apikey": FMP_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            results = response.json()
            
            if results and isinstance(results, list):
                search_results = []
                for item in results[:limit]:
                    symbol = item.get("symbol", "")
                    name = item.get("name", "") or item.get("companyName", "")
                    exchange = item.get("exchangeShortName", "") or item.get("exchange", "")
                    
                    if symbol:
                        search_results.append({
                            "symbol": symbol,
                            "longName": name or symbol + (f" ({exchange})" if exchange else "")
                        })
                
                return search_results
                
    except Exception as e:
        print(f"FMP ticker search error: {e}")
    
    return []
