"""MACD指标 (Moving Average Convergence Divergence)"""

from .ema import calculate_ema_series


def calculate_macd(
    prices: list[float],
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> dict | None:
    """
    计算MACD指标

    Args:
        prices: 价格列表（从新到旧排序）
        fast_period: 快线周期
        slow_period: 慢线周期
        signal_period: 信号线周期

    Returns:
        {
            "macd": MACD值,
            "signal": 信号线值,
            "histogram": 柱状图值,
            "trend": "bullish" | "bearish" | "neutral"
        }
        数据不足返回None
    """
    if len(prices) < slow_period + signal_period:
        return None

    # 计算快慢EMA
    fast_ema = calculate_ema_series(prices, fast_period)
    slow_ema = calculate_ema_series(prices, slow_period)

    if not fast_ema or not slow_ema:
        return None

    # 对齐长度
    min_len = min(len(fast_ema), len(slow_ema))
    fast_ema = fast_ema[:min_len]
    slow_ema = slow_ema[:min_len]

    # MACD线 = 快线 - 慢线
    macd_line = [f - s for f, s in zip(fast_ema, slow_ema)]

    # 信号线 = MACD的EMA
    signal_line = calculate_ema_series(macd_line, signal_period)

    if not signal_line:
        return None

    # 柱状图
    min_len = min(len(macd_line), len(signal_line))
    macd_val = macd_line[min_len - 1]
    signal_val = signal_line[min_len - 1]
    histogram = macd_val - signal_val

    # 判断趋势
    if histogram > 0:
        trend = "bullish"
    elif histogram < 0:
        trend = "bearish"
    else:
        trend = "neutral"

    return {
        "macd": macd_val,
        "signal": signal_val,
        "histogram": histogram,
        "trend": trend
    }