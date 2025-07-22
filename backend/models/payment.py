from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class PaymentMethod(Base):
    __tablename__ = "payment_methods"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    provider = Column(String)  # 'stripe' or 'paypal'
    provider_id = Column(String)  # Stripe customer ID or PayPal billing ID
    last4 = Column(String)
    brand = Column(String)
    is_default = Column(Boolean, default=False)
    user = relationship("User", back_populates="payment_methods")


class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    provider = Column(String, nullable=False)  # 'stripe' or 'paypal'
    transaction_id = Column(String, nullable=False)
    status = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    raw_response = Column(JSON)
    order = relationship("Order", backref="payment_transactions")
