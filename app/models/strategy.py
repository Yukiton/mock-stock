"""策略模型"""

from datetime import datetime
from sqlalchemy import String, Boolean, Text, JSON, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Optional, Any

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .user import User


class Strategy(Base, TimestampMixin):
    """策略表"""
    __tablename__ = "strategies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    stock_code: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    strategy_name: Mapped[Optional[str]] = mapped_column(String(100))
    strategy_type: Mapped[str] = mapped_column(String(20), nullable=False)  # THRESHOLD/MA/MACD/RSI/MCP_SMART
    strategy_config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    executor_type: Mapped[str] = mapped_column(String(20), nullable=False)  # AUTO_TRADE/WEBSOCKET/WEBHOOK
    executor_config: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_triggered_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # 关联
    user: Mapped["User"] = relationship("User", back_populates="strategies")

    def __repr__(self) -> str:
        return f"<Strategy(id={self.id}, user_id={self.user_id}, stock_code='{self.stock_code}', type='{self.strategy_type}')>"