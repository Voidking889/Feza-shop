from sqlalchemy import Column, String, Float, DateTime, JSON
from app.db.database import Base
from datetime import datetime
import uuid

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, default=lambda: f"TXN-{uuid.uuid4().hex[:9]}")
    merchant_id = Column(String, index=True)
    phone_number = Column(String)
    amount = Column(Float)
    status = Column(String, default="pending")
    items = Column(JSON, default=list) 
    created_at = Column(DateTime, default=datetime.utcnow)
    customer_email = Column(String)
