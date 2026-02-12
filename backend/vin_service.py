"""
VIN Service — Vehicle Information via NHTSA public APIs.

Endpoints covered:
  1. VIN Decode      → vehicle make, model, year, trim, engine, etc.
  2. Recalls         → NHTSA recall campaigns for the vehicle
  3. Complaints      → consumer complaints filed with NHTSA

All data is persisted to the database for reuse.
"""

import logging
import requests

from backend.db import save_vehicle, save_vehicle_recalls

logger = logging.getLogger(__name__)

# ──────────────────── NHTSA API URLs ──────────────────── #

NHTSA_DECODE_URL = "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVin/{vin}?format=json"
NHTSA_RECALLS_URL = "https://api.nhtsa.gov/recalls/recallsByVehicle?make={make}&model={model}&modelYear={year}"
NHTSA_COMPLAINTS_URL = "https://api.nhtsa.gov/complaints/complaintsByVehicle?make={make}&model={model}&modelYear={year}"

REQUEST_TIMEOUT = 15


# ──────────────────── VIN Decode ──────────────────── #

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
    """
    Decode a VIN and return structured vehicle information.
    Saves to the database for future lookups.
    """
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
        "raw_nhtsa": raw,  # full raw data stored as JSON
    }

    # Additional fields from NHTSA (for display)
    vehicle["extra"] = {
        "manufacturer": raw.get("Manufacturer Name"),
        "plant_country": raw.get("Plant Country"),
        "vehicle_type": raw.get("Vehicle Type"),
        "doors": raw.get("Doors"),
        "gvwr": raw.get("Gross Vehicle Weight Rating From"),
        "displacement_l": raw.get("Displacement (L)"),
        "cylinders": raw.get("Engine Number of Cylinders"),
        "fuel_injection": raw.get("Fuel Type - Secondary"),
        "transmission": raw.get("Transmission Style"),
        "abs": raw.get("Anti-lock Braking System (ABS)"),
        "series": raw.get("Series"),
        "error_code": raw.get("Error Code"),
    }

    # Save to DB
    try:
        vehicle_id = save_vehicle(vehicle)
        vehicle["vehicle_id"] = vehicle_id
        logger.info("Vehicle saved to DB with id=%d for VIN=%s", vehicle_id, vin)
    except Exception as e:
        logger.warning("Failed to save vehicle to DB: %s", e)
        vehicle["vehicle_id"] = None

    return vehicle


# ──────────────────── Recalls ──────────────────── #

def get_recalls(make: str, model: str, year: str) -> list:
    """
    Fetch recall campaigns from NHTSA for a specific vehicle.
    Returns a list of recall dicts.
    """
    url = NHTSA_RECALLS_URL.format(make=make, model=model, year=year)

    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            logger.warning("NHTSA Recalls API returned %d", resp.status_code)
            return []

        data = resp.json()
        results = data.get("results", [])

        recalls = []
        for item in results:
            recalls.append({
                "nhtsa_campaign": item.get("NHTSACampaignNumber"),
                "component": item.get("Component"),
                "summary": item.get("Summary"),
                "consequence": item.get("Consequence"),
                "remedy": item.get("Remedy"),
                "report_date": item.get("ReportReceivedDate"),
                "manufacturer": item.get("Manufacturer"),
            })

        logger.info("Found %d recalls for %s %s %s", len(recalls), year, make, model)
        return recalls

    except Exception as e:
        logger.warning("Recalls API call failed: %s", e)
        return []


# ──────────────────── Complaints ──────────────────── #

def get_complaints(make: str, model: str, year: str) -> list:
    """
    Fetch consumer complaints from NHTSA for a specific vehicle.
    Returns a list of complaint summaries.
    """
    url = NHTSA_COMPLAINTS_URL.format(make=make, model=model, year=year)

    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            logger.warning("NHTSA Complaints API returned %d", resp.status_code)
            return []

        data = resp.json()
        results = data.get("results", [])

        complaints = []
        for item in results:
            complaints.append({
                "odi_number": item.get("odiNumber"),
                "component": item.get("components"),
                "summary": item.get("summary"),
                "crash": item.get("crash", False),
                "fire": item.get("fire", False),
                "injuries": item.get("numberOfInjuries", 0),
                "date_filed": item.get("dateComplaintFiled"),
            })

        logger.info("Found %d complaints for %s %s %s", len(complaints), year, make, model)
        return complaints

    except Exception as e:
        logger.warning("Complaints API call failed: %s", e)
        return []


# ──────────────────── Combined Lookup ──────────────────── #

def get_vehicle_details(vin: str) -> dict:
    """
    Full vehicle lookup: decode VIN + fetch recalls + fetch complaints.
    This is the main function called by the API endpoint.
    """
    # 1. Decode VIN
    vehicle = decode_vin(vin)

    make = vehicle.get("make")
    model = vehicle.get("model")
    year = vehicle.get("year")

    # 2. Fetch recalls (if we have make/model/year)
    recalls = []
    if make and model and year:
        recalls = get_recalls(make, model, year)

        # Save recalls to DB
        if recalls and vehicle.get("vehicle_id"):
            try:
                save_vehicle_recalls(vehicle["vehicle_id"], recalls)
            except Exception as e:
                logger.warning("Failed to save recalls to DB: %s", e)

    # 3. Fetch complaints
    complaints = []
    if make and model and year:
        complaints = get_complaints(make, model, year)

    # 4. Build response
    return {
        "vehicle": {
            "vin": vin,
            "make": make,
            "model": model,
            "year": year,
            "trim": vehicle.get("trim"),
            "body_class": vehicle.get("body_class"),
            "engine": vehicle.get("engine"),
            "fuel_type": vehicle.get("fuel_type"),
            "drive_type": vehicle.get("drive_type"),
            "plant_info": vehicle.get("plant_info"),
            "manufacturer": vehicle.get("extra", {}).get("manufacturer"),
            "vehicle_type": vehicle.get("extra", {}).get("vehicle_type"),
            "doors": vehicle.get("extra", {}).get("doors"),
            "cylinders": vehicle.get("extra", {}).get("cylinders"),
            "transmission": vehicle.get("extra", {}).get("transmission"),
        },
        "recalls": recalls,
        "recalls_count": len(recalls),
        "complaints": complaints[:10],  # limit to 10 most recent for response size
        "complaints_count": len(complaints),
        "vehicle_id": vehicle.get("vehicle_id"),
    }


def get_recalls_for_vin(vin: str) -> dict:
    """
    Dedicated recalls endpoint — decode VIN then fetch only recalls.
    """
    vehicle = decode_vin(vin)

    make = vehicle.get("make")
    model = vehicle.get("model")
    year = vehicle.get("year")

    if not (make and model and year):
        return {"error": "Could not determine make/model/year from VIN", "recalls": []}

    recalls = get_recalls(make, model, year)

    return {
        "vin": vin,
        "vehicle": f"{year} {make} {model}",
        "recalls": recalls,
        "recalls_count": len(recalls),
    }