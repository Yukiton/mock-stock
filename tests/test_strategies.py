"""策略测试 - 重构后的统一测试"""

import pytest
from decimal import Decimal

from app.strategies import (
    AlertStrategy,
    AlertContext,
    CheckResult,
    ThresholdStrategy,
    MAStrategy,
    MACDStrategy,
    RSIStrategy,
    MCPSmartStrategy,
)


class TestThresholdStrategy:
    """阈值策略测试"""

    def test_strategy_type(self):
        strategy = ThresholdStrategy()
        assert strategy.strategy_type == "THRESHOLD"

    @pytest.mark.asyncio
    async def test_upper_threshold_triggered(self):
        strategy = ThresholdStrategy()
        context = AlertContext(
            stock_code="000001",
            current_price=Decimal("15.0"),
            prev_close=Decimal("14.0")
        )
        config = {"upper": 14.5}

        result = await strategy.check(context, config)
        assert result.triggered == True
        assert "上限" in result.reason or "触及" in result.reason
        assert result.suggested_action == "SELL"

    @pytest.mark.asyncio
    async def test_lower_threshold_triggered(self):
        strategy = ThresholdStrategy()
        context = AlertContext(
            stock_code="000001",
            current_price=Decimal("10.0"),
            prev_close=Decimal("14.0")
        )
        config = {"lower": 12.0}

        result = await strategy.check(context, config)
        assert result.triggered == True
        assert "下限" in result.reason
        assert result.suggested_action == "BUY"

    @pytest.mark.asyncio
    async def test_percent_upper_triggered(self):
        strategy = ThresholdStrategy()
        context = AlertContext(
            stock_code="000001",
            current_price=Decimal("16.0"),
            prev_close=Decimal("14.0")
        )
        config = {"percent_upper": 10.0}

        result = await strategy.check(context, config)
        assert result.triggered == True
        assert result.suggested_action == "SELL"

    @pytest.mark.asyncio
    async def test_not_triggered(self):
        strategy = ThresholdStrategy()
        context = AlertContext(
            stock_code="000001",
            current_price=Decimal("15.0"),
            prev_close=Decimal("14.0")
        )
        config = {"upper": 20.0, "lower": 10.0}

        result = await strategy.check(context, config)
        assert result.triggered == False

    @pytest.mark.asyncio
    async def test_custom_action(self):
        strategy = ThresholdStrategy()
        context = AlertContext(
            stock_code="000001",
            current_price=Decimal("15.0"),
            prev_close=Decimal("14.0")
        )
        config = {"upper": 14.5, "action_on_upper": "NOTIFY"}

        result = await strategy.check(context, config)
        assert result.triggered == True
        assert result.suggested_action == "NOTIFY"


class TestMAStrategy:
    """均线策略测试"""

    @pytest.mark.asyncio
    async def test_ma_up_breakout(self):
        strategy = MAStrategy()
        context = AlertContext(
            stock_code="000001",
            current_price=Decimal("15.0"),
            indicators={"ma5": 14.5}
        )
        config = {"period": 5, "direction": "up"}

        result = await strategy.check(context, config)
        assert result.triggered == True
        assert result.suggested_action == "BUY"

    @pytest.mark.asyncio
    async def test_ma_down_breakout(self):
        strategy = MAStrategy()
        context = AlertContext(
            stock_code="000001",
            current_price=Decimal("14.0"),
            indicators={"ma5": 15.0}
        )
        config = {"period": 5, "direction": "down"}

        result = await strategy.check(context, config)
        assert result.triggered == True
        assert result.suggested_action == "SELL"

    @pytest.mark.asyncio
    async def test_ma_insufficient_data(self):
        strategy = MAStrategy()
        context = AlertContext(
            stock_code="000001",
            current_price=Decimal("15.0"),
            indicators={},
            history_prices=[]
        )
        config = {"period": 5}

        result = await strategy.check(context, config)
        assert result.triggered == False
        assert "不足" in result.reason or "无法" in result.reason


class TestMACDStrategy:
    """MACD策略测试"""

    @pytest.mark.asyncio
    async def test_golden_cross(self):
        strategy = MACDStrategy()
        context = AlertContext(
            stock_code="000001",
            current_price=Decimal("15.0"),
            indicators={"macd": {"macd": 0.1, "signal": 0.05, "histogram": 0.05}}
        )
        config = {"type": "golden_cross"}

        result = await strategy.check(context, config)
        assert result.triggered == True
        assert result.suggested_action == "BUY"

    @pytest.mark.asyncio
    async def test_death_cross(self):
        strategy = MACDStrategy()
        context = AlertContext(
            stock_code="000001",
            current_price=Decimal("15.0"),
            indicators={"macd": {"macd": -0.1, "signal": -0.05, "histogram": -0.05}}
        )
        config = {"type": "death_cross"}

        result = await strategy.check(context, config)
        assert result.triggered == True
        assert result.suggested_action == "SELL"


class TestRSIStrategy:
    """RSI策略测试"""

    @pytest.mark.asyncio
    async def test_overbought(self):
        strategy = RSIStrategy()
        context = AlertContext(
            stock_code="000001",
            current_price=Decimal("15.0"),
            indicators={"rsi14": 75.0}
        )
        config = {"period": 14}

        result = await strategy.check(context, config)
        assert result.triggered == True
        assert result.suggested_action == "SELL"

    @pytest.mark.asyncio
    async def test_oversold(self):
        strategy = RSIStrategy()
        context = AlertContext(
            stock_code="000001",
            current_price=Decimal("15.0"),
            indicators={"rsi14": 25.0}
        )
        config = {"period": 14}

        result = await strategy.check(context, config)
        assert result.triggered == True
        assert result.suggested_action == "BUY"


