from fastapi import APIRouter, HTTPException
import yfinance as yf
from pydantic import BaseModel
from typing import Optional, List, Dict

from .. import analysis

router = APIRouter()

class PhilTownAnalysis(BaseModel):
    moat: Dict
    management: Dict
    mos: Dict
    growth_rates: Dict

@router.get("/analysis/{ticker}/phil-town", response_model=PhilTownAnalysis)
async def get_phil_town_analysis(ticker: str):
    stock = yf.Ticker(ticker)
    if not stock.info or stock.info.get('longName') is None:
        print(f"[Backend] Ticker {ticker} not found for Phil Town analysis.")
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found.")

    financials = stock.financials
    balance_sheet = stock.balance_sheet
    cash_flow = stock.cashflow

    print(f"[Backend] Fetching data for Phil Town analysis for {ticker}...")
    stock_data = {
        "info": stock.info,
        "financials": financials,
        "balance_sheet": balance_sheet,
        "cash_flow": cash_flow
    }

    try:
        avg_roic, roic_annual = analysis.calculate_roic_phil_town(financials, balance_sheet)
        print(f"[Backend] ROIC calculated: {avg_roic}")
        growth_rates = analysis.get_growth_rates_phil_town(stock_data)
        print(f"[Backend] Growth rates calculated: {growth_rates}")
        management_metrics = analysis.calculate_management_metrics_phil_town(stock_data)
        print(f"[Backend] Management metrics calculated: {management_metrics}")
        mos_data = analysis.calculate_margin_of_safety_phil_town(stock_data, growth_rates)
        print(f"[Backend] MOS data calculated: {mos_data}")

        return {
            "moat": {"avg_roic": avg_roic, "roic_annual": roic_annual},
            "management": management_metrics,
            "mos": mos_data,
            "growth_rates": growth_rates
        }
    except Exception as e:
        print(f"[Backend] Error during Phil Town analysis for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class HighGrowthAnalysis(BaseModel):
    sales_cagr_hg: Optional[float]
    net_margins_historical: List[float]
    net_margin_trend: str
    current_net_margin: Optional[float]
    current_psr: Optional[float]
    current_per: Optional[float]
    market_cap: Optional[float]
    shares_outstanding: Optional[float]
    ev_to_ebitda: Optional[float]
    net_debt: Optional[float]
    net_debt_to_ebitda: Optional[float]
    latest_roe: Optional[float]
    avg_roic: Optional[float]
    insider_ownership_hg: Optional[float]
    dividend_yield: Optional[float]
    pays_dividends: bool

@router.get("/analysis/{ticker}/high-growth", response_model=HighGrowthAnalysis)
async def get_high_growth_analysis(ticker: str):
    stock = yf.Ticker(ticker)
    if not stock.info or stock.info.get('longName') is None:
        print(f"[Backend] Ticker {ticker} not found for High-Growth analysis.")
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found.")

    financials = stock.financials
    balance_sheet = stock.balance_sheet
    cash_flow = stock.cashflow
    dividends = stock.dividends

    print(f"[Backend] Fetching data for High-Growth analysis for {ticker}...")
    stock_data = {
        "info": stock.info,
        "financials": financials,
        "balance_sheet": balance_sheet,
        "cash_flow": cash_flow,
        "dividends": dividends
    }

    try:
        avg_roic, _ = analysis.calculate_roic_phil_town(financials, balance_sheet)
        print(f"[Backend] Avg ROIC for High-Growth analysis: {avg_roic}")
        hg_analysis = analysis.analyze_high_growth_quality_strategy(stock_data, avg_roic)
        print(f"[Backend] High-Growth analysis results: {hg_analysis}")

        return hg_analysis
    except Exception as e:
        print(f"[Backend] Error during High-Growth analysis for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
