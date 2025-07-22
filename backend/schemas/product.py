from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime


class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    description: Optional[str] = Field(None, max_length=1024)
    price: float = Field(..., gt=0)
    image_url: Optional[HttpUrl] = None
    stock: int = Field(0, ge=0)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(ProductBase):
    pass


class ProductOut(ProductBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ProductSearch(BaseModel):
    query: Optional[str] = None
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    in_stock: Optional[bool] = None
    sort_by: Optional[str] = Field(None, pattern="^(name|price|created_at)$")
    sort_order: Optional[str] = Field(None, pattern="^(asc|desc)$")


class ProductFilter(BaseModel):
    category: Optional[str] = None
    brand: Optional[str] = None
    tags: Optional[List[str]] = None
