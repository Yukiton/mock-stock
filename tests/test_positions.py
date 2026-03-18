import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from decimal import Decimal

from app.main import create_app
from app.models import User, Position
from app.db.database import get_db
from app.auth import get_password_hash


@pytest_asyncio.fixture(scope="function")
async def client_with_auth(db_session):
    """创建测试客户端并预置用户和token"""
    app = create_app()

    # 创建测试用户
    user = User(
        username="positiontest",
        password_hash=get_password_hash("testpass123"),
        balance=100000.00,
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
            data={"username": "positiontest", "password": "testpass123"}
        )
        token = login_response.json()["access_token"]
        yield ac, user, token


@pytest.mark.asyncio
async def test_get_positions_empty(client_with_auth):
    """测试获取空持仓列表"""
    client, _, token = client_with_auth
    response = await client.get(
        "/api/v1/positions",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_position(client_with_auth):
    """测试创建持仓"""
    client, _, token = client_with_auth
    response = await client.post(
        "/api/v1/positions",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "stock_code": "000001",
            "stock_name": "平安银行",
            "quantity": 1000,
            "avg_cost": "15.50"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["stock_code"] == "000001"
    assert data["stock_name"] == "平安银行"
    assert data["quantity"] == 1000
    assert float(data["avg_cost"]) == 15.50


@pytest.mark.asyncio
async def test_create_duplicate_position(client_with_auth):
    """测试重复创建持仓"""
    client, _, token = client_with_auth
    # 第一次创建
    await client.post(
        "/api/v1/positions",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "stock_code": "000002",
            "stock_name": "万科A",
            "quantity": 500,
            "avg_cost": "10.00"
        }
    )
    # 第二次创建同一股票
    response = await client.post(
        "/api/v1/positions",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "stock_code": "000002",
            "stock_name": "万科A",
            "quantity": 200,
            "avg_cost": "11.00"
        }
    )
    assert response.status_code == 400
    assert "已持有" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_positions(client_with_auth):
    """测试获取持仓列表"""
    client, _, token = client_with_auth
    # 创建两个持仓
    await client.post(
        "/api/v1/positions",
        headers={"Authorization": f"Bearer {token}"},
        json={"stock_code": "000001", "quantity": 100, "avg_cost": "15.00"}
    )
    await client.post(
        "/api/v1/positions",
        headers={"Authorization": f"Bearer {token}"},
        json={"stock_code": "000002", "quantity": 200, "avg_cost": "20.00"}
    )

    response = await client.get(
        "/api/v1/positions",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_get_position(client_with_auth):
    """测试获取单只股票持仓"""
    client, _, token = client_with_auth
    await client.post(
        "/api/v1/positions",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "stock_code": "000001",
            "stock_name": "平安银行",
            "quantity": 1000,
            "avg_cost": "15.50"
        }
    )

    response = await client.get(
        "/api/v1/positions/000001",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["stock_code"] == "000001"
    assert data["quantity"] == 1000


@pytest.mark.asyncio
async def test_get_position_not_found(client_with_auth):
    """测试获取不存在的持仓"""
    client, _, token = client_with_auth
    response = await client.get(
        "/api/v1/positions/999999",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_position(client_with_auth):
    """测试更新持仓"""
    client, _, token = client_with_auth
    await client.post(
        "/api/v1/positions",
        headers={"Authorization": f"Bearer {token}"},
        json={"stock_code": "000001", "quantity": 100, "avg_cost": "15.00"}
    )

    response = await client.put(
        "/api/v1/positions/000001",
        headers={"Authorization": f"Bearer {token}"},
        json={"quantity": 200, "avg_cost": "16.00"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["quantity"] == 200
    assert float(data["avg_cost"]) == 16.00


@pytest.mark.asyncio
async def test_delete_position(client_with_auth):
    """测试删除持仓"""
    client, _, token = client_with_auth
    await client.post(
        "/api/v1/positions",
        headers={"Authorization": f"Bearer {token}"},
        json={"stock_code": "000001", "quantity": 100, "avg_cost": "15.00"}
    )

    response = await client.delete(
        "/api/v1/positions/000001",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

    # 验证已删除
    response = await client.get(
        "/api/v1/positions/000001",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_position_not_found(client_with_auth):
    """测试删除不存在的持仓"""
    client, _, token = client_with_auth
    response = await client.delete(
        "/api/v1/positions/999999",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404