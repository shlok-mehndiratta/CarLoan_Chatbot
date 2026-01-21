import requests

def get_vehicle_details(vin: str) -> dict:
    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVin/{vin}?format=json"
    resp = requests.get(url, timeout=10)

    if resp.status_code != 200:
        return {"error": "VIN lookup failed"}

    data = resp.json()["Results"]

    result = {}
    for item in data:
        if item["Value"]:
            result[item["Variable"]] = item["Value"]

    return {
        "make": result.get("Make"),
        "model": result.get("Model"),
        "year": result.get("Model Year"),
        "body_class": result.get("Body Class"),
        "engine": result.get("Engine Model"),
        "recalls_note": "Check NHTSA recalls separately"
    }