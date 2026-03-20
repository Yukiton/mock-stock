"""MACD策略 - MACD金叉/死叉时触发"""

from decimal import Decimal

from .base import BaseStrategy, CheckResult
from .context import StrategyContext
from app.quant import calculate_macd


class MACDStrategy(BaseStrategy):
    """
    MACD策略

    使用quant模块计算MACD指标。

    config: {
        "fast": 12,           # 快线周期
        "slow": 26,           # 慢线周期
        "signal": 9,          # 信号线周期
        "type": "golden_cross", # 触发类型: "golden_cross"(金叉), "death_cross"(死叉), "both"
        "action_on_golden": "BUY",  # 金叉时的动作（默认买入）
        "action_on_death": "SELL"   # 死叉时的动作（默认卖出）
    }
    """

    @property
    def strategy_type(self) -> str:
        return "MACD"

    async def check(self, context: StrategyContext, config: dict) -> CheckResult:
        fast = config.get("fast", 12)
        slow = config.get("slow", 26)
        signal_period = config.get("signal", 9)
        cross_type = config.get("type", "both")

        # 获取动作配置
        action_on_golden = config.get("action_on_golden", "BUY")
        action_on_death = config.get("action_on_death", "SELL")

        # 从历史价格计算MACD
        closes = self._extract_closes(context)
        if not closes or len(closes) < slow + signal_period:
            return CheckResult(
                triggered=False,
                reason="无法计算MACD，历史数据不足"
            )

        macd_data = calculate_macd(closes, fast, slow, signal_period)
        if macd_data is None:
            return CheckResult(
                triggered=False,
                reason="无法计算MACD"
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
        is_golden_cross = macd > signal and hist > 0
        is_death_cross = macd < signal and hist < 0

        if cross_type in ("golden_cross", "both") and is_golden_cross:
            return CheckResult(
                triggered=True,
                reason=f"MACD金叉: MACD({macd:.4f}) > Signal({signal:.4f})",
                suggested_action=action_on_golden,
                details=details
            )
        elif cross_type in ("death_cross", "both") and is_death_cross:
            return CheckResult(
                triggered=True,
                reason=f"MACD死叉: MACD({macd:.4f}) < Signal({signal:.4f})",
                suggested_action=action_on_death,
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