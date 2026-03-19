"""执行器测试"""

import pytest
from decimal import Decimal

from app.executors import (
    AutoTradeExecutor,
    WebSocketExecutor,
    WebhookExecutor,
    ExecutionRequest,
    ExecutionResult,
    get_executor,
    list_executors,
)


class TestAutoTradeExecutor:
    """自动交易执行器测试"""

    def test_executor_type(self):
        executor = AutoTradeExecutor()
        assert executor.executor_type == "AUTO_TRADE"

    @pytest.mark.asyncio
    async def test_execute_buy(self):
        executor = AutoTradeExecutor()
        request = ExecutionRequest(
            user_id=1,
            stock_code="000001",
            action="BUY",
            quantity=100,
            price=Decimal("15.0"),
            reason="MA5突破"
        )
        result = await executor.execute(request, {})
        assert result.success == True
        assert result.action == "BUY"
        assert result.details.get("requires_trade") == True

    @pytest.mark.asyncio
    async def test_execute_sell(self):
        executor = AutoTradeExecutor()
        request = ExecutionRequest(
            user_id=1,
            stock_code="000001",
            action="SELL",
            quantity=100,
            price=Decimal("15.0"),
            reason="RSI超买"
        )
        result = await executor.execute(request, {})
        assert result.success == True
        assert result.action == "SELL"

    @pytest.mark.asyncio
    async def test_execute_notify_not_supported(self):
        executor = AutoTradeExecutor()
        request = ExecutionRequest(
            user_id=1,
            stock_code="000001",
            action="NOTIFY",
            reason="通知"
        )
        result = await executor.execute(request, {})
        assert result.success == False

    @pytest.mark.asyncio
    async def test_dry_run_mode(self):
        executor = AutoTradeExecutor()
        request = ExecutionRequest(
            user_id=1,
            stock_code="000001",
            action="BUY",
            quantity=100,
            price=Decimal("15.0"),
            reason="测试"
        )
        result = await executor.execute(request, {"dry_run": True})
        assert result.success == True
        assert result.details.get("dry_run") == True

    @pytest.mark.asyncio
    async def test_max_quantity_limit(self):
        executor = AutoTradeExecutor()
        request = ExecutionRequest(
            user_id=1,
            stock_code="000001",
            action="BUY",
            quantity=100000,  # 超过默认限制
            price=Decimal("15.0"),
            reason="测试"
        )
        result = await executor.execute(request, {"max_quantity": 1000})
        assert result.success == False


class TestWebSocketExecutor:
    """WebSocket执行器测试"""

    def test_executor_type(self):
        executor = WebSocketExecutor()
        assert executor.executor_type == "WEBSOCKET"

    @pytest.mark.asyncio
    async def test_execute_no_connection(self):
        executor = WebSocketExecutor()
        request = ExecutionRequest(
            user_id=999,  # 不存在的用户
            stock_code="000001",
            action="NOTIFY",
            reason="测试"
        )
        result = await executor.execute(request, {})
        assert result.success == False


class TestWebhookExecutor:
    """Webhook执行器测试"""

    def test_executor_type(self):
        executor = WebhookExecutor()
        assert executor.executor_type == "WEBHOOK"

    @pytest.mark.asyncio
    async def test_execute_no_url(self):
        executor = WebhookExecutor()
        request = ExecutionRequest(
            user_id=1,
            stock_code="000001",
            action="NOTIFY",
            reason="测试"
        )
        result = await executor.execute(request, {})
        assert result.success == False
        assert "URL" in result.message

    @pytest.mark.asyncio
    async def test_test_connection_no_url(self):
        executor = WebhookExecutor()
        result = await executor.test_connection({})
        assert result == False


class TestExecutorRegistry:
    """执行器注册表测试"""

    def test_list_executors(self):
        executors = list_executors()
        assert "AUTO_TRADE" in executors
        assert "WEBSOCKET" in executors
        assert "WEBHOOK" in executors

    def test_get_executor(self):
        executor = get_executor("AUTO_TRADE")
        assert executor is not None
        assert executor.executor_type == "AUTO_TRADE"

    def test_get_executor_invalid(self):
        executor = get_executor("INVALID")
        assert executor is None


class TestExecutionRequest:
    """执行请求测试"""

    def test_create_request(self):
        request = ExecutionRequest(
            user_id=1,
            stock_code="000001",
            action="BUY",
            quantity=100,
            price=Decimal("15.0"),
            reason="MA5突破"
        )
        assert request.user_id == 1
        assert request.stock_code == "000001"
        assert request.action == "BUY"
        assert request.quantity == 100


class TestExecutionResult:
    """执行结果测试"""

    def test_create_result(self):
        result = ExecutionResult(
            success=True,
            action="BUY",
            message="买入成功",
            details={"transaction_id": 1}
        )
        assert result.success == True
        assert result.action == "BUY"
        assert result.details.get("transaction_id") == 1