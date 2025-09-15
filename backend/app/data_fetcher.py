

import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
from datetime import date, datetime, timedelta
from functools import lru_cache

# Cache configuration
CACHE_MAXSIZE = 128
CACHE_TTL_SECONDS = 300  # 5 minutes

# --- Fallback Libraries (Optional) ---
try:
    from investiny import search_assets
    from investiny.info import overview as investiny_overview
    from investiny.fundamentus import financial_summary as investiny_financial_summary
    investiny_available = True
except ImportError:
    investiny_available = False
    def search_assets(*args, **kwargs): return []
    def investiny_overview(*args, **kwargs): return {}
    def investiny_financial_summary(*args, **kwargs): return pd.DataFrame()

try:
    import fix_yahoo_finance as fyf
except ImportError:
    fyf = None

try:
    from finvizfinance.stock import Stock as FinvizStock
    finviz_available = True
except ImportError:
    finviz_available = False
    def FinvizStock(*args, **kwargs): return None

# --- Configuration ---
YEARS_OF_DATA = 10

# --- Helper Functions ---
def convert_financial_string_to_float(value_str):
    if isinstance(value_str, (int, float)): return float(value_str)
    if not isinstance(value_str, str): return None
    value_str = value_str.replace(',', '').strip()
    if not value_str or value_str.lower() == 'n/a' or value_str == '-': return None
    multiplier = 1.0; is_percentage = False
    if value_str.endswith('%'): is_percentage = True; value_str = value_str[:-1]
    elif value_str.upper().endswith('B'): multiplier = 1e9; value_str = value_str[:-1]
    elif value_str.upper().endswith('M'): multiplier = 1e6; value_str = value_str[:-1]
    elif value_str.upper().endswith('K'): multiplier = 1e3; value_str = value_str[:-1]
    try:
        numeric_val = float(value_str)
        return numeric_val / 100.0 if is_percentage else numeric_val * multiplier
    except ValueError: return None

def get_safe_value(data_structure, key, is_column_data=False):
    if data_structure is None: return None
    if isinstance(data_structure, dict): return data_structure.get(key)
    if is_column_data:
        if not isinstance(data_structure, pd.Series): return None
        return data_structure.get(key)
    if isinstance(data_structure, pd.DataFrame):
        if key in data_structure.index: return data_structure.loc[key]
        return None
    if isinstance(data_structure, pd.Series): return data_structure.get(key)
    return None

# --- Fallback Helpers ---
asset_id_cache: Dict[str, str] = {} # Global cache for investiny asset IDs

def get_investiny_asset_id(ticker: str) -> Optional[str]:
    if ticker in asset_id_cache: return asset_id_cache[ticker]
    if not investiny_available: return None
    try:
        results = search_assets(query=ticker, limit=1, type="stock")
        if results and isinstance(results, list) and len(results) > 0:
            asset_id = results[0].get("id_")
            if asset_id: asset_id_cache[ticker] = asset_id; return asset_id
    except Exception as e: pass # Suppress error message
    return None

def get_series_from_investiny_summary(ticker: str, investiny_column_name: str, target_metric_name: str) -> Optional[pd.Series]:
    if not investiny_available: return None
    asset_id = get_investiny_asset_id(ticker)
    if not asset_id: return None
    
    try:
        financial_data = investiny_financial_summary(asset_id=asset_id, period="annual", summary_type="income_statement")
        if not (isinstance(financial_data, pd.DataFrame) and not financial_data.empty): return None
        summary_df = financial_data
        if investiny_column_name in summary_df.columns:
            series = summary_df[investiny_column_name].copy()
            series.index = pd.to_datetime(series.index, errors='coerce')
            series = series.dropna().sort_index()
            converted_values = [convert_financial_string_to_float(val) for val in series.values]
            valid_indices = [idx for idx, val in zip(series.index, converted_values) if val is not None]
            valid_converted_values = [val for val in converted_values if val is not None]
            if valid_converted_values:
                series = pd.Series(valid_converted_values, index=pd.Index(valid_indices, dtype='datetime64[ns]'))
                if not series.empty: return series
    except Exception as e: pass # Suppress error message
    return None

# --- Cache configuration ---
CACHE_MAXSIZE = 128
CACHE_TTL_SECONDS = 300  # 5 minutes

