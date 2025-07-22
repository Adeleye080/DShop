from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from models.cart import Cart, CartItem
from models.product import Product
from models.user import User
from schemas.cart import CartItemBase, CartItemOut, CartOut
from core.security import get_current_user
from core.database import get_db
from datetime import datetime
from typing import List

router = APIRouter(prefix="/cart", tags=["cart"])


@router.get("/", response_model=CartOut)
def get_cart(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    cart = db.query(Cart).filter(Cart.user_id == user.id).first()
    if not cart:
        cart = Cart(user_id=user.id, created_at=datetime.utcnow())
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


@router.post("/add", response_model=CartOut)
def add_to_cart(
    item: CartItemBase,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cart = db.query(Cart).filter(Cart.user_id == user.id).first()
    if not cart:
        cart = Cart(user_id=user.id, created_at=datetime.utcnow())
        db.add(cart)
        db.commit()
        db.refresh(cart)
    cart_item = (
        db.query(CartItem)
        .filter(CartItem.cart_id == cart.id, CartItem.product_id == item.product_id)
        .first()
    )
    if cart_item:
        cart_item.quantity += item.quantity
    else:
        cart_item = CartItem(
            cart_id=cart.id, product_id=item.product_id, quantity=item.quantity
        )
        db.add(cart_item)
    db.commit()
    db.refresh(cart)
    return cart


@router.post("/remove", response_model=CartOut)
def remove_from_cart(
    item: CartItemBase,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cart = db.query(Cart).filter(Cart.user_id == user.id).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    cart_item = (
        db.query(CartItem)
        .filter(CartItem.cart_id == cart.id, CartItem.product_id == item.product_id)
        .first()
    )
    if not cart_item:
        raise HTTPException(status_code=404, detail="Item not in cart")
    db.delete(cart_item)
    db.commit()
    db.refresh(cart)
    return cart


@router.post("/update", response_model=CartOut)
def update_cart_item(
    item: CartItemBase,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cart = db.query(Cart).filter(Cart.user_id == user.id).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    cart_item = (
        db.query(CartItem)
        .filter(CartItem.cart_id == cart.id, CartItem.product_id == item.product_id)
        .first()
    )
    if not cart_item:
        raise HTTPException(status_code=404, detail="Item not in cart")
    cart_item.quantity = item.quantity
    db.commit()
    db.refresh(cart)
    return cart
