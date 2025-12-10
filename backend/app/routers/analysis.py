from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from app.dependencies import get_agent_dependencies, AgentDependencies
from app.financial_agent.schemas.tool_schemas import MetricComputationOutput

router = APIRouter()

@router.get("/analysis/{ticker}/phil-town", response_model=MetricComputationOutput)
async def get_phil_town_analysis(
    ticker: str,
    enable_web_search: bool = True,
    agent_deps: AgentDependencies = Depends(get_agent_dependencies)
):
    tool = agent_deps.tools_map.get("phil_town_analysis_complete")
    if not tool:
        raise HTTPException(status_code=500, detail="Phil Town Analysis tool not found")
    
    try:
        # The tool expects a dictionary input matching MetricComputationInput
        result = await tool.ainvoke({
            "ticker": ticker,
            "strategy": "phil_town",
            "enable_web_search": enable_web_search
        })
        
        return result
    except Exception as e:
        print(f"[Backend] Error during Phil Town analysis for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/{ticker}/high-growth", response_model=MetricComputationOutput)
async def get_high_growth_analysis(
    ticker: str,
    enable_web_search: bool = True,
    agent_deps: AgentDependencies = Depends(get_agent_dependencies)
):
    tool = agent_deps.tools_map.get("high_growth_analysis_complete")
    if not tool:
        raise HTTPException(status_code=500, detail="High Growth Analysis tool not found")
    
    try:
        result = await tool.ainvoke({
            "ticker": ticker,
            "strategy": "high_growth",
            "enable_web_search": enable_web_search
        })
        
        return result
    except Exception as e:
        print(f"[Backend] Error during High-Growth analysis for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/{ticker}/competitors")
async def get_competitor_analysis(
    ticker: str,
    agent_deps: AgentDependencies = Depends(get_agent_dependencies)
):
    tool = agent_deps.tools_map.get("competitor_analysis")
    if not tool:
        raise HTTPException(status_code=500, detail="Competitor Analysis tool not found")
    
    try:
        # The tool expects a string input or a dictionary depending on implementation
        # BaseTool.ainvoke usually handles dicts best if arguments are named
        result = await tool.ainvoke({
            "ticker": ticker
        })
        
        return result
    except Exception as e:
        print(f"[Backend] Error during Competitor analysis for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/{ticker}/deep-dive")
async def get_deep_dive_analysis(
    ticker: str,
    agent_deps: AgentDependencies = Depends(get_agent_dependencies)
):
    tool = agent_deps.tools_map.get("deep_dive_analysis")
    if not tool:
        raise HTTPException(status_code=500, detail="Deep Dive Analysis tool not found")
    
    try:
        result = await tool.ainvoke({
            "ticker": ticker
        })
        
        return result
    except Exception as e:
        print(f"[Backend] Error during Deep Dive analysis for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/{ticker}/price-projection")
async def get_price_projection_analysis(
    ticker: str,
    agent_deps: AgentDependencies = Depends(get_agent_dependencies)
):
    """
    Get price projection data with configurable defaults for the 4-variable model:
    - Revenue Growth Rate
    - Net Profit Margin
    - Target P/E Ratio
    - Share Count Change
    """
    tool = agent_deps.tools_map.get("price_projection_analysis")
    if not tool:
        raise HTTPException(status_code=500, detail="Price Projection tool not found")
    
    try:
        result = await tool.ainvoke({
            "ticker": ticker
        })
        
        return result
    except Exception as e:
        print(f"[Backend] Error during Price Projection analysis for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

