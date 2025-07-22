from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.security import require_role
from core.database import get_db
from models.user import User
from models.product import Product
from models.order import Order
from models.payment import PaymentTransaction
from schemas.user import Token
from typing import List

admin_router = APIRouter(
    prefix="/admin", tags=["admin"], dependencies=[Depends(require_role("admin"))]
)


@admin_router.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    user_count = db.query(User).filter(User.is_deleted == False).count()
    product_count = db.query(Product).filter(Product.is_deleted == False).count()
    order_count = db.query(Order).filter(Order.is_deleted == False).count()
    payment_count = db.query(PaymentTransaction).count()
    total_sales = (
        db.query(Order)
        .filter(Order.status == "paid")
        .with_entities(Order.total_amount)
        .all()
    )
    total_sales_sum = sum([o[0] for o in total_sales]) if total_sales else 0
    return {
        "users": user_count,
        "products": product_count,
        "orders": order_count,
        "payments": payment_count,
        "total_sales": total_sales_sum,
    }


@admin_router.get("/users", response_model=List[Token])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).filter(User.is_deleted == False).all()


@admin_router.get("/payments")
def list_payments(db: Session = Depends(get_db)):
    return db.query(PaymentTransaction).all()
