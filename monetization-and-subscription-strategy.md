# Monetization & Subscription Strategy: FamFin-AI

This document outlines the business model, competitor benchmark, in-app payment mechanisms (Telegram Stars & Stripe), pricing tiers, and technical implementation plan for monetizing **FamFin-AI**.

---

## 1. Executive Summary

* **Monetization Engine:** In-app native subscriptions via **Telegram Stars (`XTR`)** with optional **Stripe** fallback.
* **Pricing Sweet Spot:** **$2.99 / month** (Solo Pro) and **$5.99 / month** (Family Pro).
* **Unit Economics:** Cloud infrastructure costs **~$0.00 to $0.09 / user / month**, resulting in a **> 95% net profit margin**.

---

## 2. In-App Payment Mechanisms: Telegram Stars vs Stripe

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       TELEGRAM STARS PAYMENT FLOW                           │
│                                                                             │
│ [ User Taps "Upgrade" ] ──► [ Native Apple Pay / Google Pay / Card ]        │
│                                           │                                 │
│                                           ▼ (1 Tap - Zero Card Entry)       │
│                               [ Telegram Stars (XTR) ]                      │
│                                           │                                 │
│                                           ▼                                 │
│                   [ FamFin API: successful_payment Webhook ]                │
│                                           │                                 │
│                                           ▼                                 │
│                     [ SQLModel: family.plan_type = "pro" ]                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Option A: Telegram Stars (Recommended for Bots)
Telegram Stars is the official, Apple/Google-compliant digital currency for Telegram bots and mini-apps.

* **Frictionless 1-Tap Checkout:** Users pay using **Apple Pay, Google Pay, or saved cards** directly within the Telegram UI. They never leave the chat or re-enter billing details.
* **App Store & Play Store Compliance:** Digital goods in iOS/Android apps require in-app purchases. Telegram Stars complies 100% with App Store rules.
* **Developer Payouts:** Stars can be withdrawn into **USD (Bank Transfer)** or **Toncoin (TON)** via Telegram's official platform (**[Fragment.com](https://fragment.com)**).
* **Bot API Integration:** Implemented via standard Bot API methods: `sendInvoice` (with currency `XTR`), `answerPreCheckoutQuery`, and handling `successful_payment`.

### Option B: Stripe / External Web Checkout
* **Usage:** Best for web dashboards or users who prefer direct Stripe invoices.
* **Flow:** The bot sends a Stripe Checkout URL (`https://buy.stripe.com/...`). Once paid, Stripe webhooks update the user's account.

### 🔒 Security & Compliance
* **PCI-DSS Compliance:** The FamFin backend **never stores, sees, or processes credit card numbers**.
* **Cryptographic Signatures:** Telegram signs all payment payloads; webhooks are validated using secret tokens and transaction IDs.

---

## 3. 🔍 Competitor & Market Analysis

We evaluated the primary AI financial bots across Telegram and WhatsApp:

| Competitor | Platform | Pricing Model | Price Points | Key Features |
|---|---|---|---|---|
| **POQT** | WhatsApp | 7-Day Free Trial → Monthly Sub | **$4.99 / month** | Voice/Text logging, monthly spending summaries |
| **Auritrack** | Telegram | Freemium | **$3.99 / month** ($35/yr) | Basic free logging; Pro unlocks bank statements & charts |
| **TrackFi** | WhatsApp | Freemium | **$5.99 / month** | Receipt scanning, business vs personal tagging |
| **Cleo AI** | Chat / App | Freemium Subscription | **$5.99 – $9.99 / month** | AI financial roast, budgeting, credit tracking |

---

## 4. 💎 Recommended 3-Tier Pricing Model

FamFin-AI’s competitive advantage is **multi-user family synchronization** and **AES-256 zero-knowledge encryption**.

```
┌───────────────────────────┬───────────────────────────┬───────────────────────────┐
│        FREE TIER          │         SOLO PRO          │        FAMILY PRO         │
│         $0.00             │      $2.99 / month        │      $5.99 / month        │
│                           │      ($24.99 / year)      │      ($49.99 / year)      │
├───────────────────────────┼───────────────────────────┼───────────────────────────┤
│ • 30 transactions / month │ • Unlimited text & voice  │ • Everything in Solo Pro  │
│ • Text & Voice logging    │ • AI Natural Language     │ • Up to 5 Family Members  │
│ • 1 Single User           │   Queries (Epic 3)        │ • Shared vs Private Views │
│ • AES-256 Encryption      │ • CSV / PDF Data Export   │ • Notion Mirroring Sync   │
│                           │ • 1 Single User           │ • Family Budget Alerts    │
└───────────────────────────┴───────────────────────────┴───────────────────────────┘
```

