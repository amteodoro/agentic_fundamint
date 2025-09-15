from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

router = APIRouter()

CRITERIA_DATA = [
  {
    "criteria_name": "Sales Growth",
    "interpretation": "Annual sales growth rate, indicating market share gain and business expansion. Significant stock appreciation is difficult without sales growth.",
    "ranges": {
      "good": "> 15% p.a. (preferably > 20% p.a.)",
      "neutral": "5% - 15% p.a. (faster than GDP/inflation)",
      "warning": "< 5% p.a., stagnant, or decreasing"
    },
  },
  {
    "criteria_name": "Net Margin",
    "interpretation": "Profit earned per unit of sale (Net Income / Sales), reflecting profitability. Companies with low net margins (e.g., 1-2%) often operate in highly competitive industries or have many employees.",
    "ranges": {
      "good": "> 10% (for software/low fixed costs: > 20%)",
      "neutral": "5% - 10%",
      "warning": "< 5% or negative"
    },
  },
  {
    "criteria_name": "EV/EBITDA",
    "interpretation": "Enterprise Value / Earnings Before Interest, Taxes, Depreciation, and Amortization. A measure of the company's cost relative to its operational cash flow. EBITDA is a proxy for operational cash flow.",
    "ranges": {
      "good": "< 5 (considered cheap/undervalued)",
      "neutral": "5 - 20 (around 10 is typical)",
      "warning": "> 20 (considered high/expensive/overvalued)"
    },
  },
  {
    "criteria_name": "Net Debt / EBITDA",
    "interpretation": "Net Debt (Financial Debt minus Cash & Equivalents) relative to EBITDA, indicating the company's ability to honor its debt. It is crucial to pay debt on time.",
    "ranges": {
      "good": "Net Cash Positive (more cash than debt) or < 3",
      "neutral": "0 - 3",
      "warning": "Significantly > 3 (a warning sign of potential struggle with debt obligations)"
    },
  },
  {
    "criteria_name": "ROE",
    "interpretation": "How effectively a company reinvests capital to generate high returns, supporting future growth. An ROIC > 15% is also positive.",
    "ranges": { "good": "> 20% (a strong indicator of quality)", "neutral": "15% - 20% (derived from ROIC > 15% also being positive)", "warning": "< 15%" }
  },
  {
    "criteria_name": "PER",
    "interpretation": "Market Value / Net Income. A popular valuation ratio indicating how many times its annual profit the market values the company at. PER should be considered with Earnings Per Share (EPS) growth, as rapid EPS growth and optimistic prospects can justify a higher PER.",
    "ranges": { "good": "< 10 (considered low/undervalued)", "neutral": "10 - 20 (20 is typical)", "warning": "> 20 (considered high/overvalued, especially if EPS growth is not high; can go up to 30-40)" }
  },
  {
    "criteria_name": "PSR",
    "interpretation": "Market Value / Annual Sales. Reflects how highly the market values the company relative to its total sales. Generally, a PSR above 10 suggests potential overvaluation.",
    "ranges": { "good": "< 1", "neutral": "1 - 10", "warning": "> 10 (often suggests potential overvaluation)" }
  },
  {
    "criteria_name": "Insider Ownership",
    "interpretation": "Alignment of management or major shareholder interests with minority investors. A fragmented ownership where no dominant shareholder exists can lead to management prioritizing personal bonuses over long-term company health/shareholder interests.",
    "ranges": { "good": "**Significant main shareholder** (e.g., founder/family) with a relevant percentage, whose wealth depends on the stock's value, aligning interests.", "neutral": None, "warning": "Fragmented ownership where no dominant shareholder exists, potentially leading to management prioritizing personal bonuses over long-term company health/shareholder interests." }
  },
  {
    "criteria_name": "Dividends",
    "interpretation": "Distribution of a portion of profits to shareholders. This indicates a profitable, stable, predictable, and growing business with a healthy balance sheet.",
    "ranges": { "good": "**Consistently pays dividends** (annually, semiannually, or quarterly), indicating a profitable, stable, predictable, and growing business with a healthy balance sheet.", "neutral": None, "warning": "Inconsistent or no dividend payments, potentially indicating less quality or that the company needs to retain capital." }
  },
  {
    "criteria_name": "Share Buybacks",
    "interpretation": "Company's practice of using its resources to buy its own shares. This creates demand for the stock and indicates the company views its shares as a valuable, potentially undervalued asset. A company that only issues new shares and never buys back its own implies it doesn't value its stock highly and may dilute existing shareholders.",
    "ranges": { "good": "**Consistently buying back shares**, indicating the company views its stock as a valuable, potentially undervalued asset and creates demand.", "neutral": None, "warning": "Never buys back shares and only issues new ones, implying the company does not value its own stock highly or dilutes existing shareholders." }
  }
]

class CriteriaItem(BaseModel):
    criteria_name: str
    interpretation: str
    ranges: Dict[str, Optional[str]]

@router.get("/criteria", response_model=List[CriteriaItem])
async def get_criteria():
    return CRITERIA_DATA