@lru_cache(maxsize=CACHE_MAXSIZE)
def _fetch_stock_data_cached(ticker_symbol: str, _timestamp: int) -> Dict[str, Any]:
    # The _timestamp argument is used to control cache invalidation.
    # It's not directly used in data fetching but changes when the cache should be cleared.
    data: Dict[str, Any] = {
        "info": {},
        "financials": pd.DataFrame(),
        "balance_sheet": pd.DataFrame(),
        "cash_flow": pd.DataFrame(),
        "major_holders": pd.DataFrame(),
        "dividends": pd.Series(dtype=float),
        "actions": pd.DataFrame(),
        "history": pd.DataFrame()
    }
    yfinance_primary_fetch_successful = False
    fyf_used_for_core = False

    # 1. Try yfinance first
    try:
        stock_yf = yf.Ticker(ticker_symbol)
        stock_info_yf = stock_yf.info
        if stock_info_yf and stock_info_yf.get('symbol', '').upper() == ticker_symbol.upper() and \
           any(k in stock_info_yf for k in ['regularMarketPrice', 'currentPrice', 'previousClose', 'longName']):
            data["info"] = stock_info_yf
            for key in ["financials", "balance_sheet", "cash_flow", "major_holders", "dividends", "actions"]:
                try:
                    attr_val = getattr(stock_yf, key)
                    if attr_val is not None and not attr_val.empty: data[key] = attr_val
                except Exception: pass
            hist_data = stock_yf.history(period=f"{YEARS_OF_DATA+1}y")
            if hist_data is not None and not hist_data.empty: data["history"] = hist_data
            if not data["financials"].empty and not data["balance_sheet"].empty: yfinance_primary_fetch_successful = True
        else:
            hist_check = stock_yf.history(period="5d")
            if hist_check.empty and (not stock_info_yf or not stock_info_yf.get('symbol')):
                pass # Suppress error message
            elif not stock_info_yf or not stock_info_yf.get('symbol'):
                data["info"] = stock_info_yf if stock_info_yf else {}
    except Exception as e_yf: pass

    # 2. Fallback to fix-yahoo-finance if yfinance failed for core data
    if not yfinance_primary_fetch_successful and fyf:
        try:
            stock_fyf = fyf.Ticker(ticker_symbol)
            fyf_info = stock_fyf.info
            if isinstance(fyf_info, dict) and fyf_info.get('symbol'): data["info"] = fyf_info
            for key, fyf_attr_name in [("financials", "financials"), ("balance_sheet", "balance_sheet"), ("cash_flow", "cashflow")]:
                if data[key].empty:
                    fyf_df = getattr(stock_fyf, fyf_attr_name, pd.DataFrame())
                    if isinstance(fyf_df, pd.DataFrame) and not fyf_df.empty: data[key] = fyf_df; fyf_used_for_core = True
            if fyf_used_for_core: yfinance_primary_fetch_successful = True
            if data["history"].empty:
                hist_data_fyf = stock_fyf.history(period=f"{YEARS_OF_DATA+1}y")
                if hist_data_fyf is not None and not hist_data_fyf.empty: data["history"] = hist_data_fyf
        except Exception as e_fyf:
            pass

    # 3. Fallback to investiny for missing info fields
    if investiny_available:
        investiny_info_map = {'EPS (TTM)': 'trailingEps', 'Market Cap': 'marketCap', 'P/E Ratio': 'trailingPE',
                              'Dividend (Yield)': 'dividendYield', 'Prev. Close': 'previousClose', 'EBITDA': 'ebitda',
                              'Name': 'longName'} # Added 'Name' to map to 'longName'
        investiny_overview_data_fetched = False
        investiny_overview_data_dict = None
        asset_id = get_investiny_asset_id(ticker_symbol)
        if asset_id:
            for inv_key, yf_key in investiny_info_map.items():
                if data["info"].get(yf_key) is None:
                    if not investiny_overview_data_fetched:
                        try:
                            investiny_overview_data_dict = investiny_overview(asset_id=asset_id)
                            investiny_overview_data_fetched = True
                        except Exception as e_inv_ov:
                            pass; break
                    if investiny_overview_data_dict and investiny_overview_data_dict.get(inv_key):
                        raw_val = investiny_overview_data_dict.get(inv_key)
                        if yf_key == 'dividendYield' and isinstance(raw_val, str) and '(' in raw_val and '%' in raw_val:
                            try: yield_str = raw_val.split('(')[1].split('%')[0]; converted_val = convert_financial_string_to_float(yield_str + '%')
                            except: converted_val = None
                        else: converted_val = convert_financial_string_to_float(raw_val)
                        if converted_val is not None: data["info"][yf_key] = converted_val
            if not data["info"].get('symbol') and investiny_overview_data_dict:
                data["info"]['symbol'] = ticker_symbol
                data["info"]['longName'] = investiny_overview_data_dict.get('name', ticker_symbol)

    # 4. Fallback to finvizfinance for missing info fields
    if finviz_available:
        finviz_map = {'P/E': 'trailingPE', 'EPS (ttm)': 'trailingEps', 'Market Cap': 'marketCap', 'Dividend %': 'dividendYield',
                      'P/S': 'priceToSalesTrailing12Months', 'Insider Own': 'heldPercentInsiders', 'Inst Own': 'heldPercentInstitutions'}
        finviz_data = None
        try:
            stock_finviz = FinvizStock(ticker_symbol)
            finviz_data = stock_finviz.get_stock()
        except Exception as e_finviz:
            pass
        if finviz_data:
            
            for fv_key, yf_key in finviz_map.items():
                if data["info"].get(yf_key) is None and fv_key in finviz_data:
                    converted_val = convert_financial_string_to_float(finviz_data[fv_key])
                    if converted_val is not None: data["info"][yf_key] = converted_val
            if not data["info"].get('sector') and 'Sector' in finviz_data: data["info"]['sector'] = finviz_data['Sector']
            if not data["info"].get('industry') and 'Industry' in finviz_data: data["info"]['industry'] = finviz_data['Industry']

    return data

def fetch_stock_data(ticker_symbol: str) -> Dict[str, Any]:
    # Calculate current timestamp rounded to the nearest CACHE_TTL_SECONDS
    now = datetime.now()
    # Use integer division to get the number of full cache intervals since epoch
    timestamp = int(now.timestamp() // CACHE_TTL_SECONDS) * CACHE_TTL_SECONDS
    return _fetch_stock_data_cached(ticker_symbol, timestamp)
