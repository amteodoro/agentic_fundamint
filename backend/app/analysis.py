import pandas as pd
import numpy as np

def clean_data(data):
    if isinstance(data, dict):
        return {k: clean_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_data(i) for i in data]
    elif isinstance(data, float) and (np.isnan(data) or np.isinf(data)):
        return None
    return data

# --- Configuration ---
YEARS_OF_DATA = 10
YEARS_FOR_TREND_ANALYSIS = 5
YEARS_TO_PROJECT = 10
MIN_ACCEPTABLE_RETURN = 0.15
DEFAULT_TAX_RATE = 0.21
GROWTH_RATE_CAP = 0.15
FUTURE_PE_CAP = 30.0

# --- Helper Functions ---
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

def calculate_cagr(series, years_to_consider=YEARS_OF_DATA):
    if not isinstance(series, pd.Series) or series.empty: return None
    series_numeric = pd.to_numeric(series, errors='coerce').dropna().sort_index()
    if len(series_numeric) < 2: return None
    series_recent = series_numeric.tail(years_to_consider + 1)
    if len(series_recent) < 2: series_recent = series_numeric
    if len(series_recent) < 2: return None
    start_value, end_value = series_recent.iloc[0], series_recent.iloc[-1]
    num_periods = len(series_recent) - 1
    if start_value == 0 or start_value is None or end_value is None or num_periods == 0: return None
    if (end_value > 0 and start_value < 0) or (end_value < 0 and start_value > 0): return None
    if start_value < 0 and end_value >=0: return None
    return ((end_value / start_value) ** (1 / num_periods)) - 1

# --- Phil Town Strategy Functions ---
def calculate_roic_phil_town(financials, balance_sheet, years_to_consider=YEARS_OF_DATA):
    
    roics = []
    if financials.empty or balance_sheet.empty: return clean_data((None, []))
    common_years = financials.columns.intersection(balance_sheet.columns)
    sorted_common_years = sorted(common_years, reverse=True)[:years_to_consider]
    for year_col in sorted_common_years:
        year_financials, year_balance_sheet = financials[year_col], balance_sheet[year_col]
        ebit = get_safe_value(year_financials, 'EBIT', is_column_data=True)
        if ebit is None:
            net_income = get_safe_value(year_financials, 'Net Income', is_column_data=True)
            interest_expense = get_safe_value(year_financials, 'Interest Expense', is_column_data=True)
            tax_provision = get_safe_value(year_financials, 'Tax Provision', is_column_data=True)
            if all(v is not None for v in [net_income, interest_expense, tax_provision]):
                ebit = net_income + interest_expense + tax_provision
            else: ebit = get_safe_value(year_financials, 'Operating Income', is_column_data=True)
        if ebit is None: continue
        income_before_tax = get_safe_value(year_financials, 'Pretax Income', is_column_data=True)
        tax_provision = get_safe_value(year_financials, 'Tax Provision', is_column_data=True)
        tax_rate = DEFAULT_TAX_RATE
        if income_before_tax and tax_provision and income_before_tax != 0:
            current_tax_rate = tax_provision / income_before_tax
            if 0 <= current_tax_rate <= 0.60: tax_rate = current_tax_rate
        nopat = ebit * (1 - tax_rate)
        total_equity = get_safe_value(year_balance_sheet, 'Stockholders Equity', is_column_data=True)
        long_term_debt = get_safe_value(year_balance_sheet, 'Long Term Debt', is_column_data=True)
        if long_term_debt is None:
            total_debt = get_safe_value(year_balance_sheet, 'Total Debt', is_column_data=True)
            current_debt = get_safe_value(year_balance_sheet, 'Current Debt', is_column_data=True)
            if total_debt is not None and current_debt is not None: long_term_debt = total_debt - current_debt
            elif total_debt is not None: long_term_debt = total_debt
            else: long_term_debt = 0
        if total_equity is None: continue
        invested_capital = total_equity + (long_term_debt if long_term_debt is not None else 0)
        if invested_capital and invested_capital != 0: roics.append(nopat / invested_capital)
        else: roics.append(None)
    valid_roics = [r for r in roics if r is not None and isinstance(r, (int, float)) and not np.isnan(r) and not np.isinf(r)]
    
    return clean_data((sum(valid_roics) / len(valid_roics)) if valid_roics else None), clean_data(valid_roics)

