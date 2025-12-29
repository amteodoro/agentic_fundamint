"""
Earnings Calendar API Router

Provides endpoints for:
- Earnings calendar (daily, weekly, monthly views)
- Individual stock earnings history and upcoming dates
- Earnings details with historical performance
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

# Import earnings functions from fmp_fetcher
from ..fmp_fetcher import (
    fetch_earnings_calendar,
    fetch_earnings_history,
    fetch_stock_earnings_info,
    is_fmp_available,
)


router = APIRouter()


# ====== Pydantic Models ======

class EarningEvent(BaseModel):
    """Single earnings announcement event."""
    symbol: str = Field(..., description="Stock ticker symbol")
    date: str = Field(..., description="Earnings announcement date (YYYY-MM-DD)")
    time: Optional[str] = Field(None, description="Time of announcement (bmo, amc, dmh, unknown)")
    epsEstimate: Optional[float] = Field(None, description="Estimated EPS")
    epsActual: Optional[float] = Field(None, description="Actual reported EPS (if available)")
    revenueEstimate: Optional[float] = Field(None, description="Estimated revenue")
    revenueActual: Optional[float] = Field(None, description="Actual revenue (if available)")
    fiscalDateEnding: Optional[str] = Field(None, description="Fiscal period end date")


class DailyEarnings(BaseModel):
    """Earnings grouped by a single day."""
    date: str = Field(..., description="Date (YYYY-MM-DD)")
    dayOfWeek: str = Field(..., description="Day name (Monday, Tuesday, etc.)")
    earnings: List[EarningEvent] = Field(default_factory=list)
    count: int = Field(0, description="Number of earnings announcements")


class EarningsCalendarResponse(BaseModel):
    """Response for earnings calendar endpoint."""
    startDate: str = Field(..., description="Calendar start date")
    endDate: str = Field(..., description="Calendar end date")
    view: str = Field(..., description="View type (daily, weekly, monthly)")
    days: List[DailyEarnings] = Field(default_factory=list)
    totalEarnings: int = Field(0, description="Total number of earnings in period")


class HistoricalEarning(BaseModel):
    """Single historical earnings report."""
    date: str = Field(..., description="Earnings report date")
    symbol: str = Field(..., description="Stock ticker")
    epsActual: Optional[float] = Field(None, description="Actual EPS reported")
    epsEstimate: Optional[float] = Field(None, description="EPS estimate")
    epsSurprise: Optional[float] = Field(None, description="EPS surprise (actual - estimate)")
    epsSurprisePercent: Optional[float] = Field(None, description="EPS surprise percentage")
    revenue: Optional[float] = Field(None, description="Actual revenue")
    revenueEstimate: Optional[float] = Field(None, description="Estimated revenue")
    fiscalDateEnding: Optional[str] = Field(None, description="Fiscal period end")


class EarningsStats(BaseModel):
    """Statistics about historical earnings performance."""
    totalReported: int = Field(0, description="Total number of earnings reports")
    beats: int = Field(0, description="Number of times beat estimates")
    misses: int = Field(0, description="Number of times missed estimates")
    meets: int = Field(0, description="Number of times met estimates")
    beatRate: Optional[float] = Field(None, description="Percentage of beats")


class StockEarningsResponse(BaseModel):
    """Complete earnings info for a single stock."""
    symbol: str = Field(..., description="Stock ticker")
    nextEarningsDate: Optional[str] = Field(None, description="Next earnings date")
    nextEarningsTime: Optional[str] = Field(None, description="Time of next earnings (bmo/amc)")
    epsEstimate: Optional[float] = Field(None, description="Next EPS estimate")
    revenueEstimate: Optional[float] = Field(None, description="Next revenue estimate")
    history: List[HistoricalEarning] = Field(default_factory=list)
    stats: EarningsStats = Field(default_factory=EarningsStats)


class BulkEarningsRequest(BaseModel):
    """Request for earnings dates of multiple stocks."""
    tickers: List[str] = Field(..., description="List of stock tickers")


class BulkEarningsItem(BaseModel):
    """Earnings date info for a single stock."""
    symbol: str
    nextEarningsDate: Optional[str] = None
    nextEarningsTime: Optional[str] = None
    daysUntilEarnings: Optional[int] = None


class BulkEarningsResponse(BaseModel):
    """Response for bulk earnings dates."""
    earnings: List[BulkEarningsItem] = Field(default_factory=list)


# ====== Helper Functions ======

def get_day_of_week(date_str: str) -> str:
    """Get day of week name from date string."""
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")
        return date.strftime("%A")
    except:
        return "Unknown"


def organize_earnings_by_day(earnings: List[Dict], start_date: str, end_date: str) -> List[DailyEarnings]:
    """Organize earnings events by day."""
    # Create a dict to group earnings by date
    earnings_by_date: Dict[str, List[EarningEvent]] = {}
    
    for earning in earnings:
        date = earning.get("date")
        if date:
            if date not in earnings_by_date:
                earnings_by_date[date] = []
            earnings_by_date[date].append(EarningEvent(**earning))
    
    # Generate all dates in range and create DailyEarnings objects
    days = []
    current = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    
    while current <= end:
        date_str = current.strftime("%Y-%m-%d")
        day_earnings = earnings_by_date.get(date_str, [])
        
        days.append(DailyEarnings(
            date=date_str,
            dayOfWeek=current.strftime("%A"),
            earnings=day_earnings,
            count=len(day_earnings)
        ))
        current += timedelta(days=1)
    
    return days


# ====== API Endpoints ======

@router.get("/earnings/calendar", response_model=EarningsCalendarResponse)
async def get_earnings_calendar(
    view: str = Query("weekly", description="View type: daily, weekly, monthly"),
    from_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    to_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
):
    """
    Get earnings calendar for a specified period.
    
    Views:
    - daily: Returns next 7 days
    - weekly: Returns current week and next week (14 days)
    - monthly: Returns next 30 days
    """
    if not is_fmp_available():
        raise HTTPException(
            status_code=503,
            detail="Earnings calendar not available. Please configure FMP_API_KEY."
        )
    
    today = datetime.now()
    
    # Determine date range based on view
    if from_date and to_date:
        start = from_date
        end = to_date
    elif view == "daily":
        start = today.strftime("%Y-%m-%d")
        end = (today + timedelta(days=7)).strftime("%Y-%m-%d")
    elif view == "monthly":
        start = today.strftime("%Y-%m-%d")
        end = (today + timedelta(days=30)).strftime("%Y-%m-%d")
    else:  # weekly (default)
        # Start from beginning of current week (Monday)
        days_since_monday = today.weekday()
        week_start = today - timedelta(days=days_since_monday)
        start = week_start.strftime("%Y-%m-%d")
        end = (week_start + timedelta(days=13)).strftime("%Y-%m-%d")  # 2 weeks
    
    try:
        # Fetch earnings from FMP
        earnings = fetch_earnings_calendar(start, end)
        
        # Organize by day
        days = organize_earnings_by_day(earnings, start, end)
        
        return EarningsCalendarResponse(
            startDate=start,
            endDate=end,
            view=view,
            days=days,
            totalEarnings=len(earnings)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching earnings calendar: {str(e)}")


@router.get("/earnings/{ticker}", response_model=StockEarningsResponse)
async def get_stock_earnings(ticker: str):
    """
    Get complete earnings information for a specific stock.
    
    Includes:
    - Next earnings date and time
    - EPS and revenue estimates
    - Historical earnings with beat/miss analysis
    - Overall earnings performance statistics
    """
    if not is_fmp_available():
        raise HTTPException(
            status_code=503,
            detail="Earnings data not available. Please configure FMP_API_KEY."
        )
    
    try:
        earnings_info = fetch_stock_earnings_info(ticker)
        
        if not earnings_info:
            raise HTTPException(status_code=404, detail=f"No earnings data found for {ticker}")
        
        # Convert history to HistoricalEarning models
        history = [HistoricalEarning(**h) for h in earnings_info.get("history", [])]
        
        # Create stats model
        stats_data = earnings_info.get("stats", {})
        stats = EarningsStats(
            totalReported=stats_data.get("totalReported", 0),
            beats=stats_data.get("beats", 0),
            misses=stats_data.get("misses", 0),
            meets=stats_data.get("meets", 0),
            beatRate=stats_data.get("beatRate"),
        )
        
        return StockEarningsResponse(
            symbol=earnings_info.get("symbol", ticker.upper()),
            nextEarningsDate=earnings_info.get("nextEarningsDate"),
            nextEarningsTime=earnings_info.get("nextEarningsTime"),
            epsEstimate=earnings_info.get("epsEstimate"),
            revenueEstimate=earnings_info.get("revenueEstimate"),
            history=history,
            stats=stats,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching earnings for {ticker}: {str(e)}")


@router.get("/earnings/{ticker}/history")
async def get_earnings_history(
    ticker: str,
    limit: int = Query(20, ge=1, le=50, description="Number of historical records")
):
    """
    Get historical earnings for a specific stock.
    """
    if not is_fmp_available():
        raise HTTPException(
            status_code=503,
            detail="Earnings data not available. Please configure FMP_API_KEY."
        )
    
    try:
        history = fetch_earnings_history(ticker, limit)
        return {"ticker": ticker.upper(), "history": history, "count": len(history)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching earnings history: {str(e)}")


@router.post("/earnings/bulk", response_model=BulkEarningsResponse)
async def get_bulk_earnings_dates(request: BulkEarningsRequest):
    """
    Get next earnings dates for multiple stocks at once.
    Useful for portfolio/watchlist views.
    """
    if not is_fmp_available():
        raise HTTPException(
            status_code=503,
            detail="Earnings data not available. Please configure FMP_API_KEY."
        )
    
    if len(request.tickers) > 50:
        raise HTTPException(
            status_code=400,
            detail="Maximum 50 tickers allowed per request"
        )
    
    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")
    future_str = (today + timedelta(days=120)).strftime("%Y-%m-%d")
    
    try:
        # Fetch calendar for the range
        calendar = fetch_earnings_calendar(today_str, future_str)
        
        # Create lookup by symbol
        earnings_by_symbol: Dict[str, Dict] = {}
        for earning in calendar:
            symbol = earning.get("symbol", "").upper()
            if symbol and symbol not in earnings_by_symbol:
                earnings_by_symbol[symbol] = earning
        
        # Build response
        results = []
        for ticker in request.tickers:
            ticker_upper = ticker.upper()
            earning_data = earnings_by_symbol.get(ticker_upper)
            
            days_until = None
            if earning_data and earning_data.get("date"):
                try:
                    earnings_date = datetime.strptime(earning_data["date"], "%Y-%m-%d")
                    days_until = (earnings_date - today).days
                except:
                    pass
            
            results.append(BulkEarningsItem(
                symbol=ticker_upper,
                nextEarningsDate=earning_data.get("date") if earning_data else None,
                nextEarningsTime=earning_data.get("time") if earning_data else None,
                daysUntilEarnings=days_until,
            ))
        
        return BulkEarningsResponse(earnings=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching bulk earnings: {str(e)}")
