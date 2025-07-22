from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from models.order import Order
from models.user import User
from models.payment import PaymentTransaction
from core.security import get_current_user
from core.database import get_db
import stripe
import paypalrestsdk
import os
import requests
from core.email_utils import send_email, render_template
from datetime import datetime

payment_router = APIRouter(prefix="/payments", tags=["payments"])

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_...")
paypalrestsdk.configure(
    {
        "mode": os.getenv("PAYPAL_MODE", "sandbox"),
        "client_id": os.getenv("PAYPAL_CLIENT_ID", "your-client-id"),
        "client_secret": os.getenv("PAYPAL_CLIENT_SECRET", "your-client-secret"),
    }
)


@payment_router.post("/stripe/{order_id}")
def pay_with_stripe(
    order_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    idempotency_key: str = Header(None),
):
    order = (
        db.query(Order).filter(Order.id == order_id, Order.user_id == user.id).first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != "pending":
        raise HTTPException(status_code=400, detail="Order already paid or cancelled")
    stripe_args = {
        "amount": int(order.total_amount * 100),
        "currency": "usd",
        "metadata": {"order_id": order.id, "user_id": user.id},
    }
    if idempotency_key:
        intent = stripe.PaymentIntent.create(
            **stripe_args, idempotency_key=idempotency_key
        )
    else:
        intent = stripe.PaymentIntent.create(**stripe_args)
    return {"client_secret": intent.client_secret}


@payment_router.post("/stripe/confirm/{order_id}")
def confirm_stripe_payment(
    order_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    return {
        "status": "pending",
        "order_id": order_id,
        "message": "Order will be marked as paid after Stripe webhook confirmation.",
    }


@payment_router.post("/paypal/{order_id}")
def pay_with_paypal(
    order_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    order = (
        db.query(Order).filter(Order.id == order_id, Order.user_id == user.id).first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != "pending":
        raise HTTPException(status_code=400, detail="Order already paid or cancelled")
    existing_txn = (
        db.query(PaymentTransaction)
        .filter_by(order_id=order.id, provider="paypal")
        .first()
    )
    if existing_txn:
        raise HTTPException(
            status_code=409, detail="Payment already initiated for this order."
        )
    payment = paypalrestsdk.Payment(
        {
            "intent": "sale",
            "payer": {"payment_method": "paypal"},
            "redirect_urls": {
                "return_url": "http://localhost:8000/payments/paypal/confirm/{order_id}",
                "cancel_url": "http://localhost:8000/payments/paypal/cancel/{order_id}",
            },
            "transactions": [
                {
                    "amount": {"total": f"{order.total_amount:.2f}", "currency": "USD"},
                    "description": f"Order #{order.id}",
                }
            ],
        }
    )
    if payment.create():
        for link in payment.links:
            if link.rel == "approval_url":
                return {"approval_url": link.href}
        raise HTTPException(status_code=500, detail="No approval URL found")
    else:
        raise HTTPException(status_code=500, detail="PayPal payment creation failed")


@payment_router.get("/paypal/confirm/{order_id}")
def confirm_paypal_payment(
    order_id: int,
    paymentId: str,
    PayerID: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return {
        "status": "pending",
        "order_id": order_id,
        "message": "Order will be marked as paid after PayPal webhook confirmation.",
    }


@payment_router.post("/stripe/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_...")
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    if event["type"] == "payment_intent.succeeded":
        intent = event["data"]["object"]
        order_id = intent["metadata"].get("order_id")
        transaction_id = intent["id"]
        amount = intent["amount"] / 100.0
        order = db.query(Order).filter(Order.id == order_id).first()
        if order and order.status == "pending":
            order.status = "paid"
            txn = PaymentTransaction(
                order_id=order.id,
                provider="stripe",
                transaction_id=transaction_id,
                status="succeeded",
                amount=amount,
                raw_response=intent,
            )
            db.add(txn)
            db.commit()
            # Send payment receipt email
            user = db.query(User).filter(User.id == order.user_id).first()
            html_body = render_template(
                "payment_receipt_email.html",
                full_name=user.full_name,
                order_id=order.id,
                amount=amount,
                payment_method="Stripe",
                date=str(datetime.utcnow()),
            )
            send_email(
                str(user.email),
                "Payment Receipt",
                f"Payment received for order #{order.id}.",
                html_body=html_body,
            )
    return {"status": "ok"}


@payment_router.post("/paypal/webhook")
async def paypal_webhook(request: Request, db: Session = Depends(get_db)):
    event = await request.json()
    verify_url = os.getenv(
        "PAYPAL_WEBHOOK_VERIFY_URL",
        "https://api.sandbox.paypal.com/v1/notifications/verify-webhook-signature",
    )
    auth = (os.getenv("PAYPAL_CLIENT_ID", ""), os.getenv("PAYPAL_CLIENT_SECRET", ""))
    headers = {"Content-Type": "application/json"}
    transmission_id = request.headers.get("paypal-transmission-id")
    transmission_time = request.headers.get("paypal-transmission-time")
    cert_url = request.headers.get("paypal-cert-url")
    auth_algo = request.headers.get("paypal-auth-algo")
    transmission_sig = request.headers.get("paypal-transmission-sig")
    webhook_id = os.getenv("PAYPAL_WEBHOOK_ID", "")
    verify_payload = {
        "auth_algo": auth_algo,
        "cert_url": cert_url,
        "transmission_id": transmission_id,
        "transmission_sig": transmission_sig,
        "transmission_time": transmission_time,
        "webhook_id": webhook_id,
        "webhook_event": event,
    }
    resp = requests.post(verify_url, json=verify_payload, auth=auth, headers=headers)
    if resp.status_code != 200 or resp.json().get("verification_status") != "SUCCESS":
        raise HTTPException(status_code=400, detail="Invalid PayPal webhook signature")
    if event.get("event_type") == "PAYMENT.SALE.COMPLETED":
        resource = event["resource"]
        invoice_id = resource.get("invoice_number")
        transaction_id = resource["id"]
        amount = float(resource["amount"]["total"])
        order = db.query(Order).filter(Order.id == invoice_id).first()
        if order and order.status == "pending":
            order.status = "paid"
            txn = PaymentTransaction(
                order_id=order.id,
                provider="paypal",
                transaction_id=transaction_id,
                status="completed",
                amount=amount,
                raw_response=resource,
            )
            db.add(txn)
            db.commit()
            # Send payment receipt email
            user = db.query(User).filter(User.id == order.user_id).first()
            html_body = render_template(
                "payment_receipt_email.html",
                full_name=user.full_name,
                order_id=order.id,
                amount=amount,
                payment_method="PayPal",
                date=str(datetime.utcnow()),
            )
            send_email(
                str(user.email),
                "Payment Receipt",
                f"Payment received for order #{order.id}.",
                html_body=html_body,
            )
    return {"status": "ok"}