def get_growth_rates_phil_town(stock_data, years_to_consider=YEARS_OF_DATA):
    
    financials, balance_sheet, cash_flow = stock_data["financials"], stock_data["balance_sheet"], stock_data["cash_flow"]
    
    growth_rates = {}
    eps_series = None
    if not financials.empty:
        if 'Diluted EPS' in financials.index: eps_series = get_safe_value(financials, 'Diluted EPS', is_column_data=False)
        elif 'Basic EPS' in financials.index: eps_series = get_safe_value(financials, 'Basic EPS', is_column_data=False)
    growth_rates['eps_cagr'] = calculate_cagr(eps_series, years_to_consider)
    bvps_series = None
    if not balance_sheet.empty and not financials.empty:
        equity = get_safe_value(balance_sheet, 'Stockholders Equity', is_column_data=False)
        shares = None
        if 'Diluted Average Shares' in financials.index: shares = get_safe_value(financials, 'Diluted Average Shares', is_column_data=False)
        elif 'Basic Average Shares' in financials.index: shares = get_safe_value(financials, 'Basic Average Shares', is_column_data=False)
        if isinstance(equity, pd.Series) and isinstance(shares, pd.Series):
            aligned_equity, aligned_shares = equity.align(shares, join='inner')
            if not aligned_equity.empty and not aligned_shares.empty:
                bvps_values = {yr: aligned_equity[yr] / aligned_shares[yr] for yr in aligned_equity.index if pd.notna(aligned_equity[yr]) and pd.notna(aligned_shares[yr]) and aligned_shares[yr] != 0}
                if bvps_values: bvps_series = pd.Series(bvps_values)
    growth_rates['bvps_cagr'] = calculate_cagr(bvps_series, years_to_consider)
    revenue_series = get_safe_value(financials, 'Total Revenue', is_column_data=False)
    growth_rates['sales_cagr'] = calculate_cagr(revenue_series, years_to_consider)
    fcf_series = None
    if not cash_flow.empty:
        op_cash = get_safe_value(cash_flow, 'Operating Cash Flow', is_column_data=False)
        cap_ex = get_safe_value(cash_flow, 'Capital Expenditure', is_column_data=False)
        if isinstance(op_cash, pd.Series) and isinstance(cap_ex, pd.Series):
            aligned_op, aligned_ce = op_cash.align(cap_ex, join='inner')
            if not aligned_op.empty and not aligned_ce.empty:
                fcf_values = {yr: aligned_op[yr] + aligned_ce[yr] for yr in aligned_op.index if pd.notna(aligned_op[yr]) and pd.notna(aligned_ce[yr])}
                if fcf_values: fcf_series = pd.Series(fcf_values)
    growth_rates['fcf_cagr'] = calculate_cagr(fcf_series, years_to_consider)
    
    return clean_data(growth_rates)

def calculate_management_metrics_phil_town(stock_data):
    
    balance_sheet, cash_flow, info = stock_data["balance_sheet"], stock_data["cash_flow"], stock_data["info"]
    
    metrics = {}
    long_term_debt = None
    if not balance_sheet.empty:
        latest_year_bs_data = balance_sheet.iloc[:, 0]
        
        long_term_debt = get_safe_value(latest_year_bs_data, 'Long Term Debt', is_column_data=True)
        if long_term_debt is None:
            total_debt = get_safe_value(latest_year_bs_data, 'Total Debt', is_column_data=True)
            current_debt = get_safe_value(latest_year_bs_data, 'Current Debt', is_column_data=True)
            if total_debt is not None and current_debt is not None: long_term_debt = total_debt - current_debt
            elif total_debt is not None: long_term_debt = total_debt
            else: long_term_debt = 0
    
    fcf_most_recent = None
    if not cash_flow.empty:
        latest_year_cf_data = cash_flow.iloc[:, 0]
        
        op_cash = get_safe_value(latest_year_cf_data, 'Operating Cash Flow', is_column_data=True)
        cap_ex = get_safe_value(latest_year_cf_data, 'Capital Expenditure', is_column_data=True)
        if op_cash is not None and cap_ex is not None: fcf_most_recent = op_cash + cap_ex
    
    metrics['debt_payoff_years'] = long_term_debt / fcf_most_recent if long_term_debt is not None and fcf_most_recent is not None and fcf_most_recent > 0 else None
    metrics['insider_ownership'] = get_safe_value(info, 'heldPercentInsiders')
    
    return clean_data(metrics)

