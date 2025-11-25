# routers/stripe_webhooks.py

from fastapi import APIRouter, Request, status

router = APIRouter()


@router.post("/webhooks/stripe", status_code=status.HTTP_200_OK)
async def stripe_webhook(request: Request):
    """
    Minimaler Stripe-Webhook-Endpoint.
    – Nimmt den Request entgegen
    – Liest den Body (für später)
    – Gibt erstmal nur 200 OK zurück.
    """
    raw_body = await request.body()
    # aktuell wird raw_body noch nicht verwendet, ist aber schon da
    return {"received": True}
