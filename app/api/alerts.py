"""价格提醒API路由"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import User
from app.schemas import AlertCreate, AlertUpdate, AlertResponse
from app.services import AlertService
from app.auth import get_current_active_user
from app.strategies import list_strategies
from app.notifiers import list_notifiers

router = APIRouter()


@router.get("", response_model=List[AlertResponse])
async def get_alerts(
    stock_code: Optional[str] = None,
    enabled_only: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取价格提醒列表"""
    service = AlertService(db)
    alerts = await service.get_alerts(
        user_id=current_user.id,
        stock_code=stock_code,
        enabled_only=enabled_only
    )
    return alerts


@router.post("", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(
    data: AlertCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """创建价格提醒"""
    # 验证策略类型
    if data.strategy_type not in list_strategies():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的策略类型: {data.strategy_type}"
        )

    # 验证通知器类型
    if data.notifier_type not in list_notifiers():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的通知器类型: {data.notifier_type}"
        )

    service = AlertService(db)
    alert = await service.create_alert(user_id=current_user.id, data=data)
    return alert


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取单个价格提醒"""
    service = AlertService(db)
    alert = await service.get_alert(alert_id, current_user.id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提醒不存在"
        )
    return alert


@router.put("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: int,
    data: AlertUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新价格提醒"""
    service = AlertService(db)
    alert = await service.update_alert(alert_id, current_user.id, data)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提醒不存在"
        )
    return alert


@router.delete("/{alert_id}")
async def delete_alert(
    alert_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """删除价格提醒"""
    service = AlertService(db)
    success = await service.delete_alert(alert_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提醒不存在"
        )
    return {"message": "删除成功"}


@router.post("/{alert_id}/check")
async def check_alert(
    alert_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """手动检查提醒是否触发"""
    service = AlertService(db)
    alert = await service.get_alert(alert_id, current_user.id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提醒不存在"
        )

    result = await service.check_alert(alert)

    response = {
        "alert_id": alert_id,
        "stock_code": alert.stock_code,
        "triggered": result.triggered,
        "reason": result.reason,
        "details": result.details
    }

    # 如果触发，发送通知
    if result.triggered:
        success = await service.trigger_alert(alert, result)
        response["notified"] = success

    return response


@router.post("/check-all")
async def check_all_alerts(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """检查当前用户所有启用的提醒"""
    service = AlertService(db)
    results = await service.check_all_alerts(user_id=current_user.id)
    return {"results": results}


@router.get("/meta/strategies")
async def get_available_strategies():
    """获取可用的策略类型"""
    return {"strategies": list_strategies()}


@router.get("/meta/notifiers")
async def get_available_notifiers():
    """获取可用的通知器类型"""
    return {"notifiers": list_notifiers()}