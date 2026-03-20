"""阈值策略 - 价格突破上限或下限时触发"""

from decimal import Decimal

from .base import BaseStrategy, CheckResult
from .context import StrategyContext


class ThresholdStrategy(BaseStrategy):
    """
    阈值策略

    config: {
        "upper": 100.0,      # 上限价格（可选）
        "lower": 50.0,       # 下限价格（可选）
        "percent_upper": 5.0, # 涨幅上限百分比（可选，相对昨收）
        "percent_lower": -5.0, # 跌幅下限百分比（可选，相对昨收）
        "action_on_upper": "SELL",  # 触及上限时的动作（默认卖出）
        "action_on_lower": "BUY"    # 触及下限时的动作（默认买入）
    }
    """

    @property
    def strategy_type(self) -> str:
        return "THRESHOLD"

    async def check(self, context: StrategyContext, config: dict) -> CheckResult:
        price = float(context.current_price)
        prev_close = float(context.prev_close) if context.prev_close else None

        # 获取动作配置
        action_on_upper = config.get("action_on_upper", "SELL")
        action_on_lower = config.get("action_on_lower", "BUY")

        # 检查绝对价格上限
        upper = config.get("upper")
        if upper is not None and price >= float(upper):
            return CheckResult(
                triggered=True,
                reason=f"价格 {price} 触及上限 {upper}",
                suggested_action=action_on_upper,
                details={"type": "upper", "price": price, "threshold": upper}
            )

        # 检查绝对价格下限
        lower = config.get("lower")
        if lower is not None and price <= float(lower):
            return CheckResult(
                triggered=True,
                reason=f"价格 {price} 触及下限 {lower}",
                suggested_action=action_on_lower,
                details={"type": "lower", "price": price, "threshold": lower}
            )

        # 检查涨幅上限百分比
        percent_upper = config.get("percent_upper")
        if percent_upper is not None and prev_close:
            change_percent = ((price - prev_close) / prev_close) * 100
            if change_percent >= float(percent_upper):
                return CheckResult(
                    triggered=True,
                    reason=f"涨幅 {change_percent:.2f}% 触及上限 {percent_upper}%",
                    suggested_action=action_on_upper,
                    details={"type": "percent_upper", "change_percent": change_percent, "threshold": percent_upper}
                )

        # 检查跌幅下限百分比
        percent_lower = config.get("percent_lower")
        if percent_lower is not None and prev_close:
            change_percent = ((price - prev_close) / prev_close) * 100
            if change_percent <= float(percent_lower):
                return CheckResult(
                    triggered=True,
                    reason=f"跌幅 {abs(change_percent):.2f}% 触及下限 {abs(percent_lower)}%",
                    suggested_action=action_on_lower,
                    details={"type": "percent_lower", "change_percent": change_percent, "threshold": percent_lower}
                )

        return CheckResult(triggered=False)