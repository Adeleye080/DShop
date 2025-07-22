from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class Address(Base):
    __tablename__ = "addresses"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    street = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    postal_code = Column(String, nullable=False)
    country = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="addresses")
