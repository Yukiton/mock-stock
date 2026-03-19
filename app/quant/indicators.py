"""量化指标计算工具

独立的量化计算模块，可被：
1. 策略调用进行指标计算
2. AlertService构建上下文时调用
3. MCP智能策略调用获取指标结果
"""

from typing import Optional
from decimal import Decimal
import math


def calculate_ma(prices: list[float], period: int) -> Optional[float]:
    """
    计算简单移动平均线 (Simple Moving Average)

    Args:
        prices: 价格列表（从新到旧排序）
        period: 周期

    Returns:
        MA值，数据不足返回None
    """
    if len(prices) < period:
        return None
    return sum(prices[:period]) / period


def calculate_ema(prices: list[float], period: int) -> Optional[float]:
    """
    计算指数移动平均线 (Exponential Moving Average)

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
    ema = sum(prices[period - 1:0:-1]) / period  # 从最旧的period个计算SMA
    # 从旧到新迭代
    for i in range(period - 1, -1, -1):
        ema = (prices[i] - ema) * multiplier + ema

    return ema


def calculate_macd(
    prices: list[float],
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> Optional[dict]:
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
    fast_ema = _calculate_ema_series(prices, fast_period)
    slow_ema = _calculate_ema_series(prices, slow_period)

    if not fast_ema or not slow_ema:
        return None

    # 对齐长度
    min_len = min(len(fast_ema), len(slow_ema))
    fast_ema = fast_ema[:min_len]
    slow_ema = slow_ema[:min_len]

    # MACD线 = 快线 - 慢线
    macd_line = [f - s for f, s in zip(fast_ema, slow_ema)]

    # 信号线 = MACD的EMA
    signal_line = _calculate_ema_series(macd_line, signal_period)

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


def calculate_rsi(prices: list[float], period: int = 14) -> Optional[dict]:
    """
    计算RSI指标

    Args:
        prices: 价格列表（从新到旧排序）
        period: 周期

    Returns:
        {
            "rsi": RSI值,
            "overbought": 是否超买,
            "oversold": 是否超卖,
            "zone": "overbought" | "oversold" | "neutral"
        }
        数据不足返回None
    """
    if len(prices) < period + 1:
        return None

    # 计算价格变化
    changes = []
    for i in range(len(prices) - 1):
        changes.append(prices[i] - prices[i + 1])

    if len(changes) < period:
        return None

    # 取最近period个变化
    recent_changes = changes[:period]
    gains = [c for c in recent_changes if c > 0]
    losses = [-c for c in recent_changes if c < 0]

    avg_gain = sum(gains) / period if gains else 0
    avg_loss = sum(losses) / period if losses else 0

    if avg_loss == 0:
        rsi = 100.0
    else:
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

    # 判断区域
    overbought = rsi >= 70
    oversold = rsi <= 30

    if overbought:
        zone = "overbought"
    elif oversold:
        zone = "oversold"
    else:
        zone = "neutral"

    return {
        "rsi": rsi,
        "overbought": overbought,
        "oversold": oversold,
        "zone": zone
    }


def calculate_bollinger(
    prices: list[float],
    period: int = 20,
    std_dev: float = 2.0
) -> Optional[dict]:
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


def _calculate_ema_series(prices: list[float], period: int) -> list[float]:
    """
    计算EMA序列（内部使用）

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