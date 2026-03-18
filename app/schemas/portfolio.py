from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field

from .common import BaseSchema


class PortfolioValue(BaseModel):
    """持仓市值"""
    stock_code: str
    stock_name: Optional[str]
    quantity: int
    current_price: Optional[Decimal] = None
    market_value: Optional[Decimal] = None


class PortfolioTotal(BaseModel):
    """总资产"""
    cash_balance: Decimal
    stock_value: Decimal
    total_value: Decimal


class ProfitLoss(BaseModel):
    """盈亏"""
    stock_code: str
    stock_name: Optional[str]
    quantity: int
    avg_cost: Decimal
    current_price: Optional[Decimal] = None
    profit_loss: Optional[Decimal] = None
    profit_loss_percent: Optional[Decimal] = None


class PortfolioProfitLoss(BaseModel):
    """组合盈亏"""
    items: list[ProfitLoss]
    total_profit_loss: Optional[Decimal] = None
    total_profit_loss_percent: Optional[Decimal] = None