---

## 5. 🛠️ Technical Architecture & Implementation Plan

### Step 5.1: Database Schema Expansion (`Family` Table)
Expand the `Family` model in `src/db/models.py` to store subscription status and quotas:

```python
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field

class Family(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Subscription Fields
    plan_type: str = Field(default="free")                # "free", "solo_pro", "family_pro"
    subscription_status: str = Field(default="active")    # "active", "expired", "cancelled"
    monthly_tx_count: int = Field(default=0)
    current_period_end: Optional[datetime] = None
    telegram_payment_charge_id: Optional[str] = None
```

### Step 5.2: In-App Invoice Generation (`sendInvoice`)
When a user types `/upgrade` or reaches their free tier quota, the bot issues a Telegram Stars invoice:

```python
async def send_subscription_invoice(chat_id: int, plan: str):
    prices = {
        "solo_pro": {"stars": 150, "title": "FamFin Solo Pro (1 Month)"},
        "family_pro": {"stars": 300, "title": "FamFin Family Pro (1 Month)"}
    }
    selected = prices[plan]
    
    payload = {
        "chat_id": chat_id,
        "title": selected["title"],
        "description": "Unlock unlimited AI voice logging, natural language insights, and family sync.",
        "payload": f"sub_{plan}_{chat_id}",
        "currency": "XTR",  # Telegram Stars currency code
        "prices": [{"label": selected["title"], "amount": selected["stars"]}]
    }
    
    async with httpx.AsyncClient() as client:
        await client.post(
            f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendInvoice",
            json=payload
        )
```

### Step 5.3: Webhook Verification & Activation
Handle `pre_checkout_query` and `successful_payment` in the FastAPI webhook handler:

```python
# 1. Telegram pre-checkout validation (must respond within 10s)
if update.get("pre_checkout_query"):
    query_id = update["pre_checkout_query"]["id"]
    await answer_pre_checkout(query_id, ok=True)

# 2. Payment confirmed
if message.get("successful_payment"):
    payment = message["successful_payment"]
    # Activate subscription in PostgreSQL
    activate_subscription(
        user_id=message["from"]["id"],
        plan=payment["invoice_payload"],
        charge_id=payment["telegram_payment_charge_id"]
    )
```

### Step 5.4: Quota Gating Logic
Before processing an expense in `MessagingService`:
```python
if family.plan_type == "free" and family.monthly_tx_count >= 30:
    return {
        "action": "reply",
        "text": "⚠️ You have reached your 30 free transactions this month.\n\nType /upgrade to unlock unlimited text, voice logging, and AI insights!"
    }
```

---

## 6. 📊 Revenue Projections

Assuming standard Telegram Bot conversion benchmarks (5% to 8% free-to-paid conversion):

| Active Users | Paid Subscribers (7%) | Avg Price / Mo | Monthly Revenue | Monthly Cloud Cost | Net Monthly Profit |
|---|---|---|---|---|---|
| **100** | 7 users | $4.50 | **$31.50** | $0.00 (Free Tier) | **$31.50 (100%)** |
| **500** | 35 users | $4.50 | **$157.50** | $0.00 – $45.00 | **~$125.00 (80%)** |
| **2,500** | 175 users | $4.50 | **$787.50** | ~$60.00 | **~$727.50 (92%)** |
| **10,000** | 700 users | $4.50 | **$3,150.00** | ~$120.00 | **~$3,030.00 (96%)** |
| **50,000** | 3,500 users | $4.50 | **$15,750.00** | ~$450.00 | **~$15,300.00 (97%)** |

---

## 7. Next Actions for Roadmap

1. **Include Subscription Fields in Epic 5 / 6 Schema.**
2. **Add `/upgrade` Command and Telegram Stars Invoice Scaffolding.**
3. **Register Bot with BotFather Payments (`/mybots > Bot Settings > Payments > Telegram Stars`).**
