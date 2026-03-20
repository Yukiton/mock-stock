"""策略执行上下文"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Optional


@dataclass
class StrategyContext:
    """
    策略执行上下文（原始数据）

    只存储原始数据，不含量化指标。
    量化指标由策略器内部调用 quant 模块按需计算。
    """
    # 基础信息
    user_id: int
    stock_code: str

    # 行情数据
    current_price: Decimal
    open_price: Optional[Decimal] = None
    high_price: Optional[Decimal] = None
    low_price: Optional[Decimal] = None
    prev_close: Optional[Decimal] = None
    volume: Optional[int] = None

    # 持仓信息
    position_quantity: Optional[int] = None
    position_avg_cost: Optional[Decimal] = None
    position_profit_loss: Optional[Decimal] = None
    position_profit_loss_percent: Optional[Decimal] = None

    # 交易记录
    recent_transactions: list[dict[str, Any]] = field(default_factory=list)

    # 历史价格（用于量化计算）
    history_prices: list[dict[str, Any]] = field(default_factory=list)