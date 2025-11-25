from fastapi import APIRouter, Header, HTTPException, Request, status
from typing import Any, Mapping
from datetime import datetime
import json

import stripe

import config
from storage import orders_store

router = APIRouter()

# Stripe API-Key (für spätere Nutzung, z. B. Event-API etc.)
stripe.api_key = config.STRIPE_SECRET_KEY


def process_stripe_event(event: Mapping[str, Any]) -> None:
    """
    Verarbeitet Stripe-Events, die uns interessieren.

    Aktuell:
    – checkout.session.completed:
      * client_reference_id = Order-ID
      * setzt Order-Status auf "paid" (falls noch nicht paid/provisioned)
      * speichert Session-ID und PaymentIntent-ID
    """
    event_type = event.get("type")
    if event_type != "checkout.session.completed":
        # Alles andere ignorieren wir vorerst
        return

    data = event.get("data") or {}
    session = (data.get("object") or {})  # Stripe Checkout-Session

    order_id = session.get("client_reference_id")
    if not order_id:
        # Ohne Referenz zur Order können wir nichts tun
        return

    order = orders_store.get(order_id)
    if order is None:
        # Order existiert nicht (könnte theoretisch gelöscht worden sein)
        return

    # Idempotenz: wenn Order schon bezahlt oder provisioniert ist, nichts machen
    if order.status in ("paid", "provisioned"):
        return

    order.status = "paid"
    order.stripe_session_id = session.get("id")
    order.stripe_payment_intent = session.get("payment_intent")
    order.updated_at = datetime.utcnow()

    orders_store.update(order)


@router.post("/webhooks/stripe", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(default=None, alias="Stripe-Signature"),
):
    """
    Stripe-Webhook-Endpoint.

    – Liest den Body
    – Prüft optional die Signatur (wenn STRIPE_WEBHOOK_SECRET gesetzt ist)
    – Ruft process_stripe_event(...) auf
    """

    raw_body = await request.body()

    # Dev/Tests: kein Webhook-Secret gesetzt → keine Signaturprüfung,
    # aber wir verarbeiten das Event trotzdem.
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

    # Ab hier: „echter“ Betrieb mit Signaturprüfung
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
        # JSON oder Payload kaputt
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payload",
        )
    except stripe.error.SignatureVerificationError:
        # Signatur stimmt nicht
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signature",
        )

    process_stripe_event(event)
    return {"received": True, "type": event["type"]}
