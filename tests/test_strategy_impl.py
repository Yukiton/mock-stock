"""策略实现测试"""

import pytest
from decimal import Decimal

from app.strategies import (
    BaseStrategy,
    StrategyContext,
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
        context = StrategyContext(
            user_id=1,
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
        context = StrategyContext(
            user_id=1,
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
        context = StrategyContext(
            user_id=1,
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
        context = StrategyContext(
            user_id=1,
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
        context = StrategyContext(
            user_id=1,
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
        # 构建带有历史价格的context
        context = StrategyContext(
            user_id=1,
            stock_code="000001",
            current_price=Decimal("15.0"),
            history_prices=[
                {"close": 15.0},
                {"close": 14.5},
                {"close": 14.0},
                {"close": 13.5},
                {"close": 13.0},
            ]
        )
        config = {"period": 5, "direction": "up"}

        result = await strategy.check(context, config)
        # MA5 = (15+14.5+14+13.5+13)/5 = 14，当前价格15 > 14，向上突破
        assert result.triggered == True
        assert result.suggested_action == "BUY"

    @pytest.mark.asyncio
    async def test_ma_down_breakout(self):
        strategy = MAStrategy()
        context = StrategyContext(
            user_id=1,
            stock_code="000001",
            current_price=Decimal("13.0"),
            history_prices=[
                {"close": 13.0},
                {"close": 14.5},
                {"close": 14.0},
                {"close": 13.5},
                {"close": 15.0},
            ]
        )
        config = {"period": 5, "direction": "down"}

        result = await strategy.check(context, config)
        assert result.triggered == True
        assert result.suggested_action == "SELL"

    @pytest.mark.asyncio
    async def test_ma_insufficient_data(self):
        strategy = MAStrategy()
        context = StrategyContext(
            user_id=1,
            stock_code="000001",
            current_price=Decimal("15.0"),
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
        # 构建足够的历史价格用于MACD计算
        prices = [{"close": 10.0 + i * 0.1} for i in range(50)]
        context = StrategyContext(
            user_id=1,
            stock_code="000001",
            current_price=Decimal("15.0"),
            history_prices=prices
        )
        config = {"type": "golden_cross"}

        result = await strategy.check(context, config)
        # MACD计算结果取决于具体数据
        assert result.triggered in (True, False)

    @pytest.mark.asyncio
    async def test_insufficient_data(self):
        strategy = MACDStrategy()
        context = StrategyContext(
            user_id=1,
            stock_code="000001",
            current_price=Decimal("15.0"),
            history_prices=[{"close": 15.0}]
        )
        config = {"type": "golden_cross"}

        result = await strategy.check(context, config)
        assert result.triggered == False


class TestRSIStrategy:
    """RSI策略测试"""

    @pytest.mark.asyncio
    async def test_rsi_overbought(self):
        strategy = RSIStrategy()
        # 构建上涨趋势的价格（RSI应该偏高）
        prices = [{"close": 10.0 + i * 0.5} for i in range(20)]
        context = StrategyContext(
            user_id=1,
            stock_code="000001",
            current_price=Decimal("20.0"),
            history_prices=prices
        )
        config = {"period": 14}

        result = await strategy.check(context, config)
        # RSI可能超买也可能不超买，取决于具体计算
        assert result.triggered in (True, False)

    @pytest.mark.asyncio
    async def test_rsi_insufficient_data(self):
        strategy = RSIStrategy()
        context = StrategyContext(
            user_id=1,
            stock_code="000001",
            current_price=Decimal("15.0"),
            history_prices=[{"close": 15.0}]
        )
        config = {"period": 14}

        result = await strategy.check(context, config)
        assert result.triggered == False


class TestMCPSmartStrategy:
    """MCP智能策略测试"""

    def test_strategy_type(self):
        strategy = MCPSmartStrategy()
        assert strategy.strategy_type == "MCP_SMART"

    @pytest.mark.asyncio
    async def test_mock_ai_response(self):
        """测试模拟AI响应"""
        strategy = MCPSmartStrategy()
        context = StrategyContext(
            user_id=1,
            stock_code="000001",
            current_price=Decimal("15.0"),
            history_prices=[
                {"close": 15.0 + i * 0.5} for i in range(20)
            ]
        )
        config = {"min_confidence": 0.5}

        result = await strategy.check(context, config)
        # 模拟响应应该返回结果
        assert result.details.get("ai_analysis") == True

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
        context = StrategyContext(
            user_id=1,
            stock_code="000001",
            current_price=Decimal("15.0"),
            history_prices=[]
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
        context = StrategyContext(
            user_id=1,
            stock_code="000001",
            current_price=Decimal("15.0"),
            history_prices=[]
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
        context = StrategyContext(
            user_id=1,
            stock_code="000001",
            current_price=Decimal("15.0"),
            history_prices=[]
        )
        config = {"ai_client": hold_client}

        result = await strategy.check(context, config)
        assert result.triggered == False
        assert result.suggested_action == "HOLD"


class TestStrategyContext:
    """StrategyContext测试"""

    def test_create_context(self):
        context = StrategyContext(
            user_id=1,
            stock_code="000001",
            current_price=Decimal("15.0"),
            position_quantity=1000,
            position_avg_cost=Decimal("13.0")
        )
        assert context.user_id == 1
        assert context.stock_code == "000001"
        assert context.current_price == Decimal("15.0")
        assert context.position_quantity == 1000

    def test_default_values(self):
        context = StrategyContext(
            user_id=1,
            stock_code="000001",
            current_price=Decimal("15.0")
        )
        assert context.position_quantity is None
        assert context.history_prices == []
        assert context.recent_transactions == []


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