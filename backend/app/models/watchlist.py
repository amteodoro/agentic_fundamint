"""
Watchlist and WatchlistItem models for tracking stocks of interest.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Text, DateTime, ForeignKey, Numeric, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from ..database import Base

if TYPE_CHECKING:
    from .user import User


class Watchlist(Base):
    """
    Watchlist model representing a user's list of stocks to watch.
    
    Attributes:
        id: Unique identifier (UUID)
        user_id: Reference to the owning user
        name: Watchlist name
        created_at: Timestamp of creation
    """
    
    __tablename__ = "watchlists"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="watchlists",
    )
    items: Mapped[list["WatchlistItem"]] = relationship(
        "WatchlistItem",
        back_populates="watchlist",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<Watchlist(id={self.id}, name={self.name}, user_id={self.user_id})>"


class WatchlistItem(Base):
    """
    WatchlistItem model representing a stock within a watchlist.
    
    Attributes:
        id: Unique identifier (UUID)
        watchlist_id: Reference to the parent watchlist
        ticker: Stock ticker symbol
        added_at: When the stock was added to the watchlist
        target_price: Optional target price for alerts
        notes: Optional notes about the stock
    """
    
    __tablename__ = "watchlist_items"
    __table_args__ = (
        UniqueConstraint("watchlist_id", "ticker", name="uq_watchlist_ticker"),
    )
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    watchlist_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("watchlists.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ticker: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    target_price: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    
    # Relationships
    watchlist: Mapped["Watchlist"] = relationship(
        "Watchlist",
        back_populates="items",
    )
    
    def __repr__(self) -> str:
        return f"<WatchlistItem(id={self.id}, ticker={self.ticker})>"
