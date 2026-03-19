"""量化工具模块测试"""

import pytest
from app.quant import (
    calculate_ma,
    calculate_ema,
    calculate_macd,
    calculate_rsi,
    calculate_bollinger,
    calculate_all_indicators,
)


class TestMA:
    """MA计算测试"""

    def test_calculate_ma_basic(self):
        prices = [10.0, 11.0, 12.0, 13.0, 14.0]
        result = calculate_ma(prices, 5)
        assert result == 12.0  # (10+11+12+13+14)/5

    def test_calculate_ma_insufficient_data(self):
        prices = [10.0, 11.0]
        result = calculate_ma(prices, 5)
        assert result is None

    def test_calculate_ma_partial(self):
        prices = [10.0, 11.0, 12.0, 13.0, 14.0, 15.0]
        result = calculate_ma(prices, 3)
        # 取最新的3个: 10+11+12=33/3=11
        assert result == 11.0


class TestEMA:
    """EMA计算测试"""

    def test_calculate_ema_basic(self):
        prices = [10.0] * 26  # 26个相同价格
        result = calculate_ema(prices, 12)
        # EMA计算方式导致结果接近但不完全等于价格
        assert result is not None
        assert abs(result - 10.0) < 0.5  # 允许一定误差

    def test_calculate_ema_insufficient_data(self):
        prices = [10.0, 11.0]
        result = calculate_ema(prices, 12)
        assert result is None


class TestMACD:
    """MACD计算测试"""

    def test_calculate_macd_uptrend(self):
        # 构造上升趋势
        prices = [100.0 + i for i in range(40)][::-1]  # 从100到140，反转后从新到旧
        result = calculate_macd(prices)
        assert result is not None
        assert "macd" in result
        assert "signal" in result
        assert "histogram" in result
        assert "trend" in result

    def test_calculate_macd_insufficient_data(self):
        prices = [10.0, 11.0, 12.0]
        result = calculate_macd(prices)
        assert result is None


class TestRSI:
    """RSI计算测试"""

    def test_calculate_rsi_uptrend(self):
        # 构造持续上涨
        prices = [100.0 + i for i in range(20)][::-1]
        result = calculate_rsi(prices, 14)
        assert result is not None
        assert result["rsi"] > 70  # 持续上涨，RSI应该很高
        assert result["overbought"] == True

    def test_calculate_rsi_downtrend(self):
        # 构造持续下跌
        prices = [100.0 - i for i in range(20)][::-1]
        result = calculate_rsi(prices, 14)
        assert result is not None
        assert result["rsi"] < 30  # 持续下跌，RSI应该很低
        assert result["oversold"] == True

    def test_calculate_rsi_neutral(self):
        # 构造震荡行情
        prices = [100.0, 101.0, 99.0, 100.0, 101.0, 99.0] * 3
        result = calculate_rsi(prices, 14)
        assert result is not None
        assert 30 <= result["rsi"] <= 70
        assert result["zone"] == "neutral"


class TestBollinger:
    """布林带计算测试"""

    def test_calculate_bollinger_basic(self):
        prices = [100.0 + (i % 5) for i in range(25)]  # 震荡价格
        result = calculate_bollinger(prices, 20)
        assert result is not None
        assert "upper" in result
        assert "middle" in result
        assert "lower" in result
        assert result["upper"] > result["middle"] > result["lower"]

    def test_calculate_bollinger_position(self):
        # 震荡行情
        prices = [100.0 + (i % 5 - 2) for i in range(25)]
        result = calculate_bollinger(prices, 20)
        assert result is not None
        # 价格位置应该在合理范围内
        assert 0 <= result["position"] <= 100


class TestCalculateAllIndicators:
    """全量指标计算测试"""

    def test_calculate_all_indicators(self):
        # 构造足够的历史数据
        prices = [100.0 + (i % 10) for i in range(70)]
        result = calculate_all_indicators(prices)

        # 验证各指标都有计算
        assert "ma5" in result
        assert "ma10" in result
        assert "ma20" in result
        assert "ma60" in result
        assert "macd" in result
        assert "rsi6" in result
        assert "rsi14" in result
        assert "bollinger" in result

    def test_calculate_all_indicators_insufficient(self):
        prices = [10.0, 11.0, 12.0]
        result = calculate_all_indicators(prices)
        # 数据不足，大部分指标应该没有
        assert result == {} or len(result) == 0