# Chapter 6: VIN Lookup & Price Estimation

[← Previous: LLM & Fairness](05-llm-fairness.md) | [Back to Contents](../DOCUMENTATION.md) | [Next: Negotiation Chatbot →](07-negotiation-chatbot.md)

---

## 6.1 What Is a VIN?

A **Vehicle Identification Number (VIN)** is a unique 17-character code assigned to every vehicle manufactured. It encodes:

| Position | Meaning | Example |
|----------|---------|---------|
| 1–3 | World Manufacturer ID | `1HG` = Honda, USA |
| 4–8 | Vehicle attributes (model, engine, body) | `CR2F3` |
| 9 | Check digit | `8` |
| 10 | Model year | `P` = 2023 |
| 11 | Assembly plant | `A` |
| 12–17 | Production sequence | `123456` |

**Example VIN:** `1HGCR2F38PA123456` — This is a 2023 Honda Civic sedan.

### Why VIN Lookup Matters for Contract Review

When reviewing a car contract, verifying the vehicle through its VIN tells you:
1. **Is the vehicle description accurate?** — Does the contract say "2023 Honda Civic" and the VIN confirms it?
2. **Are there safety recalls?** — Has the manufacturer issued any recalls for this vehicle?
3. **Are there consumer complaints?** — Have other owners reported problems?

---

## 6.2 NHTSA Public APIs

The **National Highway Traffic Safety Administration (NHTSA)** provides free public APIs. No API key is required.

| API | URL Pattern | Returns |
|-----|------------|---------|
| VIN Decode | `vpic.nhtsa.dot.gov/api/vehicles/DecodeVin/{vin}?format=json` | Make, model, year, engine, body, etc. |
| Recalls | `api.nhtsa.gov/recalls/recallsByVehicle?make={}&model={}&modelYear={}` | Safety recall campaigns |
| Complaints | `api.nhtsa.gov/complaints/complaintsByVehicle?make={}&model={}&modelYear={}` | Consumer-reported issues |

### File: `backend/vin_service.py`

```python
"""
VIN Service — Vehicle Information via NHTSA public APIs.

Endpoints covered:
  1. VIN Decode  → vehicle make, model, year, trim, engine, etc.
  2. Recalls     → NHTSA recall campaigns for the vehicle
  3. Complaints  → consumer complaints filed with NHTSA

All data is persisted to the database for reuse.
"""

import logging
import requests
from backend.db import save_vehicle, save_vehicle_recalls

logger = logging.getLogger(__name__)

NHTSA_DECODE_URL = "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVin/{vin}?format=json"
NHTSA_RECALLS_URL = "https://api.nhtsa.gov/recalls/recallsByVehicle?make={make}&model={model}&modelYear={year}"
NHTSA_COMPLAINTS_URL = "https://api.nhtsa.gov/complaints/complaintsByVehicle?make={make}&model={model}&modelYear={year}"

REQUEST_TIMEOUT = 15
```

### VIN Decode Function

```python
def _decode_vin_raw(vin: str) -> dict:
    """Call NHTSA VIN Decode API and return a flat dict of all non-empty fields."""
    url = NHTSA_DECODE_URL.format(vin=vin)
    resp = requests.get(url, timeout=REQUEST_TIMEOUT)

    if resp.status_code != 200:
        raise ConnectionError(f"NHTSA VIN decode returned {resp.status_code}")

    data = resp.json().get("Results", [])
    result = {}
    for item in data:
        if item.get("Value") and item["Value"].strip():
            result[item["Variable"]] = item["Value"].strip()
    return result


def decode_vin(vin: str) -> dict:
    """Decode a VIN and return structured vehicle information."""
    raw = _decode_vin_raw(vin)

    vehicle = {
        "vin": vin,
        "make": raw.get("Make"),
        "model": raw.get("Model"),
        "year": raw.get("Model Year"),
        "trim": raw.get("Trim"),
        "body_class": raw.get("Body Class"),
        "engine": raw.get("Engine Model"),
        "fuel_type": raw.get("Fuel Type - Primary"),
        "drive_type": raw.get("Drive Type"),
        "plant_info": raw.get("Plant Company Name"),
        "raw_nhtsa": raw,
    }

    # Additional fields for display
    vehicle["extra"] = {
        "manufacturer": raw.get("Manufacturer Name"),
        "plant_country": raw.get("Plant Country"),
        "vehicle_type": raw.get("Vehicle Type"),
        "doors": raw.get("Doors"),
        "cylinders": raw.get("Engine Number of Cylinders"),
        "transmission": raw.get("Transmission Style"),
    }

    # Persist to database
    try:
        vehicle_id = save_vehicle(vehicle)
        vehicle["vehicle_id"] = vehicle_id
    except Exception as e:
        logger.warning("Failed to save vehicle to DB: %s", e)
        vehicle["vehicle_id"] = None

    return vehicle
```

