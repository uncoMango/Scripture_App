import os
import stripe
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
import access
import email_utils

router = APIRouter(prefix="/stripe")

stripe.api_key  = os.environ.get("STRIPE_SECRET_KEY", "")
_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
_PRICE_ID       = os.environ.get("STRIPE_PRICE_ID", "")
_BASE_URL       = os.environ.get("APP_BASE_URL", "https://scripture-app.onrender.com")


@router.post("/create-checkout-session")
async def create_checkout_session():
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": _PRICE_ID, "quantity": 1}],
            mode="payment",
            success_url=f"{_BASE_URL}/stripe/success",
            cancel_url=f"{_BASE_URL}/stripe/cancel",
        )
        return {"url": session.url}
    except stripe.error.StripeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/webhook")
async def webhook(request: Request):
    payload    = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, _WEBHOOK_SECRET)
    except (ValueError, stripe.error.SignatureVerificationError):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    if event["type"] == "checkout.session.completed":
        session_obj      = event["data"]["object"]
        customer_details = session_obj.get("customer_details") or {}
        email            = customer_details.get("email", "")
        if email:
            code = access.generate_code(email)
            email_utils.send_access_code_email(email, code)

    return {"status": "ok"}


def _simple_page(title: str, heading: str, body: str, link_href: str, link_label: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} — Ke Aupuni O Ke Akua</title>
  <style>
    body {{ font-family: 'Helvetica Neue', Arial, sans-serif; background: #0f0d0a;
           color: #e8dfc8; display: flex; align-items: center;
           justify-content: center; min-height: 100vh; margin: 0; padding: 1.5rem; }}
    .box {{ max-width: 460px; width: 100%; text-align: center; }}
    h1 {{ font-size: 1.1rem; color: #c8972a; letter-spacing: 0.08em;
          text-transform: uppercase; margin-bottom: 1rem; }}
    p {{ color: #9a8e78; font-size: 0.88rem; line-height: 1.85; margin-bottom: 1.75rem; }}
    a {{ display: inline-block; background: #7a5a18; color: #f0e8d0; text-decoration: none;
         padding: 0.7rem 1.6rem; border-radius: 4px; font-size: 0.82rem; font-weight: 600;
         letter-spacing: 0.07em; text-transform: uppercase; }}
    a:hover {{ background: #c8972a; color: #1a1610; }}
  </style>
</head>
<body>
  <div class="box">
    <h1>{heading}</h1>
    <p>{body}</p>
    <a href="{link_href}">{link_label}</a>
  </div>
</body>
</html>"""


@router.get("/success", response_class=HTMLResponse)
async def success():
    return _simple_page(
        title="Payment Complete",
        heading="Payment Complete",
        body="Your access code is on its way — check your email. It usually arrives within "
             "a minute. Enter the code on the unlock page to start studying.",
        link_href="/unlock",
        link_label="Enter my code →",
    )


@router.get("/cancel", response_class=HTMLResponse)
async def cancel():
    return _simple_page(
        title="Payment Cancelled",
        heading="Payment Cancelled",
        body="No charge was made. You can try again whenever you're ready.",
        link_href="/unlock",
        link_label="← Back",
    )
