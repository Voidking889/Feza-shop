from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(320), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False, default="Customer")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    orders = relationship("PurchaseOrder", back_populates="customer")


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String(120), unique=True, index=True, nullable=False)
    invoice_id = Column(String(120), nullable=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    campus = Column(String(120), nullable=True)
    destination = Column(String(500), nullable=True)
    payment_method = Column(String(80), nullable=False)
    status = Column(String(32), nullable=False, default="paid")
    subtotal = Column(Float, nullable=False)
    shipping = Column(Float, nullable=False, default=0)
    tax = Column(Float, nullable=False, default=0)
    total = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    customer = relationship("Customer", back_populates="orders")
    items = relationship("PurchaseItem", back_populates="order", cascade="all, delete-orphan", order_by="PurchaseItem.id")


class PurchaseItem(Base):
    __tablename__ = "purchase_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False, index=True)
    product_id = Column(String(120), nullable=True)
    name = Column(String(200), nullable=False)
    price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    size = Column(String(40), nullable=True)
    color = Column(String(80), nullable=True)

    order = relationship("PurchaseOrder", back_populates="items")