**Why we save to the database:** VIN decoding requires an HTTP call to NHTSA servers. By saving results, we avoid redundant API calls for the same VIN. This is a simple **caching** strategy.

### Recalls Function

```python
def get_recalls(make: str, model: str, year: str) -> list:
    """Fetch recall campaigns from NHTSA for a specific vehicle."""
    url = NHTSA_RECALLS_URL.format(make=make, model=model, year=year)

    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            return []

        results = resp.json().get("results", [])
        recalls = []
        for item in results:
            recalls.append({
                "nhtsa_campaign": item.get("NHTSACampaignNumber"),
                "component": item.get("Component"),
                "summary": item.get("Summary"),
                "consequence": item.get("Consequence"),
                "remedy": item.get("Remedy"),
                "report_date": item.get("ReportReceivedDate"),
            })
        return recalls

    except Exception as e:
        logger.warning("Recalls API call failed: %s", e)
        return []
```

### Combined Lookup (Main Entry Point)

```python
def get_vehicle_details(vin: str) -> dict:
    """Full vehicle lookup: decode VIN + fetch recalls + fetch complaints."""
    vehicle = decode_vin(vin)

    make = vehicle.get("make")
    model = vehicle.get("model")
    year = vehicle.get("year")

    recalls = []
    complaints = []
    if make and model and year:
        recalls = get_recalls(make, model, year)
        complaints = get_complaints(make, model, year)

        # Save recalls to DB
        if recalls and vehicle.get("vehicle_id"):
            try:
                save_vehicle_recalls(vehicle["vehicle_id"], recalls)
            except Exception:
                pass

    return {
        "vehicle": {
            "vin": vin, "make": make, "model": model, "year": year,
            "trim": vehicle.get("trim"),
            "body_class": vehicle.get("body_class"),
            # ... other fields
        },
        "recalls": recalls,
        "recalls_count": len(recalls),
        "complaints": complaints[:10],   # Limit for response size
        "complaints_count": len(complaints),
    }
```

---

## 6.3 Price Estimation Engine

### The Problem

How do you know if the price on your contract is fair? You need to compare it against the **fair market value** of the vehicle. Our price estimation engine calculates this using:

