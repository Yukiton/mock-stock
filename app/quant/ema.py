"""指数移动平均线 (Exponential Moving Average)"""


def calculate_ema(prices: list[float], period: int) -> float | None:
    """
    计算指数移动平均线

    Args:
        prices: 价格列表（从新到旧排序）
        period: 周期

    Returns:
        EMA值，数据不足返回None
    """
    if len(prices) < period:
        return None

    multiplier = 2 / (period + 1)
    # 初始值使用SMA
    ema = sum(prices[period - 1:0:-1]) / period
    # 从旧到新迭代
    for i in range(period - 1, -1, -1):
        ema = (prices[i] - ema) * multiplier + ema

    return ema


def calculate_ema_series(prices: list[float], period: int) -> list[float]:
    """
    计算EMA序列

    Args:
        prices: 价格列表（从新到旧排序）
        period: 周期

    Returns:
        EMA序列（从新到旧排序）
    """
    if len(prices) < period:
        return []

    # 反转列表以便从旧到新计算
    reversed_prices = list(reversed(prices))
    multiplier = 2 / (period + 1)

    result = []
    # 初始SMA
    initial_sma = sum(reversed_prices[:period]) / period
    result.append(initial_sma)

    # 迭代计算EMA
    ema = initial_sma
    for price in reversed_prices[period:]:
        ema = (price - ema) * multiplier + ema
        result.append(ema)

    # 反转回从新到旧
    return list(reversed(result))