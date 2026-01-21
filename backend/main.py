from fastapi import FastAPI, UploadFile, File
import traceback

from backend.db import save_contract, save_sla
from backend.pdf_reader import extract_text_from_pdf
from backend.contract_analyzer import analyze_contract
from backend.vin_service import get_vehicle_details
from backend.fairness_engine import calculate_fairness_score

app = FastAPI(
    title="Car Lease / Loan Contract Review API",
    version="1.0",
    description="AI-powered contract analysis and negotiation assistant"
)

# ---------------- BASIC ENDPOINTS ---------------- #

@app.get("/")
def home():
    return {"message": "Car Loan / Lease AI API is running"}


@app.get("/health")
def health():
    return {"status": "ok"}


# ---------------- CONTRACT ANALYSIS ---------------- #

@app.post("/analyze")
async def analyze_contract_api(file: UploadFile = File(...)):
    """
    Upload a car lease / loan contract PDF and receive:
    - Structured SLA extraction
    - AI-assisted interpretation
    """

    try:
        # 1️⃣ Validate file type
        if file.content_type != "application/pdf":
            return {"error": "Only PDF files are supported"}

        pdf_bytes = await file.read()

        # 2️⃣ Validate file size (10 MB limit)
        if len(pdf_bytes) > 10 * 1024 * 1024:
            return {"error": "File too large (maximum 10MB allowed)"}

        # 3️⃣ Extract text (digital PDF → OCR fallback)
        contract_text = extract_text_from_pdf(pdf_bytes)

        if not contract_text or not contract_text.strip():
            return {"error": "No readable text could be extracted from the PDF"}

        # 4️⃣ Save raw contract text
        contract_id = save_contract(file.filename, contract_text)
        # 5️⃣ Rule-based SLA extraction
        final_sla = analyze_contract(contract_text)

        # 6️⃣ Calculate fairness score
        fairness = calculate_fairness_score(final_sla)

        # 7️⃣ Store SLA + fairness together
        save_sla(contract_id, {
           "sla": final_sla,
        "fairness": fairness
        })

        # 8️⃣ API response
        return {
         "contract_id": contract_id,
         "sla": final_sla,
         "fairness": fairness
        }

    except Exception:
        traceback.print_exc()
        return {
            "error": "Internal server error during contract analysis"
        }


# ---------------- VIN LOOKUP ---------------- #

@app.get("/vin/{vin}")
def vin_lookup(vin: str):
    """
    Decode VIN and fetch basic vehicle information
    using public NHTSA API
    """
    try:
        return get_vehicle_details(vin)
    except Exception:
        traceback.print_exc()
        return {"error": "VIN lookup failed"}