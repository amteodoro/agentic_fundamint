import pytest
from fastapi.testclient import TestClient
from app.main import app  # Import your FastAPI app instance

# Create a TestClient instance
client = TestClient(app)

# --- Test for the Root Endpoint ---
def test_read_root():
    """
    Tests the root endpoint to ensure the API is running.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "Welcome to the Fundamint API!"}

# --- Tests for the Stock Profile Endpoint ---
def test_get_stock_profile_success():
    """
    Tests fetching a valid stock profile (e.g., AAPL).
    """
    response = client.get("/api/stock/AAPL/profile")
    assert response.status_code == 200
    data = response.json()
    assert data["longName"] == "Apple Inc."
    assert "sector" in data
    assert "fullTimeEmployees" in data

def test_get_stock_profile_not_found():
    """
    Tests fetching a profile for a non-existent ticker.
    """
    response = client.get("/api/stock/INVALIDTICKERXYZ/profile")
    assert response.status_code == 404
    assert response.json() == {"detail": "Ticker 'INVALIDTICKERXYZ' not found."}

# --- Tests for the Financials Endpoint ---
def test_get_stock_financials_success():
    """
    Tests fetching financial data for a valid stock (e.g., MSFT).
    """
    response = client.get("/api/stock/MSFT/financials")
    assert response.status_code == 200
    data = response.json()
    
    # Check the overall structure
    assert "financials" in data
    
    # Check for a specific, expected financial metric
    assert "Total Revenue" in data["financials"]
    
    # Check that the metric's value is a dictionary (date -> value)
    revenue_data = data["financials"]["Total Revenue"]
    assert isinstance(revenue_data, dict)
    assert len(revenue_data) > 0  # Make sure there's at least one data point

def test_get_stock_financials_not_found():
    """
    Tests fetching financials for a ticker that may not have data.
    """
    # Using a ticker that is less likely to have complete financial statements
    response = client.get("/api/stock/NONEXISTENTTICKER/financials")
    assert response.status_code == 404

# --- Tests for the Price History Endpoint ---
def test_get_stock_price_history_success():
    """
    Tests fetching historical price data for a valid stock (e.g., GOOG).
    """
    response = client.get("/api/stock/GOOG/price-history?period=1mo")
    assert response.status_code == 200
    data = response.json()
    assert "history" in data
    assert isinstance(data["history"], list)
    assert len(data["history"]) > 0
    
    # Check the structure of a single data point
    first_data_point = data["history"][0]
    assert "Date" in first_data_point
    assert "Open" in first_data_point
    assert "High" in first_data_point
    assert "Low" in first_data_point
    assert "Close" in first_data_point
    assert "Volume" in first_data_point

def test_get_stock_price_history_not_found():
    """
    Tests fetching price history for a non-existent ticker.
    """
    response = client.get("/api/stock/INVALIDTICKERXYZ/price-history")
    assert response.status_code == 404
    assert response.json() == {"detail": "Ticker 'INVALIDTICKERXYZ' not found."}

def test_get_stock_price_history_no_data_for_period():
    """
    Tests fetching price history for a valid ticker but a period with no data.
    This might be rare for major stocks, but good to test.
    """
    # Using a very short period for a stock that might not have data for it
    # or a period that is too far in the past for yfinance to provide data.
    # For now, we'll use a valid ticker and a very short period.
    response = client.get("/api/stock/AAPL/price-history?period=1d")
    assert response.status_code == 200 # It should return 200 even if there is no data for the day
    data = response.json()
    assert "history" in data
    assert isinstance(data["history"], list)
    # It might return an empty list if no data for the specific day, or one entry.
    # The key is that it doesn't return a 404 unless the ticker is invalid.

# --- Tests for the Search Endpoint ---
def test_search_stocks_valid_ticker():
    """
    Tests searching for a valid stock ticker (e.g., AAPL).
    """
    response = client.get("/api/search?q=AAPL")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) == 1
    assert data["results"][0]["symbol"] == "AAPL"
    assert data["results"][0]["longName"] == "Apple Inc."

def test_search_stocks_invalid_ticker():
    """
    Tests searching for an invalid stock ticker.
    """
    response = client.get("/api/search?q=INVALIDSEARCHTERM")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) == 0

def test_search_stocks_empty_query():
    """
    Tests searching with an empty query string.
    """
    response = client.get("/api/search?q=")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) == 0
