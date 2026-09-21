import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

APP_VERSION = os.environ.get("APP_VERSION", "4.2.0")
ENVIRONMENT = os.environ.get("ENVIRONMENT", "UNKNOWN")

# Set FORCE_HEALTH_FAIL=true at container run time to make /health return
# HTTP 500 on demand. This is how you trigger the mandatory failure-injection
# scenario (build v4.2.2, start it, watch Jenkins detect the bad health
# check and roll back to v4.2.1) without touching the app code again.
FORCE_HEALTH_FAIL = os.environ.get("FORCE_HEALTH_FAIL", "false").lower() == "true"

# Simulates the DB dependency used in Task 2/3. Point this at the real
# database host name (never "localhost") once you wire up a DB container.
DB_HOST = os.environ.get("DB_HOST", "")

REGION = os.environ.get("REGION", "us-east-1")


@app.get("/health")
def health():
    if FORCE_HEALTH_FAIL:
        return JSONResponse(
            status_code=500,
            content={"status": "unhealthy", "version": APP_VERSION},
        )
    return {"status": "healthy", "version": APP_VERSION, "environment": ENVIRONMENT}


@app.get("/version")
def version():
    return {
        "service": "retail-platform",
        "version": APP_VERSION,
        "environment": ENVIRONMENT,
        "db_host": DB_HOST,
        "region": REGION,
    }


@app.get("/orders/count")
def order_count():
    # Feature-branch stub (develop): represents in-progress work for the
    # next release, unrelated to the payment hotfix.
    return {"orders_today": 0, "version": APP_VERSION}


@app.get("/orders/latest")
def latest_order():
    # Feature-branch stub (develop): second example feature commit.
    return {"order_id": None, "version": APP_VERSION}


@app.get("/payment/calculate")
def calculate_payment():
    """
    PAYMENT DEFECT (v4.2.0, original buggy code):
    Tax was calculated on the full amount BEFORE the flat discount voucher
    was subtracted, then the voucher was subtracted from the taxed total.
    That meant the customer effectively paid tax on money they never
    actually spent (the discounted portion) -- an overcharge.

    FIXED (v4.2.1, hotfix/payment-4.2.1, merged here):
    Buggy:  total = (amount * (1 + tax_rate)) - discount_amount
    Fixed:  total = (amount - discount_amount) * (1 + tax_rate)

    Resolved via merge conflict from hotfix/payment-4.2.1 into develop:
    kept the fixed (discount-before-tax) logic.
    """
    amount = 100.0
    tax_rate = 0.08
    discount_amount = 15.0

    discounted = amount - discount_amount
    total = discounted * (1 + tax_rate)

    return {"amount": amount, "total": round(total, 2), "version": APP_VERSION}