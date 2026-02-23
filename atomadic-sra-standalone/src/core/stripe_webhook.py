"""
stripe_webhook.py — M10 Stripe Webhook Handler
SRA-HelixEvolver v7.0 | Atomadic Tech Inc.

Handles Stripe subscription events for SRA SaaS tiers.
Integrates with Flask app.py server routes.

Pricing tiers:
  starter:    $99/mo  — 5 panel runs/mo
  pro:       $299/mo  — unlimited panels
  enterprise: custom  — white-label + API access

Audit: τ=1.0, ΔL>0
"""

import json
import hashlib
import hmac
import os
from datetime import datetime, timezone
from pathlib import Path

__version__ = "1.0.0"

ROOT = Path(__file__).parent.parent.parent

# ── Stripe config (set in .env) ────────────────────────────────────────────────
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "whsec_placeholder")
STRIPE_API_KEY        = os.environ.get("STRIPE_API_KEY", "sk_test_placeholder")

PRICE_TIERS = {
    "starter":    {"price_usd": 99,  "panel_runs": 5,         "label": "Starter"},
    "pro":        {"price_usd": 299, "panel_runs": float("inf"), "label": "Pro"},
    "enterprise": {"price_usd": None,"panel_runs": float("inf"), "label": "Enterprise"},
}

# ── Subscription store (file-backed for now; swap for DB later) ────────────────
_SUB_STORE_PATH = ROOT / "data" / "subscriptions.json"


