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
    return {"version": APP_VERSION, "environment": ENVIRONMENT, "db_host": DB_HOST}


@app.get("/payment/calculate")
def calculate_payment():
    """
    PAYMENT DEFECT (v4.2.0, current code below):
    Tax is calculated on the full amount BEFORE the flat discount voucher
    is subtracted, then the voucher is subtracted from the taxed total.
    That means the customer effectively pays tax on money they never
    actually spent (the discounted portion) -- an overcharge. This is the
    bug Task 1 asks you to fix on the hotfix/payment-4.2.1 branch.

    Buggy:  total = (amount * (1 + tax_rate)) - discount_amount
    Fixed:  total = (amount - discount_amount) * (1 + tax_rate)

    These are NOT the same number when the discount is a flat amount
    (they would be identical if it were a percentage -- multiplication
    order doesn't matter for percentages, which is why this uses a flat
    voucher amount instead). The difference here is exactly
    discount_amount * tax_rate = $1.20 per order.

    To apply the hotfix, replace the two lines below with:
        discounted = amount - discount_amount
        total = discounted * (1 + tax_rate)
    then commit with a message like:
        "fix: apply discount voucher before tax in payment calculation"
    """
    amount = 100.0
    tax_rate = 0.08
    discount_amount = 15.0

    discounted = amount - discount_amount
    total = discounted * (1 + tax_rate)
    
    return {"amount": amount, "total": round(total, 2), "version": APP_VERSION}
