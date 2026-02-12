"""
Price Estimation Engine — Fair Market Value for Vehicles

Approach:
  1. Built-in MSRP reference database for popular makes/models/years
  2. Standard depreciation curve adjusted for mileage and condition
  3. VIN-based lookup: decodes VIN → matches MSRP → applies depreciation
  4. Returns a price range: low / market / high with confidence score

The engine uses publicly available pricing patterns:
  - Year 1: ~20% depreciation from MSRP
  - Year 2: ~15% additional
  - Year 3-5: ~10% per year
  - Year 6+: ~5-7% per year
  - Adjusted for mileage (avg 12,000 mi/year baseline)
  - Adjusted for condition (excellent/good/fair/poor)
"""

import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# ──────────────────── Reference MSRP Database ──────────────────── #

# Base MSRP values (USD) for popular models — used when exact data unavailable.
# Source: publicly available manufacturer suggested retail prices.
# Format: { "MAKE": { "MODEL": { year: msrp } } }

MSRP_DATABASE = {
    "TOYOTA": {
        "Camry":      {2024: 28855, 2023: 27415, 2022: 26420, 2021: 25965, 2020: 25250,
                       2019: 25250, 2018: 24380, 2017: 24380, 2016: 23905, 2015: 23795,
                       2014: 23235, 2013: 23070, 2012: 22975, 2011: 22745, 2010: 21800},
        "Corolla":    {2024: 22995, 2023: 22195, 2022: 21145, 2021: 20425, 2020: 20430,
                       2019: 19990, 2018: 19510, 2017: 19365, 2016: 18335, 2015: 17560,
                       2014: 17610, 2013: 17230, 2012: 17230, 2011: 16230, 2010: 16230},
        "RAV4":       {2024: 30535, 2023: 29790, 2022: 28275, 2021: 27740, 2020: 27740,
                       2019: 26545, 2018: 26150, 2017: 25350, 2016: 25250, 2015: 25035,
                       2014: 24410, 2013: 24530, 2012: 23460, 2011: 23260, 2010: 22715},
        "Highlander": {2024: 39520, 2023: 38620, 2022: 36620, 2021: 36620, 2020: 35720,
                       2019: 35540, 2018: 32248, 2017: 31930, 2016: 31590, 2015: 30690},
        "Tacoma":     {2024: 31500, 2023: 29515, 2022: 28410, 2021: 27595, 2020: 27395,
                       2019: 26950, 2018: 26150, 2017: 25300, 2016: 24300, 2015: 23975},
    },
    "HONDA": {
        "Civic":      {2024: 24950, 2023: 24650, 2022: 23645, 2021: 22695, 2020: 21650,
                       2019: 21250, 2018: 20650, 2017: 20440, 2016: 19975, 2015: 19490,
                       2014: 19190, 2013: 19155, 2012: 18905, 2011: 18655, 2010: 16355},
        "Accord":     {2024: 29610, 2023: 28890, 2022: 27615, 2021: 26520, 2020: 25970,
                       2019: 24615, 2018: 24445, 2017: 23980, 2016: 23555, 2015: 23225,
                       2014: 22920, 2013: 22670, 2012: 22580, 2011: 22280, 2010: 22005},
        "CR-V":       {2024: 31450, 2023: 31110, 2022: 29615, 2021: 27950, 2020: 26795,
                       2019: 25895, 2018: 25350, 2017: 25245, 2016: 24845, 2015: 24595,
                       2014: 24150, 2013: 23875, 2012: 23595, 2011: 23195, 2010: 22320},
    },
    "FORD": {
        "F-150":      {2024: 36965, 2023: 35575, 2022: 32920, 2021: 30635, 2020: 29290,
                       2019: 29250, 2018: 28675, 2017: 28150, 2016: 27705, 2015: 27285,
                       2014: 25800, 2013: 25520, 2012: 24700, 2011: 23750, 2010: 22840},
        "Escape":     {2024: 30495, 2023: 29600, 2022: 28475, 2021: 27755, 2020: 26080,
                       2019: 25200, 2018: 24645, 2017: 24645, 2016: 24145, 2015: 24075},
        "Explorer":   {2024: 38710, 2023: 37645, 2022: 35745, 2021: 33745, 2020: 33860,
                       2019: 33860, 2018: 32565, 2017: 32575, 2016: 32315, 2015: 31595},
        "Mustang":    {2024: 32515, 2023: 30920, 2022: 28545, 2021: 27770, 2020: 27155,
                       2019: 26670, 2018: 26185, 2017: 26185, 2016: 25185, 2015: 24425},
    },
    "CHEVROLET": {
        "Silverado":  {2024: 37645, 2023: 36300, 2022: 33500, 2021: 30195, 2020: 29795,
                       2019: 29795, 2018: 29285, 2017: 28985, 2016: 28100, 2015: 27575},
        "Equinox":    {2024: 30495, 2023: 28600, 2022: 28100, 2021: 27400, 2020: 25800,
                       2019: 25200, 2018: 24575, 2017: 24575, 2016: 23400, 2015: 23100},
        "Malibu":     {2024: 26200, 2023: 25100, 2022: 24100, 2021: 23900, 2020: 22590,
                       2019: 22555, 2018: 22555, 2017: 22555, 2016: 22500, 2015: 22465},
    },
    "HYUNDAI": {
        "Elantra":    {2024: 22865, 2023: 22065, 2022: 20665, 2021: 20665, 2020: 20245,
                       2019: 18185, 2018: 17785, 2017: 17785, 2016: 17785, 2015: 18060},
        "Tucson":     {2024: 30550, 2023: 29550, 2022: 27750, 2021: 25350, 2020: 24450,
                       2019: 24300, 2018: 23700, 2017: 23600, 2016: 23595, 2015: 23495},
        "Sonata":     {2024: 28990, 2023: 28690, 2022: 24150, 2021: 24150, 2020: 23600,
                       2019: 23100, 2018: 22935, 2017: 22935, 2016: 22635, 2015: 22100},
    },
    "NISSAN": {
        "Altima":     {2024: 28340, 2023: 27510, 2022: 25290, 2021: 25290, 2020: 24650,
                       2019: 24650, 2018: 24150, 2017: 24025, 2016: 23775, 2015: 23365},
        "Rogue":      {2024: 30630, 2023: 29850, 2022: 28390, 2021: 27530, 2020: 27110,
                       2019: 26260, 2018: 25820, 2017: 25550, 2016: 24960, 2015: 24220},
        "Sentra":     {2024: 21740, 2023: 20810, 2022: 20050, 2021: 19990, 2020: 19310,
                       2019: 19090, 2018: 17790, 2017: 17790, 2016: 17600, 2015: 17260},
    },
    "BMW": {
        "3 Series":   {2024: 44450, 2023: 43800, 2022: 42800, 2021: 41950, 2020: 41250,
                       2019: 40250, 2018: 34950, 2017: 34750, 2016: 34350, 2015: 33950},
        "5 Series":   {2024: 57400, 2023: 56000, 2022: 55400, 2021: 54200, 2020: 53400,
                       2019: 53400, 2018: 52650, 2017: 52195, 2016: 51400, 2015: 51200},
        "X3":         {2024: 47500, 2023: 46200, 2022: 44950, 2021: 43700, 2020: 42950,
                       2019: 42650, 2018: 42650, 2017: 39950, 2016: 39950, 2015: 39950},
    },
    "MERCEDES-BENZ": {
        "C-Class":    {2024: 46250, 2023: 45250, 2022: 44600, 2021: 43250, 2020: 42500,
                       2019: 41400, 2018: 41400, 2017: 40250, 2016: 39500, 2015: 39400},
        "E-Class":    {2024: 58050, 2023: 56750, 2022: 55300, 2021: 54250, 2020: 54050,
                       2019: 53500, 2018: 53500, 2017: 53075, 2016: 52650, 2015: 52325},
    },
    "TESLA": {
        "Model 3":    {2024: 38990, 2023: 40240, 2022: 46990, 2021: 39990, 2020: 37990,
                       2019: 38990, 2018: 35000},
        "Model Y":    {2024: 44990, 2023: 47490, 2022: 62990, 2021: 53990, 2020: 49990},
    },
}

