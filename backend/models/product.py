from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, Index
from datetime import datetime
from .base import Base


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, index=True)
    price = Column(Float, nullable=False, index=True)
    image_url = Column(String)
    stock = Column(Integer, default=0, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime, nullable=True)


# Composite indexes for common queries
Index("idx_product_name_deleted", Product.name, Product.is_deleted)
Index("idx_product_price_stock", Product.price, Product.stock)
Index("idx_product_created_deleted", Product.created_at, Product.is_deleted)
