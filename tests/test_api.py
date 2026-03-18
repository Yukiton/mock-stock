"""API 测试"""
import pytest


@pytest.mark.asyncio
async def test_health_check(client):
    """测试健康检查接口"""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_openapi_docs(client):
    """测试 API 文档可访问"""
    response = await client.get("/docs")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_redoc(client):
    """测试 ReDoc 文档可访问"""
    response = await client.get("/redoc")
    assert response.status_code == 200