# Category-based MSRP fallback if exact model not found
CATEGORY_MSRP = {
    "sedan":      28000,
    "suv":        35000,
    "truck":      38000,
    "coupe":      32000,
    "hatchback":  24000,
    "van":        35000,
    "convertible": 38000,
    "wagon":      30000,
    "default":    30000,
}


# ──────────────────── Depreciation Engine ──────────────────── #

def _get_depreciation_factor(vehicle_age: int) -> float:
    """
    Calculate cumulative depreciation factor based on vehicle age.
    Returns the fraction of MSRP the vehicle is worth.
    """
    if vehicle_age <= 0:
        return 1.0

    # Year-by-year depreciation rates
    annual_rates = [
        0.20,  # Year 1: 20% drop
        0.15,  # Year 2: 15% drop
        0.10,  # Year 3
        0.10,  # Year 4
        0.10,  # Year 5
        0.07,  # Year 6
        0.07,  # Year 7
        0.05,  # Year 8
        0.05,  # Year 9
        0.05,  # Year 10
    ]

    remaining = 1.0
    for i in range(min(vehicle_age, len(annual_rates))):
        remaining *= (1.0 - annual_rates[i])

    # Beyond 10 years: 3% per year
    if vehicle_age > len(annual_rates):
        extra_years = vehicle_age - len(annual_rates)
        remaining *= (1.0 - 0.03) ** extra_years

    # Floor at 5% of original value
    return max(remaining, 0.05)


