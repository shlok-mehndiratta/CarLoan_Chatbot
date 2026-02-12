"""
FastAPI backend — Car Lease / Loan Contract Review & Negotiation API

Endpoints:
  GET  /              — health banner
  GET  /health        — health check
  POST /analyze       — upload PDF → SLA extraction (rule + LLM) + fairness
  GET  /vin/{vin}     — decode VIN via NHTSA
  GET  /contract/{id} — retrieve saved analysis
"""

import logging
import traceback

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from backend.db import (
    init_db, save_contract, save_sla, save_extracted_clauses,
    get_contract, get_sla_for_contract,
)
from backend.pdf_reader import extract_text_from_pdf
from backend.contract_analyzer import analyze_contract, merge_rule_and_llm
from backend.llm_sla_extracter import extract_sla_with_llm
from backend.vin_service import get_vehicle_details
from backend.fairness_engine import calculate_fairness_score
from backend.negotiation_assistant import generate_negotiation_points

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ──────────────────── App setup ──────────────────── #

app = FastAPI(
    title="Car Lease / Loan Contract Review API",
    version="2.0",
    description="AI-powered contract analysis and negotiation assistant",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DB on startup
@app.on_event("startup")
def startup():
    init_db()
    logger.info("Database initialized")


# ──────────────────── Basic endpoints ──────────────────── #

@app.get("/")
def home():
    return {"message": "Car Loan / Lease AI API is running", "version": "2.0"}


@app.get("/health")
def health():
    return {"status": "ok"}


# ──────────────────── Contract Analysis ──────────────────── #

@app.post("/analyze")
async def analyze_contract_api(file: UploadFile = File(...)):
    """
    Upload a car lease / loan contract PDF and receive:
    - Structured SLA extraction (rule-based + LLM merged)
    - AI-assisted interpretation
    - Fairness score
    - Negotiation points
    """

    try:
        # 1️⃣  Validate file type
        if file.content_type != "application/pdf":
            return {"error": "Only PDF files are supported"}

        pdf_bytes = await file.read()

        # 2️⃣  Validate file size (10 MB limit)
        if len(pdf_bytes) > 10 * 1024 * 1024:
            return {"error": "File too large (maximum 10MB allowed)"}

        # 3️⃣  Extract text (digital PDF → OCR fallback)
        contract_text = extract_text_from_pdf(pdf_bytes)

        if not contract_text or not contract_text.strip():
            return {"error": "No readable text could be extracted from the PDF"}

        logger.info("Extracted %d chars from '%s'", len(contract_text), file.filename)

        # 4️⃣  Save raw contract text
        contract_id = save_contract(file.filename, contract_text)

        # 5️⃣  Rule-based SLA extraction
        rule_sla = analyze_contract(contract_text)

        # 6️⃣  LLM-based SLA extraction (graceful fallback)
        extraction_method = "rule_based"
        try:
            llm_sla = extract_sla_with_llm(contract_text)
            # Merge: rule-based values take priority, LLM fills gaps
            final_sla = merge_rule_and_llm(rule_sla, llm_sla)
            extraction_method = "merged"
            logger.info("LLM extraction succeeded — using merged results")
        except (ConnectionError, ValueError, Exception) as e:
            logger.warning("LLM extraction failed (%s) — using rule-based only", e)
            final_sla = rule_sla

        # 7️⃣  Calculate fairness score
        fairness = calculate_fairness_score(final_sla)

        # 8️⃣  Generate negotiation points
        negotiation = generate_negotiation_points(final_sla, fairness)

        # 9️⃣  Store results
        save_sla(contract_id, {
            "sla": final_sla,
            "fairness": fairness,
            "negotiation_points": negotiation,
        }, extraction_method=extraction_method)

        save_extracted_clauses(contract_id, final_sla, source=extraction_method)

        # 🔟  API response
        return {
            "contract_id": contract_id,
            "sla": final_sla,
            "fairness": fairness,
            "negotiation_points": negotiation,
            "extraction_method": extraction_method,
        }

    except Exception:
        traceback.print_exc()
        return {"error": "Internal server error during contract analysis"}


# ──────────────────── Contract Retrieval ──────────────────── #

@app.get("/contract/{contract_id}")
def get_contract_analysis(contract_id: int):
    """Retrieve a previously analyzed contract."""
    contract = get_contract(contract_id)
    if not contract:
        return {"error": "Contract not found"}

    sla_record = get_sla_for_contract(contract_id)
    return {
        "contract_id": contract_id,
        "file_name": contract["file_name"],
        "created_at": contract["created_at"],
        "analysis": sla_record["sla_json"] if sla_record else None,
    }


# ──────────────────── VIN Lookup ──────────────────── #

@app.get("/vin/{vin}")
def vin_lookup(vin: str):
    """Decode VIN and fetch basic vehicle information using public NHTSA API."""
    try:
        return get_vehicle_details(vin)
    except Exception:
        traceback.print_exc()
        return {"error": "VIN lookup failed"}