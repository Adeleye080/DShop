from pydantic import BaseModel, constr
from typing import Optional


class AddressBase(BaseModel):
    street: constr(min_length=1, max_length=128)
    city: constr(min_length=1, max_length=64)
    state: constr(min_length=1, max_length=64)
    postal_code: constr(min_length=1, max_length=20)
    country: constr(min_length=1, max_length=64)
    phone: Optional[constr(min_length=7, max_length=20)] = None


class AddressCreate(AddressBase):
    pass


class AddressUpdate(AddressBase):
    pass


class AddressOut(AddressBase):
    id: int

    class Config:
        from_attributes = True
