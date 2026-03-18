from sqlalchemy import String, Numeric, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Optional
from decimal import Decimal

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .user import User


class Position(Base, TimestampMixin):
    """持仓表"""
    __tablename__ = "positions"
    __table_args__ = (
        # 每用户每股票唯一
        {"sqlite_autoincrement": True},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    stock_code: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    stock_name: Mapped[Optional[str]] = mapped_column(String(50))
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    avg_cost: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=Decimal("0"))

    # 关联
    user: Mapped["User"] = relationship("User", back_populates="positions")

    def __repr__(self) -> str:
        return f"<Position(id={self.id}, user_id={self.user_id}, stock_code='{self.stock_code}', quantity={self.quantity})>"