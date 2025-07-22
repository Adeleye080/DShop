from pydantic import BaseModel
from typing import List


class CartItemBase(BaseModel):
    product_id: int
    quantity: int


class CartItemOut(CartItemBase):
    id: int

    class Config:
        from_attributes = True


class CartOut(BaseModel):
    id: int
    items: List[CartItemOut]

    class Config:
        from_attributes = True
