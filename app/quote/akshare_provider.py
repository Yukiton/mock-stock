from typing import Optional
from decimal import Decimal

import akshare as ak

from .base import QuoteProvider, StockQuote


class AkshareQuoteProvider(QuoteProvider):
    """基于 akshare 的行情提供者"""

    def get_quote(self, stock_code: str) -> Optional[StockQuote]:
        """
        获取单只股票/ETF行情

        自动判断类型：
        - 5开头/6开头: 上证 (ETF或主板)
        - 0开头/1开头/2开头/3开头: 深证
        """
        try:
            return self._get_quote_from_xueqiu(stock_code)
        except Exception:
            return None

    def _get_quote_from_xueqiu(self, stock_code: str) -> Optional[StockQuote]:
        """从雪球获取实时行情"""
        market_prefix = self._get_market_prefix(stock_code)
        symbol = f"{market_prefix}{stock_code}".upper()

        df = ak.stock_individual_spot_xq(symbol=symbol)
        if df is None or df.empty:
            return None

        # 转换为字典方便查找
        data = dict(zip(df.iloc[:, 0], df.iloc[:, 1]))

        # 雪球返回的字段名
        return StockQuote(
            stock_code=stock_code,
            current_price=self._to_decimal(data.get('现价')),
            open_price=self._to_decimal(data.get('今开')),
            high_price=self._to_decimal(data.get('最高')),
            low_price=self._to_decimal(data.get('最低')),
            prev_close=self._to_decimal(data.get('昨收')),
            volume=self._to_int(data.get('成交量')),
            amount=self._to_decimal(data.get('成交额')),
        )

    def get_quotes(self, stock_codes: list[str]) -> dict[str, StockQuote]:
        """批量获取股票行情"""
        result = {}
        for code in stock_codes:
            quote = self.get_quote(code)
            if quote:
                result[code] = quote
        return result

    @staticmethod
    def _get_market_prefix(stock_code: str) -> str:
        """获取市场前缀: SH=上证, SZ=深证"""
        if stock_code.startswith(('5', '6', '9')):
            return 'SH'
        return 'SZ'

    @staticmethod
    def _to_decimal(value) -> Optional[Decimal]:
        """转换为 Decimal"""
        if value is None or value == 'None':
            return None
        try:
            return Decimal(str(value))
        except Exception:
            return None

    @staticmethod
    def _to_int(value) -> Optional[int]:
        """转换为 int"""
        if value is None or value == 'None':
            return None
        try:
            return int(float(value))
        except Exception:
            return None


# 全局行情提供者实例
_quote_provider: Optional[QuoteProvider] = None


def get_quote_provider() -> QuoteProvider:
    """获取行情提供者实例"""
    global _quote_provider
    if _quote_provider is None:
        _quote_provider = AkshareQuoteProvider()
    return _quote_provider