def calculate_margin_of_safety_phil_town(stock_data, growth_rates_pt):
    
    info = stock_data["info"]
    mos_data = {}
    current_eps = get_safe_value(info, 'trailingEps')
    
    if current_eps is None or current_eps <= 0:
        mos_data['error'] = "Current EPS is not positive or unavailable, MOS calculation not suitable for Phil Town strategy."
        return clean_data(mos_data)
    mos_data['current_eps'] = current_eps
    historical_eps_growth, analyst_eps_estimate = growth_rates_pt.get('eps_cagr'), get_safe_value(info, 'earningsGrowth')
    
    valid_growth_rates = [g for g in [historical_eps_growth, analyst_eps_estimate] if isinstance(g, (int, float))]
    if not valid_growth_rates:
        mos_data['error'] = "Could not determine a reliable EPS growth rate for Phil Town MOS."
        return clean_data(mos_data)
    estimated_growth_rate = min(valid_growth_rates) if len(valid_growth_rates) > 1 else valid_growth_rates[0]
    projected_eps_growth_rate = min(estimated_growth_rate, GROWTH_RATE_CAP)
    if projected_eps_growth_rate < 0: projected_eps_growth_rate = 0.0
    mos_data['projected_eps_growth_rate'] = projected_eps_growth_rate
    future_eps = current_eps * ((1 + projected_eps_growth_rate) ** YEARS_TO_PROJECT)
    mos_data['future_eps'] = future_eps
    pe_from_growth, current_trailing_pe = 2 * (projected_eps_growth_rate * 100), get_safe_value(info, 'trailingPE')
    future_pe_options = [pe_from_growth]
    if isinstance(current_trailing_pe, (int, float)) and current_trailing_pe > 0: future_pe_options.append(current_trailing_pe)
    future_pe = min(future_pe_options) if future_pe_options else FUTURE_PE_CAP
    future_pe = min(future_pe, FUTURE_PE_CAP)
    if future_pe <= 0:
        default_pe = get_safe_value(info, 'forwardPE')
        future_pe = default_pe if isinstance(default_pe, (int, float)) and default_pe > 0 else 15.0
    mos_data['future_pe_ratio'] = future_pe
    sticker_price = (future_eps * future_pe) / ((1 + MIN_ACCEPTABLE_RETURN) ** YEARS_TO_PROJECT)
    mos_data['sticker_price'] = sticker_price
    mos_data['mos_price'] = sticker_price * 0.5
    current_price_options = [get_safe_value(info, k) for k in ['regularMarketPrice', 'currentPrice', 'previousClose']]
    mos_data['current_market_price'] = next((p for p in current_price_options if isinstance(p, (int, float))), None)
    
    return clean_data(mos_data)

# --- High-Growth Strategy Functions ---
def calculate_net_margins(financials_df, years_to_consider=YEARS_FOR_TREND_ANALYSIS):
    print(f"[Analysis] calculate_net_margins: financials_df empty: {financials_df.empty}")
    net_income_series, total_revenue_series = None, None
    if not financials_df.empty:
        net_income_series = get_safe_value(financials_df, 'Net Income', is_column_data=False)
        total_revenue_series = get_safe_value(financials_df, 'Total Revenue', is_column_data=False)
    print(f"[Analysis] calculate_net_margins: net_income_series empty: {net_income_series.empty if isinstance(net_income_series, pd.Series) else 'N/A'}, total_revenue_series empty: {total_revenue_series.empty if isinstance(total_revenue_series, pd.Series) else 'N/A'}")
    if not isinstance(net_income_series, pd.Series) or not isinstance(total_revenue_series, pd.Series) or net_income_series.empty or total_revenue_series.empty: return [], "N/A"
    net_income_series_num, total_revenue_series_num = pd.to_numeric(net_income_series, 'coerce'), pd.to_numeric(total_revenue_series, 'coerce')
    aligned_ni, aligned_rev = net_income_series_num.align(total_revenue_series_num, join='inner')
    valid_mask = (aligned_rev != 0) & pd.notna(aligned_rev) & pd.notna(aligned_ni)
    aligned_ni, aligned_rev = aligned_ni[valid_mask], aligned_rev[valid_mask]
    if aligned_rev.empty: return [], "N/A"
    net_margins_series = (aligned_ni / aligned_rev).sort_index(ascending=False)
    recent_net_margins = net_margins_series.head(years_to_consider).iloc[::-1]
    print(f"[Analysis] calculate_net_margins: recent_net_margins: {recent_net_margins.tolist()}")
    trend = "Not enough data for trend"
    if len(recent_net_margins) >= 2:
        first_margin, last_margin = recent_net_margins.iloc[0], recent_net_margins.iloc[-1]
        if isinstance(first_margin, (int,float)) and isinstance(last_margin, (int,float)):
            if last_margin > first_margin: trend = "Expanding"
            elif last_margin < first_margin: trend = "Contracting"
            else: trend = "Stable"
        else: trend = "Trend undetermined (non-numeric margins)"
    print(f"[Analysis] calculate_net_margins: trend: {trend}")
    return recent_net_margins.tolist(), trend

