from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.address import Address
from schemas.address import AddressCreate, AddressUpdate, AddressOut
from core.security import get_current_user
from core.database import get_db
from models.user import User
from typing import List

router = APIRouter(prefix="/addresses", tags=["addresses"])


@router.get("/", response_model=List[AddressOut])
def list_addresses(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    return db.query(Address).filter(Address.user_id == user.id).all()


@router.post("/", response_model=AddressOut)
def create_address(
    address: AddressCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    addr = Address(**address.dict(), user_id=user.id)
    db.add(addr)
    db.commit()
    db.refresh(addr)
    return addr


@router.put("/{address_id}", response_model=AddressOut)
def update_address(
    address_id: int,
    address: AddressUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    addr = (
        db.query(Address)
        .filter(Address.id == address_id, Address.user_id == user.id)
        .first()
    )
    if not addr:
        raise HTTPException(status_code=404, detail="Address not found")
    for k, v in address.dict().items():
        setattr(addr, k, v)
    db.commit()
    db.refresh(addr)
    return addr


@router.delete("/{address_id}", status_code=204)
def delete_address(
    address_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    addr = (
        db.query(Address)
        .filter(Address.id == address_id, Address.user_id == user.id)
        .first()
    )
    if not addr:
        raise HTTPException(status_code=404, detail="Address not found")
    db.delete(addr)
    db.commit()
    return None
