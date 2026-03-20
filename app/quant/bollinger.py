"""布林带指标 (Bollinger Bands)"""

import math


def calculate_bollinger(
    prices: list[float],
    period: int = 20,
    std_dev: float = 2.0
) -> dict | None:
    """
    计算布林带指标

    Args:
        prices: 价格列表（从新到旧排序）
        period: 周期
        std_dev: 标准差倍数

    Returns:
        {
            "middle": 中轨(MA),
            "upper": 上轨,
            "lower": 下轨,
            "bandwidth": 带宽,
            "position": 价格位置百分比
        }
        数据不足返回None
    """
    if len(prices) < period:
        return None

    # 中轨 = MA
    recent_prices = prices[:period]
    middle = sum(recent_prices) / period

    # 标准差
    variance = sum((p - middle) ** 2 for p in recent_prices) / period
    std = math.sqrt(variance)

    # 上下轨
    upper = middle + std_dev * std
    lower = middle - std_dev * std

    # 带宽
    bandwidth = (upper - lower) / middle * 100 if middle != 0 else 0

    # 价格位置（当前价在布林带中的位置）
    current_price = prices[0]
    if upper != lower:
        position = (current_price - lower) / (upper - lower) * 100
    else:
        position = 50.0

    return {
        "middle": middle,
        "upper": upper,
        "lower": lower,
        "bandwidth": bandwidth,
        "position": position
    }