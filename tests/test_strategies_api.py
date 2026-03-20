"""策略 API 测试"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from decimal import Decimal

from app.main import create_app
from app.models import User, Position
from app.db.database import get_db
from app.auth import get_password_hash


@pytest_asyncio.fixture(scope="function")
async def client_with_strategy_setup(db_session):
    """创建测试客户端并预置用户"""
    app = create_app()

    # 创建测试用户
    user = User(
        username="strategytest",
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
            data={"username": "strategytest", "password": "testpass123"}
        )
        token = login_response.json()["access_token"]
        yield ac, user, token


@pytest.mark.asyncio
async def test_get_available_strategies(client_with_strategy_setup):
    """测试获取可用策略类型"""
    client, _, token = client_with_strategy_setup

    response = await client.get(
        "/api/v1/strategies/meta/types",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "strategies" in data
    assert "THRESHOLD" in data["strategies"]
    assert "MA" in data["strategies"]
    assert "MCP_SMART" in data["strategies"]


@pytest.mark.asyncio
async def test_get_available_executors(client_with_strategy_setup):
    """测试获取可用执行器类型"""
    client, _, token = client_with_strategy_setup

    response = await client.get(
        "/api/v1/strategies/meta/executors",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "executors" in data
    assert "AUTO_TRADE" in data["executors"]
    assert "WEBSOCKET" in data["executors"]
    assert "WEBHOOK" in data["executors"]


@pytest.mark.asyncio
async def test_create_threshold_strategy(client_with_strategy_setup):
    """测试创建阈值策略"""
    client, _, token = client_with_strategy_setup

    response = await client.post(
        "/api/v1/strategies",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "stock_code": "000001",
            "strategy_name": "价格上限策略",
            "strategy_type": "THRESHOLD",
            "strategy_config": {"upper": 20.0, "lower": 10.0},
            "executor_type": "WEBSOCKET"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["stock_code"] == "000001"
    assert data["strategy_type"] == "THRESHOLD"
    assert data["enabled"] == True


@pytest.mark.asyncio
async def test_create_ma_strategy(client_with_strategy_setup):
    """测试创建均线策略"""
    client, _, token = client_with_strategy_setup

    response = await client.post(
        "/api/v1/strategies",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "stock_code": "000001",
            "strategy_name": "MA5突破策略",
            "strategy_type": "MA",
            "strategy_config": {"period": 5, "direction": "up"},
            "executor_type": "WEBHOOK",
            "executor_config": {"url": "https://example.com/webhook"}
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["strategy_type"] == "MA"


@pytest.mark.asyncio
async def test_create_mcp_smart_strategy(client_with_strategy_setup):
    """测试创建MCP智能策略"""
    client, _, token = client_with_strategy_setup

    response = await client.post(
        "/api/v1/strategies",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "stock_code": "000001",
            "strategy_name": "AI智能策略",
            "strategy_type": "MCP_SMART",
            "strategy_config": {
                "min_confidence": 0.7
            },
            "executor_type": "AUTO_TRADE"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["strategy_type"] == "MCP_SMART"


@pytest.mark.asyncio
async def test_create_strategy_invalid_type(client_with_strategy_setup):
    """测试创建无效策略类型"""
    client, _, token = client_with_strategy_setup

    response = await client.post(
        "/api/v1/strategies",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "stock_code": "000001",
            "strategy_type": "INVALID",
            "strategy_config": {},
            "executor_type": "WEBSOCKET"
        }
    )
    # 无效策略类型会被API返回400或Pydantic验证返回422
    assert response.status_code in (400, 422)


@pytest.mark.asyncio
async def test_get_strategies(client_with_strategy_setup):
    """测试获取策略列表"""
    client, _, token = client_with_strategy_setup

    # 创建两个策略
    await client.post(
        "/api/v1/strategies",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "stock_code": "000001",
            "strategy_type": "THRESHOLD",
            "strategy_config": {"upper": 20.0},
            "executor_type": "WEBSOCKET"
        }
    )
    await client.post(
        "/api/v1/strategies",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "stock_code": "000002",
            "strategy_type": "MA",
            "strategy_config": {"period": 10, "direction": "down"},
            "executor_type": "WEBSOCKET"
        }
    )

    response = await client.get(
        "/api/v1/strategies",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_get_strategy_by_id(client_with_strategy_setup):
    """测试获取单个策略"""
    client, _, token = client_with_strategy_setup

    # 创建策略
    create_response = await client.post(
        "/api/v1/strategies",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "stock_code": "000001",
            "strategy_name": "测试策略",
            "strategy_type": "THRESHOLD",
            "strategy_config": {"upper": 20.0},
            "executor_type": "WEBSOCKET"
        }
    )
    strategy_id = create_response.json()["id"]

    response = await client.get(
        f"/api/v1/strategies/{strategy_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == strategy_id
    assert data["strategy_name"] == "测试策略"


@pytest.mark.asyncio
async def test_update_strategy(client_with_strategy_setup):
    """测试更新策略"""
    client, _, token = client_with_strategy_setup

    # 创建策略
    create_response = await client.post(
        "/api/v1/strategies",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "stock_code": "000001",
            "strategy_name": "原名称",
            "strategy_type": "THRESHOLD",
            "strategy_config": {"upper": 20.0},
            "executor_type": "WEBSOCKET"
        }
    )
    strategy_id = create_response.json()["id"]

    # 更新策略
    response = await client.put(
        f"/api/v1/strategies/{strategy_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "strategy_name": "新名称",
            "enabled": False
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["strategy_name"] == "新名称"
    assert data["enabled"] == False


@pytest.mark.asyncio
async def test_delete_strategy(client_with_strategy_setup):
    """测试删除策略"""
    client, _, token = client_with_strategy_setup

    # 创建策略
    create_response = await client.post(
        "/api/v1/strategies",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "stock_code": "000001",
            "strategy_type": "THRESHOLD",
            "strategy_config": {"upper": 20.0},
            "executor_type": "WEBSOCKET"
        }
    )
    strategy_id = create_response.json()["id"]

    # 删除策略
    response = await client.delete(
        f"/api/v1/strategies/{strategy_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

    # 验证已删除
    response = await client.get(
        f"/api/v1/strategies/{strategy_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404