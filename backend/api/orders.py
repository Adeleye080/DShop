from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from models.order import Order
from models.cart import Cart, CartItem
from models.product import Product
from models.user import User
from models.audit import AuditLog
from schemas.order import OrderOut, OrderHistory, OrderFilter
from core.security import get_current_user, require_role
from core.database import get_db
from datetime import datetime
from typing import List
from core.email_utils import send_email, render_template
from core.pagination import paginate_query, get_pagination_params, PaginatedResponse
from sqlalchemy import and_

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/place", response_model=OrderOut)
def place_order(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    cart = db.query(Cart).filter(Cart.user_id == user.id).first()
    if not cart or not cart.items:
        raise HTTPException(status_code=400, detail="Cart is empty")
    total = 0
    items = []
    for item in cart.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product or product.stock < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Product {item.product_id} unavailable or out of stock",
            )
        total += product.price * item.quantity
        product.stock -= item.quantity
        items.append(
            {"name": product.name, "quantity": item.quantity, "price": product.price}
        )
    order = Order(
        user_id=user.id,
        total_amount=total,
        status="pending",
        created_at=datetime.utcnow(),
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    # Optionally clear cart
    for item in cart.items:
        db.delete(item)
    db.commit()
    # Send order confirmation email
    html_body = render_template(
        "order_confirmation_email.html",
        full_name=user.full_name,
        order_id=order.id,
        items=items,
        total=total,
    )
    send_email(
        str(user.email),
        "Order Confirmation",
        f"Your order #{order.id} has been placed.",
        html_body=html_body,
    )
    return order


@router.get("/", response_model=List[OrderOut])
def list_orders(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return (
        db.query(Order)
        .filter(Order.user_id == user.id, Order.is_deleted == False)
        .all()
    )


@router.get("/{order_id}", response_model=OrderOut)
def get_order(
    order_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    order = (
        db.query(Order)
        .filter(
            Order.id == order_id, Order.user_id == user.id, Order.is_deleted == False
        )
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(
    order_id: int, db: Session = Depends(get_db), user=Depends(require_role("admin"))
):
    order = (
        db.query(Order).filter(Order.id == order_id, Order.is_deleted == False).first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    object.__setattr__(order, "is_deleted", True)
    object.__setattr__(order, "deleted_at", datetime.utcnow())
    db.commit()
    db.add(
        AuditLog(
            user_id=user.id,
            action="delete",
            target_type="order",
            target_id=order.id,
            details={},
        )
    )
    db.commit()
    return None


@router.get(
    "/all", response_model=List[OrderOut], dependencies=[Depends(require_role("admin"))]
)
def list_all_orders(db: Session = Depends(get_db)):
    return db.query(Order).filter(Order.is_deleted == False).all()


@router.patch(
    "/{order_id}/status",
    response_model=OrderOut,
    dependencies=[Depends(require_role("admin"))],
)
def update_order_status(order_id: int, status: str, db: Session = Depends(get_db)):
    order = (
        db.query(Order).filter(Order.id == order_id, Order.is_deleted == False).first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    allowed_statuses = ["pending", "paid", "shipped", "delivered", "cancelled"]
    if status not in allowed_statuses:
        raise HTTPException(
            status_code=400, detail=f"Invalid status. Allowed: {allowed_statuses}"
        )
    # Set status on the order instance
    setattr(order, "status", status)
    db.commit()
    db.refresh(order)
    # Send order status update email
    user = db.query(User).filter(User.id == order.user_id).first()
    if user is not None:
        html_body = render_template(
            "order_status_update_email.html",
            full_name=user.full_name,
            order_id=order.id,
            status=status,
            tracking_url=None,
        )
        send_email(
            str(user.email),
            "Order Status Update",
            f"Order #{order.id} status updated to {status}.",
            html_body=html_body,
        )
    return order


@router.get("/history", response_model=PaginatedResponse[OrderHistory])
def get_order_history(
    filter: OrderFilter = Depends(),
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(Order).filter(Order.user_id == user.id, Order.is_deleted == False)

    # Apply filters
    if filter.status:
        query = query.filter(Order.status == filter.status)

    if filter.start_date:
        query = query.filter(Order.created_at >= filter.start_date)

    if filter.end_date:
        query = query.filter(Order.created_at <= filter.end_date)

    if filter.min_amount:
        query = query.filter(Order.total_amount >= filter.min_amount)

    if filter.max_amount:
        query = query.filter(Order.total_amount <= filter.max_amount)

    # Order by most recent first
    query = query.order_by(Order.created_at.desc())

    return paginate_query(query, page, size)
