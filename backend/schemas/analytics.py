from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime


class SalesAnalytics(BaseModel):
    total_sales: float
    total_orders: int
    average_order_value: float
    sales_by_month: List[Dict[str, float]]
    top_selling_products: List[Dict[str, Any]]
    revenue_growth: float  # percentage


class UserAnalytics(BaseModel):
    total_users: int
    active_users: int
    new_users_this_month: int
    user_growth_rate: float
    users_by_role: Dict[str, int]
    top_customers: List[Dict[str, Any]]


class ProductAnalytics(BaseModel):
    total_products: int
    low_stock_products: int
    out_of_stock_products: int
    top_viewed_products: List[Dict[str, Any]]
    category_distribution: Dict[str, int]


class OrderAnalytics(BaseModel):
    total_orders: int
    pending_orders: int
    completed_orders: int
    cancelled_orders: int
    orders_by_status: Dict[str, int]
    average_processing_time: float  # in hours


class DashboardAnalytics(BaseModel):
    sales: SalesAnalytics
    users: UserAnalytics
    products: ProductAnalytics
    orders: OrderAnalytics
    last_updated: datetime


class TimeRange(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
