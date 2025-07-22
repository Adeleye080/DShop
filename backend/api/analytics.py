from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc, extract
from core.security import require_role
from core.database import get_db
from models.user import User
from models.product import Product
from models.order import Order
from models.payment import PaymentTransaction
from schemas.analytics import (
    DashboardAnalytics,
    SalesAnalytics,
    UserAnalytics,
    ProductAnalytics,
    OrderAnalytics,
    TimeRange,
)
from datetime import datetime, timedelta
from typing import List, Dict

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
    dependencies=[Depends(require_role("admin"))],
)


@router.get("/dashboard", response_model=DashboardAnalytics)
def get_dashboard_analytics(
    time_range: TimeRange = Depends(), db: Session = Depends(get_db)
):
    """Get comprehensive dashboard analytics"""
    start_date = time_range.start_date or (datetime.utcnow() - timedelta(days=30))
    end_date = time_range.end_date or datetime.utcnow()

    return DashboardAnalytics(
        sales=get_sales_analytics(db, start_date, end_date),
        users=get_user_analytics(db, start_date, end_date),
        products=get_product_analytics(db),
        orders=get_order_analytics(db, start_date, end_date),
        last_updated=datetime.utcnow(),
    )


@router.get("/sales", response_model=SalesAnalytics)
def get_sales_analytics_endpoint(
    time_range: TimeRange = Depends(), db: Session = Depends(get_db)
):
    """Get sales analytics"""
    start_date = time_range.start_date or (datetime.utcnow() - timedelta(days=30))
    end_date = time_range.end_date or datetime.utcnow()
    return get_sales_analytics(db, start_date, end_date)


@router.get("/users", response_model=UserAnalytics)
def get_user_analytics_endpoint(
    time_range: TimeRange = Depends(), db: Session = Depends(get_db)
):
    """Get user analytics"""
    start_date = time_range.start_date or (datetime.utcnow() - timedelta(days=30))
    end_date = time_range.end_date or datetime.utcnow()
    return get_user_analytics(db, start_date, end_date)


@router.get("/products", response_model=ProductAnalytics)
def get_product_analytics_endpoint(db: Session = Depends(get_db)):
    """Get product analytics"""
    return get_product_analytics(db)


@router.get("/orders", response_model=OrderAnalytics)
def get_order_analytics_endpoint(
    time_range: TimeRange = Depends(), db: Session = Depends(get_db)
):
    """Get order analytics"""
    start_date = time_range.start_date or (datetime.utcnow() - timedelta(days=30))
    end_date = time_range.end_date or datetime.utcnow()
    return get_order_analytics(db, start_date, end_date)


def get_sales_analytics(
    db: Session, start_date: datetime, end_date: datetime
) -> SalesAnalytics:
    """Calculate sales analytics"""
    # Total sales and orders in date range
    sales_query = (
        db.query(
            func.sum(Order.total_amount).label("total_sales"),
            func.count(Order.id).label("total_orders"),
        )
        .filter(
            and_(
                Order.created_at >= start_date,
                Order.created_at <= end_date,
                Order.status.in_(["paid", "shipped", "delivered"]),
            )
        )
        .first()
    )

    total_sales = sales_query.total_sales or 0
    total_orders = sales_query.total_orders or 0
    average_order_value = total_sales / total_orders if total_orders > 0 else 0

    # Sales by month (last 6 months)
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    monthly_sales = (
        db.query(
            extract("year", Order.created_at).label("year"),
            extract("month", Order.created_at).label("month"),
            func.sum(Order.total_amount).label("monthly_sales"),
        )
        .filter(
            and_(
                Order.created_at >= six_months_ago,
                Order.status.in_(["paid", "shipped", "delivered"]),
            )
        )
        .group_by(extract("year", Order.created_at), extract("month", Order.created_at))
        .order_by(desc("year"), desc("month"))
        .all()
    )

    sales_by_month = [
        {
            "month": f"{int(row.year)}-{int(row.month):02d}",
            "sales": float(row.monthly_sales or 0),
        }
        for row in monthly_sales
    ]

    # Top selling products (by order count)
    top_products = (
        db.query(
            Product.name,
            func.count(Order.id).label("order_count"),
            func.sum(Order.total_amount).label("total_revenue"),
        )
        .join(Order, Product.id == Order.id)
        .filter(
            and_(
                Order.created_at >= start_date,
                Order.created_at <= end_date,
                Order.status.in_(["paid", "shipped", "delivered"]),
            )
        )
        .group_by(Product.id, Product.name)
        .order_by(desc("order_count"))
        .limit(10)
        .all()
    )

    top_selling_products = [
        {
            "name": row.name,
            "order_count": int(row.order_count),
            "total_revenue": float(row.total_revenue or 0),
        }
        for row in top_products
    ]

    # Revenue growth (compare with previous period)
    prev_start = start_date - (end_date - start_date)
    prev_sales = (
        db.query(func.sum(Order.total_amount))
        .filter(
            and_(
                Order.created_at >= prev_start,
                Order.created_at < start_date,
                Order.status.in_(["paid", "shipped", "delivered"]),
            )
        )
        .scalar()
        or 0
    )

    revenue_growth = (
        ((total_sales - prev_sales) / prev_sales * 100) if prev_sales > 0 else 0
    )

    return SalesAnalytics(
        total_sales=total_sales,
        total_orders=total_orders,
        average_order_value=average_order_value,
        sales_by_month=sales_by_month,
        top_selling_products=top_selling_products,
        revenue_growth=revenue_growth,
    )


