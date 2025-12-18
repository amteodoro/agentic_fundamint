"""
Portfolio and PortfolioHolding models for user investment tracking.
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


class Portfolio(Base):
    """
    Portfolio model representing a user's investment portfolio.
    
    Attributes:
        id: Unique identifier (UUID)
        user_id: Reference to the owning user
        name: Portfolio name
        description: Optional description
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
    """
    
    __tablename__ = "portfolios"
    
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
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    
    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="portfolios",
    )
    holdings: Mapped[list["PortfolioHolding"]] = relationship(
        "PortfolioHolding",
        back_populates="portfolio",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<Portfolio(id={self.id}, name={self.name}, user_id={self.user_id})>"


class PortfolioHolding(Base):
    """
    PortfolioHolding model representing a stock position within a portfolio.
    
    Attributes:
        id: Unique identifier (UUID)
        portfolio_id: Reference to the parent portfolio
        ticker: Stock ticker symbol
        shares: Number of shares held
        average_cost: Average cost per share
        added_at: When the position was first added
        notes: Optional notes about the position
    """
    
    __tablename__ = "portfolio_holdings"
    __table_args__ = (
        UniqueConstraint("portfolio_id", "ticker", name="uq_portfolio_ticker"),
    )
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    portfolio_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("portfolios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ticker: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )
    shares: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 8),
        nullable=True,
    )
    average_cost: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    
    # Relationships
    portfolio: Mapped["Portfolio"] = relationship(
        "Portfolio",
        back_populates="holdings",
    )
    
    def __repr__(self) -> str:
        return f"<PortfolioHolding(id={self.id}, ticker={self.ticker}, shares={self.shares})>"
