"""均线策略 - 价格突破均线时触发"""

from decimal import Decimal

from .base import BaseStrategy, CheckResult
from .context import StrategyContext
from app.quant import calculate_ma


class MAStrategy(BaseStrategy):
    """
    均线策略

    使用quant模块计算MA指标。

    config: {
        "period": 5,           # 均线周期（5/10/20/60等）
        "direction": "up",     # 突破方向: "up"(向上突破), "down"(向下突破), "both"(双向)
        "action_on_up": "BUY",    # 向上突破时的动作（默认买入）
        "action_on_down": "SELL"  # 向下跌破时的动作（默认卖出）
    }
    """

    @property
    def strategy_type(self) -> str:
        return "MA"

    async def check(self, context: StrategyContext, config: dict) -> CheckResult:
        period = config.get("period", 5)
        direction = config.get("direction", "both")

        # 获取动作配置
        action_on_up = config.get("action_on_up", "BUY")
        action_on_down = config.get("action_on_down", "SELL")

        # 从历史价格计算MA
        closes = self._extract_closes(context)
        if not closes or len(closes) < period:
            return CheckResult(
                triggered=False,
                reason=f"无法计算MA{period}，历史数据不足"
            )

        ma_value = calculate_ma(closes, period)
        if ma_value is None:
            return CheckResult(
                triggered=False,
                reason=f"无法计算MA{period}"
            )

        price = float(context.current_price)
        ma = float(ma_value)

        # 判断突破
        is_above = price > ma
        details = {
            "ma_period": period,
            "ma_value": ma,
            "price": price,
            "is_above": is_above
        }

        if direction == "up" and is_above:
            return CheckResult(
                triggered=True,
                reason=f"价格 {price} 向上突破MA{period}({ma:.2f})",
                suggested_action=action_on_up,
                details=details
            )
        elif direction == "down" and not is_above:
            return CheckResult(
                triggered=True,
                reason=f"价格 {price} 向下跌破MA{period}({ma:.2f})",
                suggested_action=action_on_down,
                details=details
            )
        elif direction == "both":
            return CheckResult(
                triggered=True,
                reason=f"价格 {price} 突破MA{period}({ma:.2f})，方向: {'向上' if is_above else '向下'}",
                suggested_action=action_on_up if is_above else action_on_down,
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