def get_user_analytics(
    db: Session, start_date: datetime, end_date: datetime
) -> UserAnalytics:
    """Calculate user analytics"""
    # Total users
    total_users = db.query(User).filter(User.is_deleted == False).count()

    # Active users (users with orders in date range)
    active_users = (
        db.query(func.count(func.distinct(Order.user_id)))
        .filter(and_(Order.created_at >= start_date, Order.created_at <= end_date))
        .scalar()
        or 0
    )

    # New users this month
    month_start = datetime.utcnow().replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    new_users_this_month = (
        db.query(User)
        .filter(and_(User.created_at >= month_start, User.is_deleted == False))
        .count()
    )

    # User growth rate
    prev_month_start = (month_start - timedelta(days=1)).replace(day=1)
    prev_month_users = (
        db.query(User)
        .filter(
            and_(
                User.created_at >= prev_month_start,
                User.created_at < month_start,
                User.is_deleted == False,
            )
        )
        .count()
    )

    user_growth_rate = (
        ((new_users_this_month - prev_month_users) / prev_month_users * 100)
        if prev_month_users > 0
        else 0
    )

    # Users by role
    users_by_role = (
        db.query(User.role, func.count(User.id).label("count"))
        .filter(User.is_deleted == False)
        .group_by(User.role)
        .all()
    )

    users_by_role_dict = {row.role: int(row.count) for row in users_by_role}

    # Top customers (by total spent)
    top_customers = (
        db.query(
            User.full_name,
            User.email,
            func.sum(Order.total_amount).label("total_spent"),
            func.count(Order.id).label("order_count"),
        )
        .join(Order, User.id == Order.user_id)
        .filter(
            and_(
                Order.status.in_(["paid", "shipped", "delivered"]),
                User.is_deleted == False,
            )
        )
        .group_by(User.id, User.full_name, User.email)
        .order_by(desc("total_spent"))
        .limit(10)
        .all()
    )

    top_customers_list = [
        {
            "name": row.full_name or "Unknown",
            "email": row.email,
            "total_spent": float(row.total_spent or 0),
            "order_count": int(row.order_count),
        }
        for row in top_customers
    ]

    return UserAnalytics(
        total_users=total_users,
        active_users=active_users,
        new_users_this_month=new_users_this_month,
        user_growth_rate=user_growth_rate,
        users_by_role=users_by_role_dict,
        top_customers=top_customers_list,
    )


def get_product_analytics(db: Session) -> ProductAnalytics:
    """Calculate product analytics"""
    # Total products
    total_products = db.query(Product).filter(Product.is_deleted == False).count()

    # Low stock products (less than 10)
    low_stock_products = (
        db.query(Product)
        .filter(
            and_(Product.stock < 10, Product.stock > 0, Product.is_deleted == False)
        )
        .count()
    )

    # Out of stock products
    out_of_stock_products = (
        db.query(Product)
        .filter(and_(Product.stock == 0, Product.is_deleted == False))
        .count()
    )

    # Top viewed products (placeholder - would need view tracking)
    top_viewed_products = []

    # Category distribution (placeholder - would need category field)
    category_distribution = {}

    return ProductAnalytics(
        total_products=total_products,
        low_stock_products=low_stock_products,
        out_of_stock_products=out_of_stock_products,
        top_viewed_products=top_viewed_products,
        category_distribution=category_distribution,
    )


def get_order_analytics(
    db: Session, start_date: datetime, end_date: datetime
) -> OrderAnalytics:
    """Calculate order analytics"""
    # Total orders in date range
    total_orders = (
        db.query(Order)
        .filter(and_(Order.created_at >= start_date, Order.created_at <= end_date))
        .count()
    )

    # Orders by status
    orders_by_status = (
        db.query(Order.status, func.count(Order.id).label("count"))
        .filter(and_(Order.created_at >= start_date, Order.created_at <= end_date))
        .group_by(Order.status)
        .all()
    )

    orders_by_status_dict = {row.status: int(row.count) for row in orders_by_status}

    pending_orders = orders_by_status_dict.get("pending", 0)
    completed_orders = orders_by_status_dict.get("delivered", 0)
    cancelled_orders = orders_by_status_dict.get("cancelled", 0)

    # Average processing time (placeholder - would need more detailed tracking)
    average_processing_time = 24.0  # hours

    return OrderAnalytics(
        total_orders=total_orders,
        pending_orders=pending_orders,
        completed_orders=completed_orders,
        cancelled_orders=cancelled_orders,
        orders_by_status=orders_by_status_dict,
        average_processing_time=average_processing_time,
    )
