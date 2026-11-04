import math
import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.database import get_db
from app.models.purchase import Customer, PurchaseItem, PurchaseOrder
from app.schemas.purchase import PurchaseCreate, PurchaseRead

router = APIRouter()


def serialize_order(order: PurchaseOrder) -> dict:
    return {
        "invoice_id": order.invoice_id,
        "transaction_id": order.transaction_id,
        "date": order.created_at.isoformat(),
        "email": order.customer.email,
        "customer_name": order.customer.name,
        "campus": order.campus,
        "destination": order.destination,
        "payment_method": order.payment_method,
        "status": order.status,
        "subtotal": order.subtotal,
        "shipping": order.shipping,
        "tax": order.tax,
        "total": order.total,
        "items": [
            {
                "id": item.product_id,
                "name": item.name,
                "price": item.price,
                "quantity": item.quantity,
                "size": item.size,
                "color": item.color,
            }
            for item in order.items
        ],
    }


async def find_order(session: AsyncSession, transaction_id: str) -> PurchaseOrder | None:
    result = await session.execute(
        select(PurchaseOrder)
        .options(selectinload(PurchaseOrder.customer), selectinload(PurchaseOrder.items))
        .where(PurchaseOrder.transaction_id == transaction_id)
    )
    return result.scalar_one_or_none()


@router.post("/orders", response_model=PurchaseRead, status_code=status.HTTP_201_CREATED)
async def create_order(payload: PurchaseCreate, session: AsyncSession = Depends(get_db)):
    email = payload.email.lower()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        raise HTTPException(status_code=422, detail="A valid customer email is required.")

    calculated_subtotal = sum(item.price * item.quantity for item in payload.items)
    calculated_total = calculated_subtotal + payload.shipping + payload.tax
    if not math.isclose(calculated_subtotal, payload.subtotal, abs_tol=0.02):
        raise HTTPException(status_code=422, detail="Order subtotal does not match its items.")
    if not math.isclose(calculated_total, payload.total, abs_tol=0.02):
        raise HTTPException(status_code=422, detail="Order total does not match its subtotal, shipping, and tax.")

    existing = await find_order(session, payload.transaction_id)
    if existing:
        return serialize_order(existing)

    customer_result = await session.execute(select(Customer).where(Customer.email == email))
    customer = customer_result.scalar_one_or_none()
    if customer is None:
        customer = Customer(email=email, name=payload.customer_name or email.split("@", 1)[0])
        session.add(customer)
        await session.flush()
    elif payload.customer_name:
        customer.name = payload.customer_name

    order = PurchaseOrder(
        transaction_id=payload.transaction_id,
        invoice_id=payload.invoice_id,
        customer=customer,
        campus=payload.campus,
        destination=payload.destination,
        payment_method=payload.payment_method,
        status="paid",
        subtotal=calculated_subtotal,
        shipping=payload.shipping,
        tax=payload.tax,
        total=calculated_total,
        created_at=datetime.now(timezone.utc),
        items=[
            PurchaseItem(
                product_id=str(item.id) if item.id is not None else None,
                name=item.name,
                price=item.price,
                quantity=item.quantity,
                size=item.size,
                color=item.color,
            )
            for item in payload.items
        ],
    )
    session.add(order)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        existing = await find_order(session, payload.transaction_id)
        if existing:
            return serialize_order(existing)
        raise HTTPException(status_code=409, detail="Could not save this purchase due to a conflicting record.")

    saved_order = await find_order(session, payload.transaction_id)
    if saved_order is None:
        raise HTTPException(status_code=500, detail="Purchase was saved but could not be loaded.")
    return serialize_order(saved_order)


@router.get("/orders", response_model=list[PurchaseRead])
async def customer_orders(
    email: str = Query(min_length=3, max_length=320),
    session: AsyncSession = Depends(get_db),
):
    normalized_email = email.strip().lower()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", normalized_email):
        raise HTTPException(status_code=422, detail="A valid customer email is required.")

    result = await session.execute(
        select(PurchaseOrder)
        .join(PurchaseOrder.customer)
        .options(selectinload(PurchaseOrder.customer), selectinload(PurchaseOrder.items))
        .where(Customer.email == normalized_email)
        .order_by(PurchaseOrder.created_at.desc())
    )
    return [serialize_order(order) for order in result.scalars().all()]


@router.get("/seller/orders", response_model=list[PurchaseRead])
async def seller_orders(
    limit: int = Query(default=500, ge=1, le=2000),
    session: AsyncSession = Depends(get_db),
):
    result = await session.execute(
        select(PurchaseOrder)
        .options(selectinload(PurchaseOrder.customer), selectinload(PurchaseOrder.items))
        .where(PurchaseOrder.status == "paid")
        .order_by(PurchaseOrder.created_at.desc())
        .limit(limit)
    )
    return [serialize_order(order) for order in result.scalars().all()]
