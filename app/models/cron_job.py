from datetime import datetime
from sqlalchemy import String, Boolean, Text, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional, Any

from .base import Base, utcnow


class CronJob(Base):
    """定时任务配置表"""
    __tablename__ = "cron_jobs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    cron_expression: Mapped[str] = mapped_column(String(100), nullable=False)
    job_type: Mapped[str] = mapped_column(String(20), nullable=False)  # PRICE_CHECK/ALERT_CHECK/CUSTOM
    config: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return f"<CronJob(id={self.id}, name='{self.name}', job_type='{self.job_type}')>"