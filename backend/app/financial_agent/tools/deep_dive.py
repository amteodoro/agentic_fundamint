from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
import yfinance as yf
import logging
import asyncio

logger = logging.getLogger(__name__)

class DeepDiveAnalysisInput(BaseModel):
    ticker: str = Field(description="The ticker symbol of the company to analyze")

class DeepDiveAnalysisTool(BaseTool):
    name: str = "deep_dive_analysis"
    description: str = "Performs a deep qualitative and quantitative analysis answering 15 key investment questions."
    llm: Any = Field(exclude=True)
    search_tool: Optional[BaseTool] = Field(default=None, exclude=True)

    def __init__(self, llm, search_tool=None, **kwargs):
        super().__init__(llm=llm, search_tool=search_tool, **kwargs)

    def _run(self, ticker: str) -> Dict[str, Any]:
        raise NotImplementedError("Use _arun instead")

    async def _arun(self, ticker: str) -> Dict[str, Any]:
        logger.info(f"Starting Deep Dive analysis for {ticker}")
        
        # 1. Fetch Data
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # 2. Define Questions
        questions = [
            "What does the company do?",
            "How much does the company cost? (Valuation)",
            "What is the company's financial position? (Balance Sheet Health)",
            "What is the shareholder structure? (Insider/Institutional Ownership)",
            "What is the trend in the number of shares issued? (Buybacks/Dilution)",
            "What is the trend in current sales?",
            "What is the trend in EBITDA?",
            "What is the trend in EBIT?",
            "What was the evolution of net income?",
            "What is the evolution of margins?",
            "What is the risk of this investment?",
            "What are the estimates for the future?",
            "Formulate an investment story.",
            "What is the target price in 10, 15, or 20 years?",
            "What is the expected rate of return?"
        ]
        
        # 3. Prepare Context for LLM
        # We need to provide enough data for the LLM to answer these questions
        context = f"""
        Company: {info.get('longName', ticker)} ({ticker})
        Industry: {info.get('industry', 'N/A')}
        Sector: {info.get('sector', 'N/A')}
        Business Summary: {info.get('longBusinessSummary', 'N/A')}
        
        Financial Metrics:
        - Market Cap: {info.get('marketCap', 'N/A')}
        - P/E Ratio: {info.get('trailingPE', 'N/A')}
        - Forward P/E: {info.get('forwardPE', 'N/A')}
        - P/S Ratio: {info.get('priceToSalesTrailing12Months', 'N/A')}
        - P/B Ratio: {info.get('priceToBook', 'N/A')}
        - EV/EBITDA: {info.get('enterpriseToEbitda', 'N/A')}
        
        Growth & Margins:
        - Revenue Growth: {info.get('revenueGrowth', 'N/A')}
        - Earnings Growth: {info.get('earningsGrowth', 'N/A')}
        - Gross Margin: {info.get('grossMargins', 'N/A')}
        - Operating Margin: {info.get('operatingMargins', 'N/A')}
        - Profit Margin: {info.get('profitMargins', 'N/A')}
        
        Balance Sheet:
        - Total Cash: {info.get('totalCash', 'N/A')}
        - Total Debt: {info.get('totalDebt', 'N/A')}
        - Current Ratio: {info.get('currentRatio', 'N/A')}
        - Debt/Equity: {info.get('debtToEquity', 'N/A')}
        
        Returns:
        - ROE: {info.get('returnOnEquity', 'N/A')}
        - ROA: {info.get('returnOnAssets', 'N/A')}
        
        Ownership:
        - Insider Ownership: {info.get('heldPercentInsiders', 'N/A')}
        - Institutional Ownership: {info.get('heldPercentInstitutions', 'N/A')}
        
        Analyst Targets:
        - Target Mean: {info.get('targetMeanPrice', 'N/A')}
        - Target High: {info.get('targetHighPrice', 'N/A')}
        - Target Low: {info.get('targetLowPrice', 'N/A')}
        """
        
        # Add historical data context (simplified for prompt length)
        try:
            financials = stock.financials
            if not financials.empty:
                context += "\n\nRecent Financials (Last 3 Years):\n"
                context += financials.iloc[:, :3].to_string()
        except Exception as e:
            logger.warning(f"Could not fetch financials: {e}")

        # 4. Generate Answers using LLM
        prompt = f"""
        You are an expert financial analyst. Based on the provided financial data for {ticker}, answer the following 15 questions in detail.
        
        Context Data:
        {context}
        
       Questions:
        {chr(10).join([f"{i+1}. {q}" for i, q in enumerate(questions)])}
        
        IMPORTANT: Return ONLY a valid JSON object (no markdown, no code blocks) where:
        - Keys are numbered "1", "2", "3"... up to "15" 
        - Values are your detailed answers to each question
        
        Example format:
        {{
            "1": "Apple Inc. is a technology company that designs...",
            "2": "Based on current P/E ratio of...",
            "3": "The company has a strong balance sheet..."
        }}
        
        For the "Investment Story", provide a compelling narrative.
        For "Target Price" and "Rate of Return", use the data to make reasonable projections.
        If data is missing, state that clearly in your answer.
        """
        
        try:
            response = await self.llm.ainvoke(prompt)
            content = response.content.strip()
            
            logger.info(f"LLM Response preview: {content[:200]}...")
            
            # Parse JSON from LLM response
            import json
            import re
            
            # Try to extract JSON from markdown code blocks first
            code_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
            if code_block_match:
                json_str = code_block_match.group(1)
            else:
                # Try to find JSON object in the response
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    # No JSON found - create a fallback response
                    logger.warning("No JSON found in LLM response, using raw text")
                    answers = {}
                    for i, q in enumerate(questions, 1):
                        answers[str(i)] = content[:500] if i == 1 else "Unable to parse specific answer from LLM response"
                    
                    return {
                        "ticker": ticker,
                        "questions": questions,
                        "answers": answers
                    }
            
            try:
                answers_raw = json.loads(json_str)
                
                # Normalize the answers dictionary to use string keys "1", "2", etc.
                answers = {}
                for i, q in enumerate(questions, 1):
                    key_str = str(i)
                    # Try to find the answer
                    if key_str in answers_raw:
                        answers[key_str] = answers_raw[key_str]
                    elif q in answers_raw:  # If LLM used full question as key
                        answers[key_str] = answers_raw[q]
                    else:
                        # Search for partial matches
                        found = False
                        for k, v in answers_raw.items():
                            if str(i) in str(k) or q[:20] in str(k):
                                answers[key_str] = v
                                found = True
                                break
                        if not found:
                            answers[key_str] = "Answer not found in LLM response"
                
                logger.info(f"Successfully parsed {len(answers)} answers")
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                logger.error(f"JSON string was: {json_str[:500]}...")
                answers = {}
                for i in range(1, len(questions) + 1):
                    answers[str(i)] = f"Failed to parse JSON response. Error: {str(e)}"

            return {
                "ticker": ticker,
                "questions": questions,
                "answers": answers
            }
            
        except Exception as e:
            logger.error(f"Error during Deep Dive analysis: {e}", exc_info=True)
            return {
                "ticker": ticker,
                "questions": questions,
                "answers": {str(i): f"Error: {str(e)}" for i in range(1, len(questions) + 1)}
            }
