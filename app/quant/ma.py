"""简单移动平均线 (Simple Moving Average)"""


def calculate_ma(prices: list[float], period: int) -> float | None:
    """
    计算简单移动平均线

    Args:
        prices: 价格列表（从新到旧排序）
        period: 周期

    Returns:
        MA值，数据不足返回None
    """
    if len(prices) < period:
        return None
    return sum(prices[:period]) / period