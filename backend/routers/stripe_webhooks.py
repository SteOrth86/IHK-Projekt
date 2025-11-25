from fastapi import APIRouter, Header, HTTPException, Request, status
from typing import Any, Mapping
from datetime import datetime
import json

import stripe

import config
from storage import orders_store
from services import orders as orders_service  # neu: unser Order-Service

router = APIRouter()

stripe.api_key = config.STRIPE_SECRET_KEY


def process_stripe_event(event: Mapping[str, Any]) -> None:
    """
    Verarbeitet Stripe-Events, die uns interessieren.

    – checkout.session.completed:
      * client_reference_id = Order-ID
      * setzt Order-Status auf "paid"
      * ruft Provisionierung für WordPress-Orders auf
      * setzt Order-Status auf "provisioned" + instance_id
    """
    event_type = event.get("type")
    if event_type != "checkout.session.completed":
        # andere Events ignorieren wir vorerst
        return

    data = event.get("data") or {}
    session = (data.get("object") or {})  # Stripe Checkout-Session

    order_id = session.get("client_reference_id")
    if not order_id:
        return

    order = orders_store.get(order_id)
    if order is None:
        return

    # Wenn schon provisioniert, tun wir nichts mehr (idempotent)
    if order.status == "provisioned":
        return

    # Stripe-Daten immer aktualisieren
    order.stripe_session_id = session.get("id")
    order.stripe_payment_intent = session.get("payment_intent")
    order.updated_at = datetime.utcnow()

    # Wenn noch nicht bezahlt, erst mal auf "paid" setzen
    if order.status != "paid":
        order.status = "paid"
        orders_store.update(order)

    # Nur WordPress-Orders werden automatisch provisioniert
    if order.product_type != "wordpress":
        return

    # Provisionierung anstoßen (aktueller Stand: nur InstanceStore-Eintrag)
    instance = orders_service.provision_wordpress_for_order(order)

    order.status = "provisioned"
    order.instance_id = instance.id
    order.updated_at = datetime.utcnow()
    orders_store.update(order)


@router.post("/webhooks/stripe", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(default=None, alias="Stripe-Signature"),
):
    raw_body = await request.body()

    # Dev/Tests: kein Webhook-Secret → keine Signaturprüfung
    if not config.STRIPE_WEBHOOK_SECRET:
        try:
            event = json.loads(raw_body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            event = {}

        process_stripe_event(event)
        return {
            "received": True,
            "verification": "skipped",
            "type": event.get("type"),
        }

    # Prod: Signaturpflicht
    if stripe_signature is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Stripe-Signature header",
        )

    try:
        event = stripe.Webhook.construct_event(
            payload=raw_body,
            sig_header=stripe_signature,
            secret=config.STRIPE_WEBHOOK_SECRET,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payload",
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signature",
        )

    process_stripe_event(event)
    return {"received": True, "type": event["type"]}
