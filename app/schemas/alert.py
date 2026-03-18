from datetime import datetime
from decimal import Decimal
from typing import Optional, Literal, Any
from pydantic import BaseModel, Field

from .common import BaseSchema


class AlertBase(BaseModel):
    """提醒基础信息"""
    stock_code: str = Field(..., min_length=1, max_length=10)
    alert_name: Optional[str] = Field(None, max_length=100)


class AlertCreate(AlertBase):
    """创建提醒"""
    strategy_type: Literal["THRESHOLD", "MA", "MACD", "RSI", "CUSTOM"]
    strategy_config: dict[str, Any] = Field(..., description="策略配置")
    notifier_type: Literal["WEBSOCKET", "SMTP", "WEBHOOK", "MCP"]
    notifier_config: Optional[dict[str, Any]] = Field(None, description="通知器配置")


class AlertUpdate(BaseModel):
    """更新提醒"""
    alert_name: Optional[str] = Field(None, max_length=100)
    strategy_config: Optional[dict[str, Any]] = None
    notifier_config: Optional[dict[str, Any]] = None
    enabled: Optional[bool] = None


class AlertResponse(BaseSchema):
    """提醒响应"""
    id: int
    user_id: int
    stock_code: str
    alert_name: Optional[str]
    strategy_type: str
    strategy_config: dict[str, Any]
    notifier_type: str
    notifier_config: Optional[dict[str, Any]]
    enabled: bool
    last_triggered_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


# 策略配置示例
class ThresholdConfig(BaseModel):
    """阈值策略配置"""
    upper: Optional[Decimal] = Field(None, description="上限价格")
    lower: Optional[Decimal] = Field(None, description="下限价格")


class MAConfig(BaseModel):
    """均线策略配置"""
    period: int = Field(..., ge=1, le=250, description="均线周期")
    direction: Literal["up", "down"] = Field(..., description="突破方向")


class RSIConfig(BaseModel):
    """RSI策略配置"""
    period: int = Field(default=14, ge=1, le=100, description="RSI周期")
    overbought: int = Field(default=70, ge=50, le=100, description="超买阈值")
    oversold: int = Field(default=30, ge=0, le=50, description="超卖阈值")