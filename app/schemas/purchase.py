from pydantic import BaseModel, ConfigDict, Field


class PurchaseItemCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    id: str | int | None = None
    name: str = Field(min_length=1, max_length=200)
    price: float = Field(ge=0, le=1_000_000_000)
    quantity: int = Field(ge=1, le=1000)
    size: str | None = Field(default=None, max_length=40)
    color: str | None = Field(default=None, max_length=80)


class PurchaseCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    transaction_id: str = Field(min_length=1, max_length=120)
    invoice_id: str | None = Field(default=None, max_length=120)
    email: str = Field(min_length=3, max_length=320)
    customer_name: str | None = Field(default=None, max_length=200)
    campus: str | None = Field(default=None, max_length=120)
    destination: str | None = Field(default=None, max_length=500)
    payment_method: str = Field(min_length=1, max_length=80)
    subtotal: float = Field(ge=0, le=1_000_000_000)
    shipping: float = Field(ge=0, le=1_000_000_000)
    tax: float = Field(ge=0, le=1_000_000_000)
    total: float = Field(gt=0, le=1_000_000_000)
    items: list[PurchaseItemCreate] = Field(min_length=1, max_length=100)


class PurchaseItemRead(BaseModel):
    id: str | None
    name: str
    price: float
    quantity: int
    size: str | None
    color: str | None


class PurchaseRead(BaseModel):
    invoice_id: str | None
    transaction_id: str
    date: str
    email: str
    customer_name: str
    campus: str | None
    destination: str | None
    payment_method: str
    status: str
    subtotal: float
    shipping: float
    tax: float
    total: float
    items: list[PurchaseItemRead]
