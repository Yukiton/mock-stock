import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from app.main import create_app
from app.models import User
from app.db.database import get_db
from app.services import UserService
from app.auth import get_password_hash


@pytest_asyncio.fixture(scope="function")
async def app():
    """创建测试应用"""
    from app.main import create_app
    return create_app()


@pytest_asyncio.fixture(scope="function")
async def client_with_user(db_session, app):
    """创建测试客户端并预置用户"""
    # 创建测试用户
    user = User(
        username="testuser",
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
        yield ac, user


@pytest.mark.asyncio
async def test_register(client_with_user):
    """测试用户注册"""
    client, _ = client_with_user
    response = await client.post(
        "/api/v1/users/register",
        params={"username": "newuser", "password": "newpass123"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["balance"] == "0.00"


@pytest.mark.asyncio
async def test_register_duplicate(client_with_user):
    """测试重复注册"""
    client, _ = client_with_user
    response = await client.post(
        "/api/v1/users/register",
        params={"username": "testuser", "password": "testpass123"}
    )
    assert response.status_code == 400
    assert "已存在" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_success(client_with_user):
    """测试登录成功"""
    client, _ = client_with_user
    response = await client.post(
        "/api/v1/users/login",
        data={"username": "testuser", "password": "testpass123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client_with_user):
    """测试登录密码错误"""
    client, _ = client_with_user
    response = await client.post(
        "/api/v1/users/login",
        data={"username": "testuser", "password": "wrongpassword"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user(client_with_user):
    """测试获取当前用户"""
    client, user = client_with_user
    # 先登录获取token
    login_response = await client.post(
        "/api/v1/users/login",
        data={"username": "testuser", "password": "testpass123"}
    )
    token = login_response.json()["access_token"]

    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert float(data["balance"]) == 100000.00


@pytest.mark.asyncio
async def test_get_current_user_no_token(client_with_user):
    """测试无token获取用户"""
    client, _ = client_with_user
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_balance(client_with_user):
    """测试获取余额"""
    client, _ = client_with_user
    login_response = await client.post(
        "/api/v1/users/login",
        data={"username": "testuser", "password": "testpass123"}
    )
    token = login_response.json()["access_token"]

    response = await client.get(
        "/api/v1/users/me/balance",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert float(data["balance"]) == 100000.00


@pytest.mark.asyncio
async def test_update_balance(client_with_user):
    """测试调整余额"""
    client, _ = client_with_user
    login_response = await client.post(
        "/api/v1/users/login",
        data={"username": "testuser", "password": "testpass123"}
    )
    token = login_response.json()["access_token"]

    # 增加余额
    response = await client.put(
        "/api/v1/users/me/balance",
        headers={"Authorization": f"Bearer {token}"},
        json={"amount": 50000.00}
    )
    assert response.status_code == 200
    data = response.json()
    assert float(data["balance"]) == 150000.00

    # 减少余额
    response = await client.put(
        "/api/v1/users/me/balance",
        headers={"Authorization": f"Bearer {token}"},
        json={"amount": -30000.00}
    )
    assert response.status_code == 200
    data = response.json()
    assert float(data["balance"]) == 120000.00


@pytest.mark.asyncio
async def test_update_balance_insufficient(client_with_user):
    """测试余额不足"""
    client, _ = client_with_user
    login_response = await client.post(
        "/api/v1/users/login",
        data={"username": "testuser", "password": "testpass123"}
    )
    token = login_response.json()["access_token"]

    response = await client.put(
        "/api/v1/users/me/balance",
        headers={"Authorization": f"Bearer {token}"},
        json={"amount": -200000.00}
    )
    assert response.status_code == 400
    assert "不足" in response.json()["detail"]