1. **MSRP (Manufacturer's Suggested Retail Price)** — the original sticker price
2. **Depreciation** — how much value the car has lost based on age
3. **Mileage adjustment** — high mileage reduces value
4. **Condition multiplier** — physical condition affects price

### File: `backend/price_service.py`

#### Step 1: MSRP Database

We maintain a built-in database of vehicle prices. Here's a sample:

```python
MSRP_DATABASE = {
    "toyota": {
        "camry":   {2024: 28855, 2023: 27515, 2022: 26420, 2021: 25965, ...},
        "corolla": {2024: 22995, 2023: 22195, 2022: 21550, ...},
        "rav4":    {2024: 30090, 2023: 29350, 2022: 28475, ...},
    },
    "honda": {
        "civic":   {2024: 24650, 2023: 24250, 2022: 23645, ...},
        "accord":  {2024: 28990, 2023: 28390, 2022: 27615, ...},
        "cr-v":    {2024: 30750, 2023: 30550, 2022: 29615, ...},
    },
    "ford": {
        "f-150":   {2024: 36765, 2023: 35665, 2022: 33695, ...},
        "mustang": {2024: 32515, 2023: 30920, 2022: 28865, ...},
    },
    # ... 10+ makes, 25+ models
}
```

**Why a built-in database?** Paid APIs like KBB (Kelley Blue Book) or Edmunds charge per-request. For a project/prototype, a static MSRP database provides good estimates for free.

#### Step 2: Depreciation Curve

Cars lose value predictably over time. The formula we use:

```python
DEPRECIATION_CURVE = {
    0: 1.00,    # Brand new = 100% of MSRP
    1: 0.80,    # 1 year old = 80% of MSRP (20% first-year drop)
    2: 0.72,    # 2 years = 72%
    3: 0.64,    # 3 years = 64%
    4: 0.56,    # 4 years = 56%
    5: 0.49,    # 5 years = 49%
    6: 0.42,
    7: 0.36,
    8: 0.31,
    9: 0.27,
    10: 0.23,
}

def _get_depreciation_factor(age: int) -> float:
    """Get depreciation multiplier based on vehicle age."""
    if age <= 0:
        return 1.0
    if age >= 10:
        return max(0.15, 0.23 - (age - 10) * 0.02)  # Floor at 15%
    return DEPRECIATION_CURVE.get(age, 0.23)
```

**Real-world basis:** According to AAA and iSeeCars research, a new car loses approximately:
- **20%** in the first year
- **15%** per year for years 2–5
- **8–10%** per year after that

#### Step 3: Mileage and Condition Adjustments

```python
def _mileage_adjustment(mileage: int, age: int) -> float:
    """
    Adjust price based on mileage vs expected.
    Average: 12,000 miles/year.
    """
    if not mileage or age <= 0:
        return 1.0
    expected = age * 12000
    diff = mileage - expected

    if diff > 30000:     return 0.85   # Way over → 15% penalty
    elif diff > 15000:   return 0.92   # Over → 8% penalty
    elif diff < -20000:  return 1.08   # Way under → 8% bonus
    elif diff < -10000:  return 1.04   # Under → 4% bonus
    return 1.0  # Within normal range


CONDITION_MULTIPLIERS = {
    "excellent": 1.05,   # 5% premium
    "good": 1.00,        # baseline
    "fair": 0.90,        # 10% discount
    "poor": 0.75,        # 25% discount
}
```

#### Step 4: Main Estimation Function

```python
def estimate_price(make, model, year, mileage=None, condition="good", body_class=None):
    """
    Estimate fair market value for a vehicle.
    Returns: {low_price, market_price, high_price, confidence, notes}
    """
    from datetime import datetime
    current_year = datetime.now().year
    age = current_year - year

    # 1. Find MSRP
    msrp, source = _find_msrp(make, model, year)
    if msrp is None:
        msrp = _estimate_msrp_by_category(body_class)
        source = "category_estimate"

    # 2. Apply depreciation
    dep_factor = _get_depreciation_factor(age)
    base_price = msrp * dep_factor

    # 3. Mileage adjustment
    mile_adj = _mileage_adjustment(mileage, age) if mileage else 1.0
    adjusted = base_price * mile_adj

    # 4. Condition adjustment
    cond_mult = CONDITION_MULTIPLIERS.get(condition.lower(), 1.0)
    market_price = adjusted * cond_mult

    # 5. Price range (±10-15%)
    low_price = market_price * 0.88
    high_price = market_price * 1.12

    # 6. Confidence score
    confidence = 0.85 if source == "msrp_database" else 0.55

    return {
        "make": make, "model": model, "year": year,
        "low_price": round(low_price, 2),
        "market_price": round(market_price, 2),
        "high_price": round(high_price, 2),
        "confidence": confidence,
        "source": source,
    }
```

#### Contract-to-Market Comparison

This function compares the finance amount in a contract to the estimated market value:

```python
def compare_contract_to_market(sla: dict, make=None, model=None, year=None):
    """Compare contract's finance amount to estimated market value."""
    finance = sla.get("finance_amount")
    if not finance:
        return {"comparison_available": False, "message": "No finance amount in contract"}

    estimate = estimate_price(make, model, year)
    market = estimate["market_price"]
    diff = float(finance) - market
    diff_pct = (diff / market) * 100

    assessment = "fair_deal" if abs(diff_pct) <= 10 else ("overpriced" if diff_pct > 0 else "good_deal")

    return {
        "comparison_available": True,
        "finance_amount": float(finance),
        "market_price": market,
        "difference": round(diff, 2),
        "diff_percent": round(diff_pct, 1),
        "assessment": assessment,
    }
```

---

## 6.4 Verification

```bash
python -c "
from backend.price_service import estimate_price

# Test known vehicle
result = estimate_price('Toyota', 'Camry', 2023, mileage=30000, condition='good')
print(f'2023 Toyota Camry:')
print(f'  Low:    \${result[\"low_price\"]:,.2f}')
print(f'  Market: \${result[\"market_price\"]:,.2f}')
print(f'  High:   \${result[\"high_price\"]:,.2f}')
print(f'  Confidence: {result[\"confidence\"]:.0%}')
"
```

---

[← Previous: LLM & Fairness](05-llm-fairness.md) | [Back to Contents](../DOCUMENTATION.md) | [Next: Negotiation Chatbot →](07-negotiation-chatbot.md)
