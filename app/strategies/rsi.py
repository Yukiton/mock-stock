"""RSI策略 - RSI进入超买/超卖区域时触发"""

from decimal import Decimal

from .base import AlertStrategy, AlertContext, CheckResult


class RSIStrategy(AlertStrategy):
    """
    RSI策略

    config: {
        "period": 14,          # RSI周期
        "overbought": 70,      # 超买阈值
        "oversold": 30,        # 超卖阈值
        "type": "both"         # "overbought"(超买), "oversold"(超卖), "both"
    }
    """

    @property
    def strategy_type(self) -> str:
        return "RSI"

    def check(self, context: AlertContext, config: dict) -> CheckResult:
        period = config.get("period", 14)
        overbought = config.get("overbought", 70)
        oversold = config.get("oversold", 30)
        alert_type = config.get("type", "both")

        # 从indicators获取或计算RSI
        rsi_key = f"rsi{period}"
        rsi = context.indicators.get(rsi_key)

        if rsi is None:
            rsi = self._calculate_rsi(context, period)

        if rsi is None:
            return CheckResult(
                triggered=False,
                reason=f"无法计算RSI{period}，历史数据不足"
            )

        details = {
            "rsi_period": period,
            "rsi_value": rsi,
            "overbought": overbought,
            "oversold": oversold
        }

        if alert_type in ("overbought", "both") and rsi >= overbought:
            return CheckResult(
                triggered=True,
                reason=f"RSI({rsi:.2f})进入超买区域(>{overbought})",
                details=details
            )
        elif alert_type in ("oversold", "both") and rsi <= oversold:
            return CheckResult(
                triggered=True,
                reason=f"RSI({rsi:.2f})进入超卖区域(<{oversold})",
                details=details
            )

        return CheckResult(triggered=False)

    def calculate_indicators(self, context: AlertContext) -> dict:
        """计算RSI指标"""
        result = {}
        for period in [6, 14, 24]:
            rsi = self._calculate_rsi(context, period)
            if rsi is not None:
                result[f"rsi{period}"] = rsi
        return result

    def _calculate_rsi(self, context: AlertContext, period: int) -> float | None:
        """计算RSI指标"""
        if len(context.history_prices) < period + 1:
            return None

        # 提取收盘价
        closes = []
        for item in context.history_prices:
            close = item.get("close") or item.get("收盘")
            if close is not None:
                closes.append(float(close))

        if len(closes) < period + 1:
            return None

        # 计算价格变化
        changes = [closes[i] - closes[i + 1] for i in range(len(closes) - 1)]

        if len(changes) < period:
            return None

        # 取最近period个变化
        recent_changes = changes[:period]
        gains = [c for c in recent_changes if c > 0]
        losses = [-c for c in recent_changes if c < 0]

        avg_gain = sum(gains) / period if gains else 0
        avg_loss = sum(losses) / period if losses else 0

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi