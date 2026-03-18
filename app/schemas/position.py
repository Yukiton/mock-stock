from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field

from .common import BaseSchema


class PositionBase(BaseModel):
    """持仓基础信息"""
    stock_code: str = Field(..., min_length=1, max_length=10)
    stock_name: Optional[str] = Field(None, max_length=50)


class PositionCreate(PositionBase):
    """创建持仓"""
    quantity: int = Field(..., ge=0)
    avg_cost: Decimal = Field(..., ge=0)


class PositionResponse(BaseSchema):
    """持仓响应"""
    id: int
    user_id: int
    stock_code: str
    stock_name: Optional[str]
    quantity: int
    avg_cost: Decimal
    created_at: datetime
    updated_at: datetime


class PositionUpdate(BaseModel):
    """持仓更新"""
    quantity: Optional[int] = Field(None, ge=0)
    avg_cost: Optional[Decimal] = Field(None, ge=0)
    stock_name: Optional[str] = Field(None, max_length=50)


class PositionWithValue(BaseSchema):
    """持仓含市值"""
    id: int
    user_id: int
    stock_code: str
    stock_name: Optional[str]
    quantity: int
    avg_cost: Decimal
    current_price: Optional[Decimal] = None
    market_value: Optional[Decimal] = None
    profit_loss: Optional[Decimal] = None
    profit_loss_percent: Optional[Decimal] = None