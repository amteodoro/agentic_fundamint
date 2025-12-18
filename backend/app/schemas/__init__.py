"""
Pydantic schemas for Fundamint API.
"""

from .auth import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    TokenRefresh,
)
from .portfolio import (
    PortfolioCreate,
    PortfolioUpdate,
    PortfolioResponse,
    PortfolioListResponse,
    HoldingCreate,
    HoldingUpdate,
    HoldingResponse,
)
from .watchlist import (
    WatchlistCreate,
    WatchlistUpdate,
    WatchlistResponse,
    WatchlistListResponse,
    WatchlistItemCreate,
    WatchlistItemUpdate,
    WatchlistItemResponse,
)

__all__ = [
    # Auth schemas
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "Token",
    "TokenRefresh",
    # Portfolio schemas
    "PortfolioCreate",
    "PortfolioUpdate",
    "PortfolioResponse",
    "PortfolioListResponse",
    "HoldingCreate",
    "HoldingUpdate",
    "HoldingResponse",
    # Watchlist schemas
    "WatchlistCreate",
    "WatchlistUpdate",
    "WatchlistResponse",
    "WatchlistListResponse",
    "WatchlistItemCreate",
    "WatchlistItemUpdate",
    "WatchlistItemResponse",
]
