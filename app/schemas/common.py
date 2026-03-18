from datetime import datetime
from typing import Optional, Generic, TypeVar
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class BaseSchema(BaseModel):
    """基础 Schema"""
    model_config = ConfigDict(from_attributes=True)


class ResponseBase(BaseModel, Generic[T]):
    """通用响应模型"""
    success: bool = True
    message: str = "success"
    data: Optional[T] = None


class PaginationParams(BaseModel):
    """分页参数"""
    page: int = 1
    page_size: int = 20

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应模型"""
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int