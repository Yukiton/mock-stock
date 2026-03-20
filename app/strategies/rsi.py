"""RSI策略 - RSI进入超买/超卖区域时触发"""

from decimal import Decimal

from .base import BaseStrategy, CheckResult
from .context import StrategyContext
from app.quant import calculate_rsi


class RSIStrategy(BaseStrategy):
    """
    RSI策略

    使用quant模块计算RSI指标。

    config: {
        "period": 14,          # RSI周期
        "overbought": 70,      # 超买阈值
        "oversold": 30,        # 超卖阈值
        "type": "both",        # "overbought"(超买), "oversold"(超卖), "both"
        "action_on_overbought": "SELL",  # 超买时的动作（默认卖出）
        "action_on_oversold": "BUY"      # 超卖时的动作（默认买入）
    }
    """

    @property
    def strategy_type(self) -> str:
        return "RSI"

    async def check(self, context: StrategyContext, config: dict) -> CheckResult:
        period = config.get("period", 14)
        overbought = config.get("overbought", 70)
        oversold = config.get("oversold", 30)
        alert_type = config.get("type", "both")

        # 获取动作配置
        action_on_overbought = config.get("action_on_overbought", "SELL")
        action_on_oversold = config.get("action_on_oversold", "BUY")

        # 从历史价格计算RSI
        closes = self._extract_closes(context)
        if not closes or len(closes) < period + 1:
            return CheckResult(
                triggered=False,
                reason=f"无法计算RSI{period}，历史数据不足"
            )

        rsi_data = calculate_rsi(closes, period)
        if rsi_data is None:
            return CheckResult(
                triggered=False,
                reason=f"无法计算RSI{period}"
            )

        rsi = rsi_data.get("rsi")

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
                suggested_action=action_on_overbought,
                details=details
            )
        elif alert_type in ("oversold", "both") and rsi <= oversold:
            return CheckResult(
                triggered=True,
                reason=f"RSI({rsi:.2f})进入超卖区域(<{oversold})",
                suggested_action=action_on_oversold,
                details=details
            )

        return CheckResult(triggered=False)

    def _extract_closes(self, context: StrategyContext) -> list[float] | None:
        """从历史价格中提取收盘价列表（从新到旧）"""
        if not context.history_prices:
            return None

        closes = []
        for item in context.history_prices:
            close = item.get("close") or item.get("收盘")
            if close is not None:
                closes.append(float(close))

        return closes if closes else None