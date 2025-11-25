# routers/orders.py
from fastapi import APIRouter, HTTPException, status
from datetime import datetime, UTC

from models import Order, OrderCreate
from storage import orders_store

router = APIRouter()


@router.post("/orders", response_model=Order, status_code=status.HTTP_201_CREATED)
async def create_order(order_in: OrderCreate) -> Order:
    """
    Neue Bestellung anlegen.
    – status = "pending"
    – id, timestamps kommen aus dem Order-Modell
    """
    order = Order(
        product_type=order_in.product_type,
        instance_slug=order_in.instance_slug,
        domain=order_in.domain,
    )
    # hier könnte später Validierung für slug/domain rein
    orders_store.add(order)
    return order


@router.get("/orders/{order_id}", response_model=Order)
async def get_order(order_id: str) -> Order:
    """
    Eine Bestellung per ID abrufen.
    """
    order = orders_store.get(order_id)
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    return order

@router.post("/orders/{order_id}/cancel", response_model=Order)
async def cancel_order(order_id: str) -> Order:
    """
    Markiert eine Bestellung als 'canceled'.

    Regeln:
    – Wenn Order nicht existiert → 404
    – Wenn Order bereits 'provisioned' → 409 Conflict
    – Wenn Order bereits 'canceled' → einfach zurückgeben (idempotent)
    – Sonst: Status auf 'canceled' setzen und speichern
    """
    order = orders_store.get(order_id)
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    if order.status == "provisioned":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Order already provisioned",
        )

    if order.status == "canceled":
        return order

    order.status = "canceled"
    order.updated_at = datetime.now(UTC)
    orders_store.update(order)
    return order
