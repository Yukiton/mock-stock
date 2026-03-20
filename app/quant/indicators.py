"""综合指标计算"""

from .ma import calculate_ma
from .ema import calculate_ema
from .macd import calculate_macd
from .rsi import calculate_rsi
from .bollinger import calculate_bollinger


def calculate_all_indicators(prices: list[float]) -> dict:
    """
    计算所有指标

    Args:
        prices: 价格列表（从新到旧排序）

    Returns:
        包含所有计算结果的字典
    """
    result = {}

    # MA
    for period in [5, 10, 20, 60]:
        ma = calculate_ma(prices, period)
        if ma is not None:
            result[f"ma{period}"] = ma

    # EMA
    for period in [12, 26]:
        ema = calculate_ema(prices, period)
        if ema is not None:
            result[f"ema{period}"] = ema

    # MACD
    macd = calculate_macd(prices)
    if macd:
        result["macd"] = macd

    # RSI
    for period in [6, 14, 24]:
        rsi = calculate_rsi(prices, period)
        if rsi:
            result[f"rsi{period}"] = rsi

    # Bollinger
    boll = calculate_bollinger(prices)
    if boll:
        result["bollinger"] = boll

    return result