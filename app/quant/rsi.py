"""RSI指标 (Relative Strength Index)"""


def calculate_rsi(prices: list[float], period: int = 14) -> dict | None:
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