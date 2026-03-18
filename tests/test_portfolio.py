import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from decimal import Decimal

from app.main import create_app
from app.models import User, Position
from app.db.database import get_db
from app.auth import get_password_hash


@pytest_asyncio.fixture(scope="function")
async def client_with_portfolio_setup(db_session):
    """创建测试客户端并预置用户和持仓"""
    app = create_app()

    # 创建测试用户
    user = User(
        username="portfoliotest",
        password_hash=get_password_hash("testpass123"),
        balance=Decimal("50000.00"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # 创建持仓
    position1 = Position(
        user_id=user.id,
        stock_code="000001",
        stock_name="平安银行",
        quantity=1000,
        avg_cost=Decimal("15.00"),
    )
    position2 = Position(
        user_id=user.id,
        stock_code="000002",
        stock_name="万科A",
        quantity=500,
        avg_cost=Decimal("18.00"),
    )
    db_session.add_all([position1, position2])
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
            data={"username": "portfoliotest", "password": "testpass123"}
        )
        token = login_response.json()["access_token"]
        yield ac, user, token


@pytest.mark.asyncio
async def test_get_portfolio_value(client_with_portfolio_setup):
    """测试获取持仓市值"""
    client, user, token = client_with_portfolio_setup

    response = await client.get(
        "/api/v1/portfolio/value",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total_value" in data
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_get_total_assets(client_with_portfolio_setup):
    """测试获取总资产"""
    client, user, token = client_with_portfolio_setup

    response = await client.get(
        "/api/v1/portfolio/total",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "cash_balance" in data
    assert "stock_value" in data
    assert "total_value" in data
    assert float(data["cash_balance"]) == 50000.00


@pytest.mark.asyncio
async def test_get_profit_loss(client_with_portfolio_setup):
    """测试获取盈亏"""
    client, user, token = client_with_portfolio_setup

    response = await client.get(
        "/api/v1/portfolio/profit-loss",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total_cost" in data
    assert "total_market_value" in data
    assert "total_profit_loss" in data
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_get_stock_quote(client_with_portfolio_setup):
    """测试获取股票行情"""
    client, user, token = client_with_portfolio_setup

    response = await client.get(
        "/api/v1/quote/000001",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["stock_code"] == "000001"
    assert "current_price" in data


@pytest.mark.asyncio
async def test_get_batch_quotes(client_with_portfolio_setup):
    """测试批量获取行情"""
    client, user, token = client_with_portfolio_setup

    response = await client.get(
        "/api/v1/quote/batch?codes=000001,000002",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert "000001" in data
    assert "000002" in data