def _mileage_adjustment(mileage: int, vehicle_age: int) -> float:
    """
    Adjust price based on mileage vs expected average.
    Average: 12,000 miles/year.
    Returns a multiplier (>1 for low mileage, <1 for high).
    """
    if vehicle_age <= 0:
        vehicle_age = 1

    expected_mileage = vehicle_age * 12000
    mileage_diff = mileage - expected_mileage

    # Each 10,000 miles above/below average adjusts ~3%
    adjustment = -(mileage_diff / 10000) * 0.03

    # Cap adjustment at ±15%
    return 1.0 + max(-0.15, min(0.15, adjustment))


def _condition_multiplier(condition: str) -> float:
    """Adjust price based on vehicle condition."""
    multipliers = {
        "excellent": 1.10,
        "good":      1.00,
        "fair":      0.88,
        "poor":      0.72,
    }
    return multipliers.get(condition.lower(), 1.00)


# ──────────────────── MSRP Lookup ──────────────────── #

def _find_msrp(make: str, model: str, year: int) -> tuple[Optional[float], str]:
    """
    Look up MSRP from the reference database.
    Returns (msrp, source).
    """
    make_upper = make.upper().strip() if make else ""
    model_title = model.strip().title() if model else ""

    # Exact match
    make_data = MSRP_DATABASE.get(make_upper, {})
    model_data = make_data.get(model_title, {})

    if year in model_data:
        return model_data[year], "msrp_database"

    # Try closest year for the same model
    if model_data:
        closest_year = min(model_data.keys(), key=lambda y: abs(y - year))
        year_diff = abs(closest_year - year)
        base_msrp = model_data[closest_year]
        # Adjust ~2% per year difference for inflation
        adjusted = base_msrp * (1.02 ** (year - closest_year))
        return adjusted, f"msrp_database_extrapolated_from_{closest_year}"

    # Fuzzy model match (partial name)
    for db_model, data in make_data.items():
        if db_model.lower() in model.lower() or model.lower() in db_model.lower():
            if year in data:
                return data[year], f"msrp_database_fuzzy_{db_model}"
            closest_year = min(data.keys(), key=lambda y: abs(y - year))
            adjusted = data[closest_year] * (1.02 ** (year - closest_year))
            return adjusted, f"msrp_database_fuzzy_{db_model}_extrapolated"

    # Category-based fallback
    return None, "not_found"


def _estimate_msrp_by_category(body_class: str = None) -> float:
    """Fallback MSRP estimation based on body class."""
    if not body_class:
        return CATEGORY_MSRP["default"]

    body_lower = body_class.lower()
    for category, msrp in CATEGORY_MSRP.items():
        if category in body_lower:
            return msrp
    return CATEGORY_MSRP["default"]


# ──────────────────── Main Estimation Function ──────────────────── #

