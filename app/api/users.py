from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import User
from app.schemas import UserResponse, BalanceUpdate, Token, ResponseBase
from app.services import UserService
from app.auth import create_access_token, get_current_active_user

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    username: str,
    password: str,
    db: AsyncSession = Depends(get_db)
):
    """用户注册"""
    from app.schemas import UserCreate
    service = UserService(db)
    try:
        user = await service.create_user(UserCreate(username=username, password=password))
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """用户登录"""
    service = UserService(db)
    user = await service.authenticate(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return Token(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """获取当前用户信息"""
    return current_user


@router.get("/me/balance")
async def get_balance(
    current_user: User = Depends(get_current_active_user)
):
    """获取账户余额"""
    return {"balance": current_user.balance}


@router.put("/me/balance")
async def update_balance(
    data: BalanceUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """调整账户余额"""
    service = UserService(db)
    try:
        user = await service.update_balance(current_user.id, data.amount)
        return {"balance": user.balance, "message": f"余额已调整 {data.amount}"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))