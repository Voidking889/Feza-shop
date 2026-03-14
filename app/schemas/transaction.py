from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

class PaymentItem(BaseModel):
    name: str = "Item"
    price: float = 0.0
    quantity: int = 1

class PaymentRequest(BaseModel):
    merchant_id: str
    phone_number: str = Field(..., description="E.g., +255123456789")
    amount: float = Field(..., gt=0, description="Amount must be greater than 0")
    network: str
    items: List[Dict[str, Any]] = []
    customer_email: str

class PaymentResponse(BaseModel):
    status: str
    message: str
    transaction_id: str

class TransactionStatus(BaseModel):
    status: str
    message: str
    transaction_id: str
    invoice_id: Optional[str] = None
    details: Dict[str, Any]
