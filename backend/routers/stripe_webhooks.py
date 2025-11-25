# routers/stripe_webhooks.py

from fastapi import APIRouter, Header, HTTPException, Request, status
import stripe

import config

router = APIRouter()

# Stripe API-Key (für spätere Nutzung, z. B. Event-API etc.)
stripe.api_key = config.STRIPE_SECRET_KEY


@router.post("/webhooks/stripe", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(default=None, alias="Stripe-Signature"),
):
    """
    Stripe-Webhook-Endpoint.

    – Liest den Body
    – Prüft optional die Signatur (wenn STRIPE_WEBHOOK_SECRET gesetzt ist)
    – Gibt bei Erfolg 200 OK zurück
    """

    raw_body = await request.body()

    # Wenn kein Webhook-Secret gesetzt ist, sind wir vermutlich in Dev/Tests:
    # → keine Signaturprüfung, einfach akzeptieren.
    if not config.STRIPE_WEBHOOK_SECRET:
        return {"received": True, "verification": "skipped"}

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

    # Später werten wir den Event-Typ aus (checkout.session.completed etc.)
    return {"received": True, "type": event["type"]}
