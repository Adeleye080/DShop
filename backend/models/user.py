from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    Index,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, index=True)
    phone = Column(String, nullable=True, index=True)
    date_of_birth = Column(DateTime, nullable=True)
    preferences = Column(JSON, default={})
    is_active = Column(Boolean, default=True, index=True)
    is_admin = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    email_verified = Column(Boolean, default=False, index=True)
    verification_token = Column(String, nullable=True, index=True)
    password_reset_token = Column(String, nullable=True, index=True)
    password_reset_expiry = Column(DateTime, nullable=True)
    role = Column(String, default="user", index=True)  # user, admin, staff
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    otp_secret = Column(String, nullable=True)  # For TOTP 2FA
    payment_methods = relationship("PaymentMethod", back_populates="user")
    carts = relationship("Cart", back_populates="user")
    orders = relationship("Order", back_populates="user")
    addresses = relationship("Address", back_populates="user")


# Composite indexes for common queries
Index("idx_user_email_active", User.email, User.is_active)
Index("idx_user_role_active", User.role, User.is_active)