class TestMCPSmartStrategy:
    """MCP智能策略测试"""

    def test_strategy_type(self):
        strategy = MCPSmartStrategy()
        assert strategy.strategy_type == "MCP_SMART"

    @pytest.mark.asyncio
    async def test_mock_ai_response_overbought(self):
        """测试模拟AI响应（超买）"""
        strategy = MCPSmartStrategy()
        context = AlertContext(
            stock_code="000001",
            current_price=Decimal("15.0"),
            indicators={
                "rsi14_rsi": 75.0,
                "rsi14_zone": "overbought"
            }
        )
        config = {"min_confidence": 0.5}

        result = await strategy.check(context, config)
        # 模拟响应应该返回超买信号
        assert result.triggered == True
        assert result.suggested_action == "SELL"
        assert result.details.get("ai_analysis") == True

    @pytest.mark.asyncio
    async def test_mock_ai_response_oversold(self):
        """测试模拟AI响应（超卖）"""
        strategy = MCPSmartStrategy()
        context = AlertContext(
            stock_code="000001",
            current_price=Decimal("10.0"),
            indicators={
                "rsi14_rsi": 25.0,
                "rsi14_zone": "oversold"
            }
        )
        config = {"min_confidence": 0.5}

        result = await strategy.check(context, config)
        assert result.triggered == True
        assert result.suggested_action == "BUY"

    @pytest.mark.asyncio
    async def test_custom_ai_client(self):
        """测试自定义AI客户端"""

        async def mock_ai_client(ai_context: dict) -> dict:
            return {
                "should_alert": True,
                "confidence": 0.9,
                "reason": "自定义AI决策",
                "suggested_action": "BUY",
                "suggested_quantity": 200,
                "suggested_price": 15.5
            }

        strategy = MCPSmartStrategy()
        context = AlertContext(
            stock_code="000001",
            current_price=Decimal("15.0"),
            indicators={}
        )
        config = {"ai_client": mock_ai_client, "min_confidence": 0.8}

        result = await strategy.check(context, config)
        assert result.triggered == True
        assert result.reason == "自定义AI决策"
        assert result.suggested_action == "BUY"
        assert result.suggested_quantity == 200
        assert result.suggested_price == Decimal("15.5")

    @pytest.mark.asyncio
    async def test_confidence_threshold(self):
        """测试置信度阈值"""

        async def low_confidence_client(ai_context: dict) -> dict:
            return {
                "should_alert": True,
                "confidence": 0.5,
                "reason": "置信度较低的信号",
                "suggested_action": "BUY"
            }

        strategy = MCPSmartStrategy()
        context = AlertContext(
            stock_code="000001",
            current_price=Decimal("15.0"),
            indicators={}
        )
        config = {"ai_client": low_confidence_client, "min_confidence": 0.8}

        result = await strategy.check(context, config)
        # 置信度不足，应该不触发
        assert result.triggered == False
        assert "置信度不足" in result.reason

    @pytest.mark.asyncio
    async def test_hold_action(self):
        """测试HOLD动作"""

        async def hold_client(ai_context: dict) -> dict:
            return {
                "should_alert": False,
                "confidence": 0.9,
                "reason": "暂无明确信号",
                "suggested_action": "HOLD"
            }

        strategy = MCPSmartStrategy()
        context = AlertContext(
            stock_code="000001",
            current_price=Decimal("15.0"),
            indicators={}
        )
        config = {"ai_client": hold_client}

        result = await strategy.check(context, config)
        assert result.triggered == False
        assert result.suggested_action == "HOLD"

    @pytest.mark.asyncio
    async def test_ai_context_building(self):
        """测试AI上下文构建"""
        strategy = MCPSmartStrategy()
        context = AlertContext(
            stock_code="000001",
            current_price=Decimal("15.0"),
            open_price=Decimal("14.5"),
            high_price=Decimal("15.5"),
            low_price=Decimal("14.0"),
            prev_close=Decimal("14.2"),
            volume=1000000,
            position_quantity=1000,
            position_avg_cost=Decimal("13.0"),
            indicators={"ma5": 14.5, "rsi14_rsi": 60.0}
        )
        config = {}

        ai_context = strategy._build_ai_context(context, config)

        assert ai_context["stock_code"] == "000001"
        assert "当前价格" in ai_context["data"]
        assert "持仓数量" in ai_context["data"]
        assert "量化指标" in ai_context["data"]

    @pytest.mark.asyncio
    async def test_ai_client_exception(self):
        """测试AI客户端异常处理"""

        async def failing_client(ai_context: dict) -> dict:
            raise Exception("AI服务不可用")

        strategy = MCPSmartStrategy()
        context = AlertContext(
            stock_code="000001",
            current_price=Decimal("15.0"),
            indicators={}
        )
        config = {"ai_client": failing_client}

        result = await strategy.check(context, config)
        assert result.triggered == False
        assert "AI调用失败" in result.reason


class TestCheckResult:
    """CheckResult测试"""

    def test_create_result(self):
        result = CheckResult(
            triggered=True,
            reason="价格突破",
            suggested_action="BUY",
            suggested_quantity=100,
            suggested_price=Decimal("15.0"),
            details={"test": "value"}
        )
        assert result.triggered == True
        assert result.suggested_action == "BUY"
        assert result.suggested_quantity == 100
        assert result.suggested_price == Decimal("15.0")

    def test_default_values(self):
        result = CheckResult(triggered=False)
        assert result.reason is None
        assert result.suggested_action == "NOTIFY"
        assert result.suggested_quantity is None
        assert result.suggested_price is None
        assert result.details == {}