def estimate_price(
    make: str,
    model: str,
    year: int,
    mileage: Optional[int] = None,
    condition: str = "good",
    body_class: Optional[str] = None,
) -> dict:
    """
    Estimate the fair market value of a vehicle.

    Returns dict with:
      - low_price, market_price, high_price
      - confidence score (0-1)
      - notes / source
    """
    current_year = datetime.now().year
    vehicle_age = current_year - year

    if vehicle_age < 0:
        vehicle_age = 0

    notes = []

    # 1. Find base MSRP
    msrp, source = _find_msrp(make, model, year)
    confidence = 0.0

    if msrp:
        if "extrapolated" in source:
            confidence = 0.65
            notes.append(f"MSRP extrapolated from reference data ({source})")
        elif "fuzzy" in source:
            confidence = 0.55
            notes.append(f"MSRP from partial model match ({source})")
        else:
            confidence = 0.80
            notes.append(f"MSRP from reference database: ${msrp:,.0f}")
    else:
        msrp = _estimate_msrp_by_category(body_class)
        confidence = 0.35
        notes.append(f"MSRP estimated from vehicle category: ${msrp:,.0f}")
        source = "category_estimate"

    # 2. Apply depreciation
    dep_factor = _get_depreciation_factor(vehicle_age)
    base_value = msrp * dep_factor
    notes.append(f"Depreciation factor: {dep_factor:.2f} (age: {vehicle_age} years)")

    # 3. Mileage adjustment
    if mileage and mileage > 0:
        mile_adj = _mileage_adjustment(mileage, vehicle_age)
        base_value *= mile_adj
        expected = vehicle_age * 12000
        if mileage > expected:
            notes.append(f"Mileage above average ({mileage:,} vs {expected:,} expected)")
        else:
            notes.append(f"Mileage below average ({mileage:,} vs {expected:,} expected)")
    else:
        mile_adj = 1.0
        notes.append("No mileage provided — using average estimate")

    # 4. Condition adjustment
    cond_mult = _condition_multiplier(condition)
    base_value *= cond_mult
    if condition.lower() != "good":
        notes.append(f"Condition adjustment: {condition} ({cond_mult:.2f}x)")

    # 5. Calculate price range
    market_price = round(base_value, -2)  # round to nearest $100
    low_price = round(market_price * 0.88, -2)    # ~12% below
    high_price = round(market_price * 1.12, -2)   # ~12% above

    # Floor at $500
    market_price = max(market_price, 500)
    low_price = max(low_price, 300)
    high_price = max(high_price, 700)

    logger.info("Price estimate for %s %s %s: $%s (range: $%s–$%s, conf: %.2f)",
                year, make, model, f"{market_price:,.0f}",
                f"{low_price:,.0f}", f"{high_price:,.0f}", confidence)

    return {
        "make": make,
        "model": model,
        "year": year,
        "mileage": mileage,
        "condition": condition,
        "low_price": low_price,
        "market_price": market_price,
        "high_price": high_price,
        "msrp": round(msrp, 0),
        "confidence": round(confidence, 2),
        "source": source,
        "notes": notes,
    }


def estimate_price_from_vin(vin: str) -> dict:
    """
    Decode a VIN, then estimate the price.
    Convenience function combining VIN decode + price estimation.
    """
    from backend.vin_service import decode_vin

    vehicle = decode_vin(vin)

    make = vehicle.get("make")
    model = vehicle.get("model")
    year_str = vehicle.get("year")
    body_class = vehicle.get("body_class")

    if not (make and model and year_str):
        return {"error": "Could not determine make/model/year from VIN"}

    try:
        year = int(year_str)
    except (ValueError, TypeError):
        return {"error": f"Invalid year from VIN decode: {year_str}"}

    result = estimate_price(
        make=make,
        model=model,
        year=year,
        body_class=body_class,
    )
    result["vin"] = vin
    result["vehicle_id"] = vehicle.get("vehicle_id")

    return result


# ──────────────────── Contract Price Comparison ──────────────────── #

def compare_contract_to_market(sla: dict, make: str = None, model: str = None,
                                year: int = None) -> dict:
    """
    Compare a contract's finance amount against fair market value.
    Returns pricing analysis for fairness scoring integration.
    """
    finance_amount = sla.get("finance_amount")

    if not finance_amount or not (make and model and year):
        return {
            "comparison_available": False,
            "reason": "Insufficient data for price comparison",
        }

    try:
        finance_amount = float(finance_amount)
    except (ValueError, TypeError):
        return {
            "comparison_available": False,
            "reason": "Invalid finance amount",
        }

    estimate = estimate_price(make=make, model=model, year=year)
    market_price = estimate["market_price"]
    high_price = estimate["high_price"]

    deviation_pct = ((finance_amount - market_price) / market_price) * 100

    result = {
        "comparison_available": True,
        "finance_amount": finance_amount,
        "market_price": market_price,
        "price_range": f"${estimate['low_price']:,.0f} – ${high_price:,.0f}",
        "deviation_percent": round(deviation_pct, 1),
        "confidence": estimate["confidence"],
    }

    if deviation_pct > 15:
        result["assessment"] = "overpriced"
        result["message"] = f"Contract price is {deviation_pct:.0f}% above market value"
    elif deviation_pct > 5:
        result["assessment"] = "slightly_above_market"
        result["message"] = f"Contract price is {deviation_pct:.0f}% above market"
    elif deviation_pct < -10:
        result["assessment"] = "good_deal"
        result["message"] = f"Contract price is {abs(deviation_pct):.0f}% below market"
    else:
        result["assessment"] = "fair"
        result["message"] = "Contract price is within fair market range"

    return result
