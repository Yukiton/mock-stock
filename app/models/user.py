from sqlalchemy import String, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, List
from decimal import Decimal

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .position import Position
    from .transaction import Transaction
    from .price_alert import PriceAlert


class User(Base, TimestampMixin):
    """用户表"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    balance: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))

    # 关联
    positions: Mapped[List["Position"]] = relationship(
        "Position", back_populates="user", cascade="all, delete-orphan"
    )
    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction", back_populates="user", cascade="all, delete-orphan"
    )
    alerts: Mapped[List["PriceAlert"]] = relationship(
        "PriceAlert", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', balance={self.balance})>"