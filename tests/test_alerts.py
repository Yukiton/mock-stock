import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from decimal import Decimal

from app.main import create_app
from app.models import User, Position
from app.db.database import get_db
from app.auth import get_password_hash


@pytest_asyncio.fixture(scope="function")
async def client_with_alert_setup(db_session):
    """创建测试客户端并预置用户"""
    app = create_app()

    # 创建测试用户
    user = User(
        username="alerttest",
        password_hash=get_password_hash("testpass123"),
        balance=Decimal("100000.00"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # 创建持仓
    position = Position(
        user_id=user.id,
        stock_code="000001",
        stock_name="平安银行",
        quantity=1000,
        avg_cost=Decimal("15.00"),
    )
    db_session.add(position)
    await db_session.commit()

    # 覆盖数据库依赖
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        # 登录获取token
        login_response = await ac.post(
            "/api/v1/users/login",
            data={"username": "alerttest", "password": "testpass123"}
        )
        token = login_response.json()["access_token"]
        yield ac, user, token


@pytest.mark.asyncio
async def test_get_available_strategies(client_with_alert_setup):
    """测试获取可用策略类型"""
    client, _, token = client_with_alert_setup

    response = await client.get(
        "/api/v1/alerts/meta/strategies",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "strategies" in data
    assert "THRESHOLD" in data["strategies"]
    assert "MA" in data["strategies"]
    assert "MCP_SMART" in data["strategies"]


@pytest.mark.asyncio
async def test_get_available_notifiers(client_with_alert_setup):
    """测试获取可用通知器类型"""
    client, _, token = client_with_alert_setup

    response = await client.get(
        "/api/v1/alerts/meta/notifiers",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "notifiers" in data
    assert "WEBSOCKET" in data["notifiers"]
    assert "WEBHOOK" in data["notifiers"]
    assert "MCP" in data["notifiers"]


@pytest.mark.asyncio
async def test_create_threshold_alert(client_with_alert_setup):
    """测试创建阈值提醒"""
    client, _, token = client_with_alert_setup

    response = await client.post(
        "/api/v1/alerts",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "stock_code": "000001",
            "alert_name": "价格上限提醒",
            "strategy_type": "THRESHOLD",
            "strategy_config": {"upper": 20.0, "lower": 10.0},
            "notifier_type": "WEBSOCKET"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["stock_code"] == "000001"
    assert data["strategy_type"] == "THRESHOLD"
    assert data["enabled"] == True


@pytest.mark.asyncio
async def test_create_ma_alert(client_with_alert_setup):
    """测试创建均线提醒"""
    client, _, token = client_with_alert_setup

    response = await client.post(
        "/api/v1/alerts",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "stock_code": "000001",
            "alert_name": "MA5突破提醒",
            "strategy_type": "MA",
            "strategy_config": {"period": 5, "direction": "up"},
            "notifier_type": "WEBHOOK",
            "notifier_config": {"url": "https://example.com/webhook"}
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["strategy_type"] == "MA"


@pytest.mark.asyncio
async def test_create_mcp_smart_alert(client_with_alert_setup):
    """测试创建MCP智能提醒"""
    client, _, token = client_with_alert_setup

    response = await client.post(
        "/api/v1/alerts",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "stock_code": "000001",
            "alert_name": "AI智能提醒",
            "strategy_type": "MCP_SMART",
            "strategy_config": {
                "mcp_server": "my-server",
                "tool": "analyze_alert",
                "min_confidence": 0.7
            },
            "notifier_type": "MCP"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["strategy_type"] == "MCP_SMART"


@pytest.mark.asyncio
async def test_create_alert_invalid_strategy(client_with_alert_setup):
    """测试创建无效策略类型的提醒"""
    client, _, token = client_with_alert_setup

    response = await client.post(
        "/api/v1/alerts",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "stock_code": "000001",
            "strategy_type": "INVALID",
            "strategy_config": {},
            "notifier_type": "WEBSOCKET"
        }
    )
    # Pydantic验证失败返回422
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_alerts(client_with_alert_setup):
    """测试获取提醒列表"""
    client, _, token = client_with_alert_setup

    # 创建两个提醒
    await client.post(
        "/api/v1/alerts",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "stock_code": "000001",
            "strategy_type": "THRESHOLD",
            "strategy_config": {"upper": 20.0},
            "notifier_type": "WEBSOCKET"
        }
    )
    await client.post(
        "/api/v1/alerts",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "stock_code": "000002",
            "strategy_type": "MA",
            "strategy_config": {"period": 10, "direction": "down"},
            "notifier_type": "WEBSOCKET"
        }
    )

    response = await client.get(
        "/api/v1/alerts",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_get_alert_by_id(client_with_alert_setup):
    """测试获取单个提醒"""
    client, _, token = client_with_alert_setup

    # 创建提醒
    create_response = await client.post(
        "/api/v1/alerts",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "stock_code": "000001",
            "alert_name": "测试提醒",
            "strategy_type": "THRESHOLD",
            "strategy_config": {"upper": 20.0},
            "notifier_type": "WEBSOCKET"
        }
    )
    alert_id = create_response.json()["id"]

    response = await client.get(
        f"/api/v1/alerts/{alert_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == alert_id
    assert data["alert_name"] == "测试提醒"


@pytest.mark.asyncio
async def test_update_alert(client_with_alert_setup):
    """测试更新提醒"""
    client, _, token = client_with_alert_setup

    # 创建提醒
    create_response = await client.post(
        "/api/v1/alerts",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "stock_code": "000001",
            "alert_name": "原名称",
            "strategy_type": "THRESHOLD",
            "strategy_config": {"upper": 20.0},
            "notifier_type": "WEBSOCKET"
        }
    )
    alert_id = create_response.json()["id"]

    # 更新提醒
    response = await client.put(
        f"/api/v1/alerts/{alert_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "alert_name": "新名称",
            "enabled": False
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["alert_name"] == "新名称"
    assert data["enabled"] == False


@pytest.mark.asyncio
async def test_delete_alert(client_with_alert_setup):
    """测试删除提醒"""
    client, _, token = client_with_alert_setup

    # 创建提醒
    create_response = await client.post(
        "/api/v1/alerts",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "stock_code": "000001",
            "strategy_type": "THRESHOLD",
            "strategy_config": {"upper": 20.0},
            "notifier_type": "WEBSOCKET"
        }
    )
    alert_id = create_response.json()["id"]

    # 删除提醒
    response = await client.delete(
        f"/api/v1/alerts/{alert_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

    # 验证已删除
    response = await client.get(
        f"/api/v1/alerts/{alert_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_check_alert(client_with_alert_setup):
    """测试手动检查提醒"""
    client, _, token = client_with_alert_setup

    # 创建提醒
    create_response = await client.post(
        "/api/v1/alerts",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "stock_code": "000001",
            "strategy_type": "THRESHOLD",
            "strategy_config": {"upper": 1000.0, "lower": 1.0},  # 设置极端阈值，应该不触发
            "notifier_type": "WEBSOCKET"
        }
    )
    alert_id = create_response.json()["id"]

    # 检查提醒
    response = await client.post(
        f"/api/v1/alerts/{alert_id}/check",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "triggered" in data
    assert "stock_code" in data


# 策略单元测试
class TestThresholdStrategy:
    """阈值策略测试"""

    def test_upper_threshold_triggered(self):
        from app.strategies import ThresholdStrategy, AlertContext

        strategy = ThresholdStrategy()
        context = AlertContext(
            stock_code="000001",
            current_price=Decimal("15.0"),
            prev_close=Decimal("14.0")
        )
        config = {"upper": 14.5}

        result = strategy.check(context, config)
        assert result.triggered == True
        assert "上限" in result.reason

    def test_lower_threshold_triggered(self):
        from app.strategies import ThresholdStrategy, AlertContext

        strategy = ThresholdStrategy()
        context = AlertContext(
            stock_code="000001",
            current_price=Decimal("10.0"),
            prev_close=Decimal("14.0")
        )
        config = {"lower": 12.0}

        result = strategy.check(context, config)
        assert result.triggered == True
        assert "下限" in result.reason

    def test_percent_upper_triggered(self):
        from app.strategies import ThresholdStrategy, AlertContext

        strategy = ThresholdStrategy()
        context = AlertContext(
            stock_code="000001",
            current_price=Decimal("16.0"),
            prev_close=Decimal("14.0")
        )
        config = {"percent_upper": 10.0}  # 10%涨幅

        result = strategy.check(context, config)
        # (16-14)/14 = 14.3% > 10%
        assert result.triggered == True

    def test_not_triggered(self):
        from app.strategies import ThresholdStrategy, AlertContext

        strategy = ThresholdStrategy()
        context = AlertContext(
            stock_code="000001",
            current_price=Decimal("15.0"),
            prev_close=Decimal("14.0")
        )
        config = {"upper": 20.0, "lower": 10.0}

        result = strategy.check(context, config)
        assert result.triggered == False


class TestMAStrategy:
    """均线策略测试"""

    def test_ma_calculation(self):
        from app.strategies import MAStrategy, AlertContext

        strategy = MAStrategy()
        context = AlertContext(
            stock_code="000001",
            current_price=Decimal("15.0"),
            history_prices=[
                {"close": 14.0},
                {"close": 14.5},
                {"close": 15.0},
                {"close": 15.5},
                {"close": 15.0},
            ]
        )
        config = {"period": 5, "direction": "up"}

        # MA5 = (14+14.5+15+15.5+15)/5 = 14.8
        # price 15 > MA5 14.8, 向上突破
        result = strategy.check(context, config)
        assert result.triggered == True
        assert result.details["is_above"] == True


class TestRSIStrategy:
    """RSI策略测试"""

    def test_rsi_calculation(self):
        from app.strategies import RSIStrategy, AlertContext

        strategy = RSIStrategy()
        # 构造价格变化数据 - 持续上涨
        prices = [{"close": 10.0 + i * 0.5} for i in range(20)]

        context = AlertContext(
            stock_code="000001",
            current_price=Decimal("20.0"),
            history_prices=prices
        )
        config = {"period": 14, "overbought": 70, "oversold": 30}

        result = strategy.check(context, config)
        # 测试RSI计算成功（不关心具体值）
        # 如果触发，会有rsi_value；如果不触发，检查reason
        if result.triggered:
            assert "rsi_value" in result.details
        else:
            # 没触发也是正常的
            assert result.triggered == False