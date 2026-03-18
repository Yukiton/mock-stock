from sqlalchemy import String, Numeric, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Optional
from decimal import Decimal

from .base import Base

if TYPE_CHECKING:
    from .user import User


class Transaction(Base):
    """交易记录表"""
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    stock_code: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    stock_name: Mapped[Optional[str]] = mapped_column(String(50))
    type: Mapped[str] = mapped_column(String(10), nullable=False)  # "BUY" / "SELL"
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # 关联
    user: Mapped["User"] = relationship("User", back_populates="transactions")

    def __repr__(self) -> str:
        return f"<Transaction(id={self.id}, user_id={self.user_id}, type='{self.type}', stock_code='{self.stock_code}')>"