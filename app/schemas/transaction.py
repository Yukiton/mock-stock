from datetime import datetime
from decimal import Decimal
from typing import Optional, Literal
from pydantic import BaseModel, Field

from .common import BaseSchema


class TransactionBase(BaseModel):
    """交易基础信息"""
    stock_code: str = Field(..., min_length=1, max_length=10)
    stock_name: Optional[str] = Field(None, max_length=50)


class TransactionCreate(TransactionBase):
    """创建交易"""
    type: Literal["BUY", "SELL"]
    quantity: int = Field(..., gt=0)
    price: Decimal = Field(..., gt=0)


class TransactionResponse(BaseSchema):
    """交易响应"""
    id: int
    user_id: int
    stock_code: str
    stock_name: Optional[str]
    type: str
    quantity: int
    price: Decimal
    amount: Decimal
    created_at: datetime


class TradeRequest(BaseModel):
    """交易请求"""
    stock_code: str = Field(..., min_length=1, max_length=10)
    quantity: int = Field(..., gt=0, description="交易数量（股）")
    price: Decimal = Field(..., gt=0, description="成交价格")


class TradeResponse(BaseSchema):
    """交易响应"""
    transaction: TransactionResponse
    balance: Decimal
    position_quantity: int