def _load_subscribers() -> dict:
    if _SUB_STORE_PATH.exists():
        try:
            return json.loads(_SUB_STORE_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_subscribers(subs: dict) -> None:
    _SUB_STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _SUB_STORE_PATH.write_text(json.dumps(subs, indent=2), encoding="utf-8")


# ── Signature verification ─────────────────────────────────────────────────────

def verify_stripe_signature(payload: bytes, sig_header: str, secret: str) -> bool:
    """
    Verify Stripe webhook signature (HMAC-SHA256, t+v1 scheme).
    Returns True if valid.
    """
    try:
        parts = {k: v for k, v in (item.split("=", 1) for item in sig_header.split(","))}
        ts    = parts.get("t", "")
        v1    = parts.get("v1", "")
        signed_payload = f"{ts}.{payload.decode('utf-8')}"
        expected = hmac.new(
            secret.encode("utf-8"),
            signed_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, v1)
    except Exception:
        return False


# ── Event handlers ─────────────────────────────────────────────────────────────

def _handle_checkout_completed(event: dict) -> dict:
    """customer.subscription.created or checkout.session.completed."""
    obj = event.get("data", {}).get("object", {})
    customer_id = obj.get("customer", "")
    email       = obj.get("customer_email", "") or obj.get("customer_details", {}).get("email", "")
    tier_key    = _resolve_tier(obj)
    subs        = _load_subscribers()
    subs[customer_id] = {
        "email": email,
        "tier": tier_key,
        "panel_runs_remaining": PRICE_TIERS.get(tier_key, {}).get("panel_runs", 5),
        "subscribed_at": datetime.now(timezone.utc).isoformat(),
        "active": True,
    }
    _save_subscribers(subs)
    print(f"[Stripe] ✓ New subscriber: {email} → {tier_key}")
    return {"status": "ok", "customer": customer_id, "tier": tier_key}


def _handle_subscription_deleted(event: dict) -> dict:
    """customer.subscription.deleted — deactivate."""
    obj = event.get("data", {}).get("object", {})
    customer_id = obj.get("customer", "")
    subs = _load_subscribers()
    if customer_id in subs:
        subs[customer_id]["active"] = False
        subs[customer_id]["cancelled_at"] = datetime.now(timezone.utc).isoformat()
        _save_subscribers(subs)
        print(f"[Stripe] ✗ Cancelled: {customer_id}")
    return {"status": "ok", "customer": customer_id, "active": False}


def _handle_invoice_paid(event: dict) -> dict:
    """invoice.paid — reset monthly panel run quota."""
    obj = event.get("data", {}).get("object", {})
    customer_id = obj.get("customer", "")
    amount_usd  = obj.get("amount_paid", 0) / 100
    subs = _load_subscribers()
    if customer_id in subs:
        tier_key = subs[customer_id].get("tier", "starter")
        subs[customer_id]["panel_runs_remaining"] = PRICE_TIERS[tier_key]["panel_runs"]
        subs[customer_id]["last_payment_usd"]    = amount_usd
        subs[customer_id]["last_payment_at"]     = datetime.now(timezone.utc).isoformat()
        _save_subscribers(subs)
        print(f"[Stripe] ✓ Invoice paid: {customer_id} ${amount_usd} — quota reset")
    return {"status": "ok", "customer": customer_id, "amount_usd": amount_usd}


def _resolve_tier(obj: dict) -> str:
    """Best-effort tier resolution from Stripe session/subscription object."""
    amount = obj.get("amount_total", obj.get("amount", 0)) or 0
    amount_usd = amount / 100
    if amount_usd <= 0:
        return "starter"
    elif amount_usd <= 150:
        return "starter"
    elif amount_usd <= 350:
        return "pro"
    else:
        return "enterprise"


# ── Main dispatch ──────────────────────────────────────────────────────────────

EVENT_HANDLERS = {
    "checkout.session.completed":   _handle_checkout_completed,
    "customer.subscription.created": _handle_checkout_completed,
    "customer.subscription.deleted": _handle_subscription_deleted,
    "invoice.paid":                  _handle_invoice_paid,
}


def handle_event(payload: bytes, sig_header: str) -> tuple[dict, int]:
    """
    Main entry point — verify signature then dispatch to handler.
    Returns (response_dict, http_status_code).

    Usage in Flask:
        from src.core.stripe_webhook import handle_event
        @app.route('/api/stripe/webhook', methods=['POST'])
        def stripe_webhook():
            response, status = handle_event(request.data, request.headers.get('Stripe-Signature',''))
            return jsonify(response), status
    """
    if not verify_stripe_signature(payload, sig_header, STRIPE_WEBHOOK_SECRET):
        return {"error": "Invalid signature"}, 400

    try:
        event = json.loads(payload)
    except json.JSONDecodeError:
        return {"error": "Invalid JSON"}, 400

    event_type = event.get("type", "")
    handler    = EVENT_HANDLERS.get(event_type)
    if handler:
        result = handler(event)
        return result, 200
    else:
        return {"status": "ignored", "type": event_type}, 200


# ── Subscription query helpers (for dashboard) ─────────────────────────────────

def get_subscriber(customer_id: str) -> dict | None:
    return _load_subscribers().get(customer_id)


def get_all_subscribers() -> list[dict]:
    subs = _load_subscribers()
    return [{"customer_id": k, **v} for k, v in subs.items()]


def get_mrr_estimate() -> dict:
    """Estimate MRR from active subscriptions."""
    subs   = _load_subscribers()
    active = [s for s in subs.values() if s.get("active")]
    mrr    = sum(PRICE_TIERS.get(s.get("tier", "starter"), {}).get("price_usd", 0) or 0
                 for s in active)
    return {
        "active_subscriptions": len(active),
        "estimated_mrr_usd": mrr,
        "estimated_arr_usd": mrr * 12,
        "tiers": {t: sum(1 for s in active if s.get("tier") == t) for t in PRICE_TIERS},
    }


def decrement_panel_run(customer_id: str) -> bool:
    """Consume one panel run. Returns False if quota exhausted."""
    subs = _load_subscribers()
    sub  = subs.get(customer_id)
    if not sub or not sub.get("active"):
        return False
    remaining = sub.get("panel_runs_remaining", 0)
    if remaining != float("inf") and remaining <= 0:
        return False
    if remaining != float("inf"):
        subs[customer_id]["panel_runs_remaining"] = remaining - 1
        _save_subscribers(subs)
    return True
