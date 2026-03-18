from abc import ABC, abstractmethod
from typing import Optional
from decimal import Decimal
from dataclasses import dataclass


@dataclass
class StockQuote:
    """股票行情数据"""
    stock_code: str
    stock_name: Optional[str] = None
    current_price: Optional[Decimal] = None
    open_price: Optional[Decimal] = None
    high_price: Optional[Decimal] = None
    low_price: Optional[Decimal] = None
    prev_close: Optional[Decimal] = None
    change: Optional[Decimal] = None
    change_percent: Optional[Decimal] = None
    volume: Optional[int] = None
    amount: Optional[Decimal] = None
    turnover_rate: Optional[Decimal] = None
    limit_up: Optional[Decimal] = None
    limit_down: Optional[Decimal] = None

    # 五档买卖
    buy_1: Optional[Decimal] = None
    buy_1_vol: Optional[int] = None
    sell_1: Optional[Decimal] = None
    sell_1_vol: Optional[int] = None


class QuoteProvider(ABC):
    """行情提供者抽象基类"""

    @abstractmethod
    def get_quote(self, stock_code: str) -> Optional[StockQuote]:
        """
        获取单只股票行情

        Args:
            stock_code: 股票代码

        Returns:
            股票行情数据，如果获取失败返回 None
        """
        pass

    @abstractmethod
    def get_quotes(self, stock_codes: list[str]) -> dict[str, StockQuote]:
        """
        批量获取股票行情

        Args:
            stock_codes: 股票代码列表

        Returns:
            股票代码到行情数据的映射
        """
        pass