from datetime import datetime, timezone
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Numeric, Integer, Boolean, Text, JSON, DateTime, ForeignKey
from typing import Optional


def utcnow():
    """返回 UTC 时间（timezone-aware）"""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """SQLAlchemy 基础模型类"""
    pass


class TimestampMixin:
    """时间戳混入类"""
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )