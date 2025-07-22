from pydantic import BaseModel, Field, constr
from datetime import datetime
from typing import Literal, List, Optional


class OrderItem(BaseModel):
    product_id: int
    product_name: str
    quantity: int
    price: float
    total: float


class OrderOut(BaseModel):
    id: int
    total_amount: float = Field(..., gt=0)
    status: Literal["pending", "paid", "shipped", "delivered", "cancelled"]
    created_at: datetime
    items: Optional[List[OrderItem]] = []
    shipping_address_id: Optional[int] = None

    class Config:
        from_attributes = True


class OrderHistory(BaseModel):
    id: int
    total_amount: float
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    shipping_address_id: Optional[int] = None

    class Config:
        from_attributes = True


class OrderFilter(BaseModel):
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_amount: Optional[float] = Field(None, ge=0)
    max_amount: Optional[float] = Field(None, ge=0)


class OrderCreate(BaseModel):
    shipping_address_id: int
    items: List[OrderItem]
