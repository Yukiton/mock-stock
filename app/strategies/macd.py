"""MACD策略 - MACD金叉/死叉时触发"""

from decimal import Decimal

from .base import AlertStrategy, AlertContext, CheckResult


class MACDStrategy(AlertStrategy):
    """
    MACD策略

    config: {
        "fast": 12,           # 快线周期
        "slow": 26,           # 慢线周期
        "signal": 9,          # 信号线周期
        "type": "golden_cross" # 触发类型: "golden_cross"(金叉), "death_cross"(死叉), "both"
    }
    """

    @property
    def strategy_type(self) -> str:
        return "MACD"

    def check(self, context: AlertContext, config: dict) -> CheckResult:
        fast = config.get("fast", 12)
        slow = config.get("slow", 26)
        signal_period = config.get("signal", 9)
        cross_type = config.get("type", "both")

        # 从indicators获取或计算MACD
        macd_data = context.indicators.get("macd")
        if macd_data is None:
            macd_data = self._calculate_macd(context, fast, slow, signal_period)

        if macd_data is None:
            return CheckResult(
                triggered=False,
                reason="无法计算MACD，历史数据不足"
            )

        macd = macd_data.get("macd")
        signal = macd_data.get("signal")
        hist = macd_data.get("histogram")

        if macd is None or signal is None:
            return CheckResult(triggered=False, reason="MACD数据不完整")

        details = {
            "macd": macd,
            "signal": signal,
            "histogram": hist
        }

        # 判断金叉/死叉
        # 金叉: MACD上穿信号线
        # 死叉: MACD下穿信号线
        is_golden_cross = macd > signal and hist > 0
        is_death_cross = macd < signal and hist < 0

        if cross_type in ("golden_cross", "both") and is_golden_cross:
            return CheckResult(
                triggered=True,
                reason=f"MACD金叉: MACD({macd:.4f}) > Signal({signal:.4f})",
                details=details
            )
        elif cross_type in ("death_cross", "both") and is_death_cross:
            return CheckResult(
                triggered=True,
                reason=f"MACD死叉: MACD({macd:.4f}) < Signal({signal:.4f})",
                details=details
            )

        return CheckResult(triggered=False)

    def calculate_indicators(self, context: AlertContext) -> dict:
        """计算MACD指标"""
        macd_data = self._calculate_macd(context, 12, 26, 9)
        if macd_data:
            return {"macd": macd_data}
        return {}

    def _calculate_macd(self, context: AlertContext, fast: int, slow: int, signal: int) -> dict | None:
        """计算MACD指标"""
        if len(context.history_prices) < slow + signal:
            return None

        # 提取收盘价
        closes = []
        for item in context.history_prices:
            close = item.get("close") or item.get("收盘")
            if close is not None:
                closes.append(float(close))

        if len(closes) < slow + signal:
            return None

        # 计算EMA
        def ema(prices: list, period: int) -> list:
            result = []
            multiplier = 2 / (period + 1)
            result.append(sum(prices[:period]) / period)  # 初始SMA
            for price in prices[period:]:
                result.append((price - result[-1]) * multiplier + result[-1])
            return result

        ema_fast = ema(closes, fast)
        ema_slow = ema(closes, slow)

        # 对齐长度
        min_len = min(len(ema_fast), len(ema_slow))
        ema_fast = ema_fast[-min_len:]
        ema_slow = ema_slow[-min_len:]

        # MACD线 = 快线EMA - 慢线EMA
        macd_line = [f - s for f, s in zip(ema_fast, ema_slow)]

        # 信号线 = MACD的EMA
        if len(macd_line) < signal:
            return None
        signal_line = ema(macd_line, signal)

        # 对齐
        min_len = min(len(macd_line), len(signal_line))
        macd_line = macd_line[-min_len:]
        signal_line = signal_line[-min_len:]

        # 柱状图
        histogram = [m - s for m, s in zip(macd_line, signal_line)]

        return {
            "macd": macd_line[-1],
            "signal": signal_line[-1],
            "histogram": histogram[-1]
        }