def analyze_high_growth_quality_strategy(stock_data, avg_roic_from_pt):
    print(f"[Analysis] analyze_high_growth_quality_strategy: stock_data keys: {stock_data.keys()}, avg_roic_from_pt: {avg_roic_from_pt}")
    info, financials, balance_sheet = stock_data["info"], stock_data["financials"], stock_data["balance_sheet"]
    print(f"[Analysis] analyze_high_growth_quality_strategy: info present: {bool(info)}, financials empty: {financials.empty}, balance_sheet empty: {balance_sheet.empty}")
    analysis = {}
    sales_series_hg = get_safe_value(financials, 'Total Revenue', is_column_data=False)
    print(f"[Analysis] analyze_high_growth_quality_strategy: sales_series_hg empty: {sales_series_hg.empty if isinstance(sales_series_hg, pd.Series) else 'N/A'}")
    analysis['sales_cagr_hg'] = calculate_cagr(sales_series_hg, YEARS_FOR_TREND_ANALYSIS)
    net_margins_list, net_margin_trend = calculate_net_margins(financials, YEARS_FOR_TREND_ANALYSIS)
    analysis.update({'net_margins_historical': net_margins_list, 'net_margin_trend': net_margin_trend,
                     'current_net_margin': net_margins_list[-1] if net_margins_list and isinstance(net_margins_list[-1], (int,float)) else None})
    analysis.update({k: get_safe_value(info, v) for k, v in {'current_psr': 'priceToSalesTrailing12Months', 'current_per': 'trailingPE',
                     'market_cap': 'marketCap', 'shares_outstanding': 'sharesOutstanding', 'ev_to_ebitda': 'enterpriseToEbitda'}.items()})
    net_debt = None
    if not balance_sheet.empty:
        latest_bs_col = balance_sheet.iloc[:, 0]
        total_debt, cash_equivalents = get_safe_value(latest_bs_col, 'Total Debt', True), get_safe_value(latest_bs_col, 'Cash And Cash Equivalents', True)
        if isinstance(total_debt, (int,float)) and isinstance(cash_equivalents, (int,float)): net_debt = total_debt - cash_equivalents
    analysis['net_debt'] = net_debt
    ebitda = get_safe_value(info, 'ebitda')
    analysis['net_debt_to_ebitda'] = net_debt / ebitda if isinstance(net_debt,(int,float)) and isinstance(ebitda,(int,float)) and ebitda != 0 else None
    latest_roe = None
    if not balance_sheet.empty:
        net_income_series_for_roe = get_safe_value(financials, 'Net Income', is_column_data=False)
        if isinstance(net_income_series_for_roe, pd.Series) and not net_income_series_for_roe.empty:
            numeric_ni_series = pd.to_numeric(net_income_series_for_roe, errors='coerce').dropna()
            net_income_latest_val = numeric_ni_series.iloc[-1] if not numeric_ni_series.empty else None
            equity_latest = get_safe_value(balance_sheet.iloc[:,0], 'Stockholders Equity', True)
            if isinstance(net_income_latest_val,(int,float)) and isinstance(equity_latest,(int,float)) and equity_latest != 0:
                latest_roe = net_income_latest_val / equity_latest
    analysis.update({'latest_roe': latest_roe, 'avg_roic': avg_roic_from_pt, 'insider_ownership_hg': get_safe_value(info, 'heldPercentInsiders')})
    div_yield = get_safe_value(info, 'dividendYield')
    analysis['dividend_yield'] = div_yield
    analysis['pays_dividends'] = bool(stock_data.get('dividends') is not None and not stock_data['dividends'].empty and isinstance(div_yield, float) and div_yield > 0)
    print(f"[Analysis] analyze_high_growth_quality_strategy: calculated analysis: {analysis}")
    return clean_data(analysis)
