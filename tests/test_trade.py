import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from decimal import Decimal

from app.main import create_app
from app.models import User, Position
from app.db.database import get_db
from app.auth import get_password_hash


@pytest_asyncio.fixture(scope="function")
async def client_with_trade_setup(db_session):
    """创建测试客户端并预置用户"""
    app = create_app()

    # 创建测试用户，初始余额 100000
    user = User(
        username="tradetest",
        password_hash=get_password_hash("testpass123"),
        balance=Decimal("100000.00"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

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
            data={"username": "tradetest", "password": "testpass123"}
        )
        token = login_response.json()["access_token"]
        yield ac, user, token


@pytest.mark.asyncio
async def test_buy_stock_success(client_with_trade_setup):
    """测试买入股票成功"""
    client, user, token = client_with_trade_setup

    response = await client.post(
        "/api/v1/trade/buy",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "stock_code": "000001",
            "quantity": 1000,
            "price": "15.00"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["transaction"]["stock_code"] == "000001"
    assert data["transaction"]["type"] == "BUY"
    assert data["transaction"]["quantity"] == 1000
    assert float(data["transaction"]["price"]) == 15.00
    assert float(data["transaction"]["amount"]) == 15000.00
    assert float(data["balance"]) == 85000.00  # 100000 - 15000
    assert data["position_quantity"] == 1000


@pytest.mark.asyncio
async def test_buy_stock_insufficient_balance(client_with_trade_setup):
    """测试买入股票余额不足"""
    client, user, token = client_with_trade_setup

    response = await client.post(
        "/api/v1/trade/buy",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "stock_code": "000001",
            "quantity": 10000,
            "price": "15.00"
        }
    )
    assert response.status_code == 400
    assert "不足" in response.json()["detail"]


@pytest.mark.asyncio
async def test_buy_stock_multiple_times(client_with_trade_setup):
    """测试多次买入同一股票（成本均价）"""
    client, user, token = client_with_trade_setup

    # 第一次买入
    await client.post(
        "/api/v1/trade/buy",
        headers={"Authorization": f"Bearer {token}"},
        json={"stock_code": "000001", "quantity": 100, "price": "10.00"}
    )

    # 第二次买入
    response = await client.post(
        "/api/v1/trade/buy",
        headers={"Authorization": f"Bearer {token}"},
        json={"stock_code": "000001", "quantity": 100, "price": "20.00"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["position_quantity"] == 200

    # 检查持仓成本均价
    pos_response = await client.get(
        "/api/v1/positions/000001",
        headers={"Authorization": f"Bearer {token}"}
    )
    pos_data = pos_response.json()
    # 成本均价 = (100*10 + 100*20) / 200 = 15
    assert float(pos_data["avg_cost"]) == 15.00


@pytest.mark.asyncio
async def test_sell_stock_success(client_with_trade_setup):
    """测试卖出股票成功"""
    client, user, token = client_with_trade_setup

    # 先买入
    await client.post(
        "/api/v1/trade/buy",
        headers={"Authorization": f"Bearer {token}"},
        json={"stock_code": "000001", "quantity": 1000, "price": "15.00"}
    )

    # 再卖出
    response = await client.post(
        "/api/v1/trade/sell",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "stock_code": "000001",
            "quantity": 500,
            "price": "16.00"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["transaction"]["type"] == "SELL"
    assert data["transaction"]["quantity"] == 500
    assert float(data["transaction"]["price"]) == 16.00
    # 余额: 100000 - 15000 + 500*16 = 100000 - 15000 + 8000 = 93000
    assert float(data["balance"]) == 93000.00
    assert data["position_quantity"] == 500


@pytest.mark.asyncio
async def test_sell_stock_not_held(client_with_trade_setup):
    """测试卖出未持有的股票"""
    client, user, token = client_with_trade_setup

    response = await client.post(
        "/api/v1/trade/sell",
        headers={"Authorization": f"Bearer {token}"},
        json={"stock_code": "000001", "quantity": 100, "price": "15.00"}
    )
    assert response.status_code == 400
    assert "未持有" in response.json()["detail"]


@pytest.mark.asyncio
async def test_sell_stock_insufficient_quantity(client_with_trade_setup):
    """测试卖出数量超过持仓"""
    client, user, token = client_with_trade_setup

    # 先买入 100 股
    await client.post(
        "/api/v1/trade/buy",
        headers={"Authorization": f"Bearer {token}"},
        json={"stock_code": "000001", "quantity": 100, "price": "15.00"}
    )

    # 尝试卖出 200 股
    response = await client.post(
        "/api/v1/trade/sell",
        headers={"Authorization": f"Bearer {token}"},
        json={"stock_code": "000001", "quantity": 200, "price": "15.00"}
    )
    assert response.status_code == 400
    assert "不足" in response.json()["detail"]


@pytest.mark.asyncio
async def test_sell_all_stock(client_with_trade_setup):
    """测试清仓卖出"""
    client, user, token = client_with_trade_setup

    # 买入
    await client.post(
        "/api/v1/trade/buy",
        headers={"Authorization": f"Bearer {token}"},
        json={"stock_code": "000001", "quantity": 100, "price": "15.00"}
    )

    # 全部卖出
    response = await client.post(
        "/api/v1/trade/sell",
        headers={"Authorization": f"Bearer {token}"},
        json={"stock_code": "000001", "quantity": 100, "price": "15.00"}
    )
    assert response.status_code == 200
    assert response.json()["position_quantity"] == 0

    # 验证持仓已清空
    pos_response = await client.get(
        "/api/v1/positions/000001",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert pos_response.status_code == 404


@pytest.mark.asyncio
async def test_trade_history(client_with_trade_setup):
    """测试交易历史记录"""
    client, user, token = client_with_trade_setup

    # 进行一些交易
    await client.post(
        "/api/v1/trade/buy",
        headers={"Authorization": f"Bearer {token}"},
        json={"stock_code": "000001", "quantity": 100, "price": "15.00"}
    )
    await client.post(
        "/api/v1/trade/buy",
        headers={"Authorization": f"Bearer {token}"},
        json={"stock_code": "000002", "quantity": 200, "price": "20.00"}
    )
    await client.post(
        "/api/v1/trade/sell",
        headers={"Authorization": f"Bearer {token}"},
        json={"stock_code": "000001", "quantity": 50, "price": "16.00"}
    )

    # 查询全部历史
    response = await client.get(
        "/api/v1/trade/history",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3

    # 按股票筛选
    response = await client.get(
        "/api/v1/trade/history?stock_code=000001",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    # 按类型筛选
    response = await client.get(
        "/api/v1/trade/history?type=BUY",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(t["type"] == "BUY" for t in data)