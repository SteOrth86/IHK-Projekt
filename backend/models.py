# models.py

from datetime import datetime, UTC
from typing import Literal, Optional
from pydantic import BaseModel, Field
import uuid


OrderStatus = Literal["pending", "paid", "provisioned", "canceled"]
ProductType = Literal["wordpress", "odoo"]


class Order(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    product_type: ProductType
    instance_slug: str
    domain: str

    status: OrderStatus = "pending"

    stripe_session_id: Optional[str] = None
    stripe_payment_intent: Optional[str] = None

    instance_id: Optional[str] = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

class OrderCreate(BaseModel):
    """
    Payload für POST /orders
    – das, was der Client beim Bestellen schickt.
    """
    product_type: ProductType
    instance_slug: str
    domain: str
