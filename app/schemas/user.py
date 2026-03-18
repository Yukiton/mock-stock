from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field

from .common import BaseSchema


class UserBase(BaseModel):
    """用户基础信息"""
    username: str = Field(..., min_length=2, max_length=50)


class UserCreate(UserBase):
    """创建用户"""
    password: str = Field(..., min_length=6, max_length=100)


class UserLogin(BaseModel):
    """用户登录"""
    username: str
    password: str


class UserResponse(BaseSchema):
    """用户响应"""
    id: int
    username: str
    balance: Decimal
    created_at: datetime
    updated_at: datetime


class UserUpdate(BaseModel):
    """更新用户"""
    username: Optional[str] = Field(None, min_length=2, max_length=50)


class BalanceUpdate(BaseModel):
    """余额更新"""
    amount: Decimal = Field(..., description="调整金额，正数增加，负数减少")
    reason: Optional[str] = Field(None, description="调整原因")


class Token(BaseModel):
    """Token 响应"""
    access_token: str
    token_type: str = "bearer"