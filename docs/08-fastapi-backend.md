# Chapter 8: FastAPI Backend

[← Previous: Negotiation Chatbot](07-negotiation-chatbot.md) | [Back to Contents](../DOCUMENTATION.md) | [Next: Flutter App →](09-flutter-app.md)

---

## 8.1 What Is FastAPI?

FastAPI is a modern Python web framework for building RESTful APIs. Key advantages:

| Feature | Benefit |
|---------|---------|
| **Automatic docs** | Interactive Swagger UI at `/docs` — test endpoints in browser |
| **Type validation** | Pydantic models auto-validate request/response data |
| **Async support** | Can handle file uploads and concurrent requests efficiently |
| **Performance** | One of the fastest Python frameworks (comparable to Node.js) |

When you run the server and visit `http://localhost:8000/docs`, you get a fully interactive API documentation page where you can test every endpoint.

---

## 8.2 Application Setup

### File: `backend/main.py`

```python
"""
FastAPI backend — Car Lease / Loan Contract Review & Negotiation API
"""

import json, logging, traceback
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

# Import all service modules
from backend.db import (
    init_db, save_contract, save_sla, save_extracted_clauses,
    get_contract, get_sla_for_contract, save_price_recommendation,
    create_negotiation_thread, save_negotiation_message, get_negotiation_history,
)
from backend.pdf_reader import extract_text_from_pdf
from backend.contract_analyzer import analyze_contract, merge_rule_and_llm
from backend.llm_sla_extracter import extract_sla_with_llm
from backend.vin_service import get_vehicle_details, get_recalls_for_vin
from backend.fairness_engine import calculate_fairness_score
from backend.negotiation_assistant import (
    generate_negotiation_points, chat_with_negotiator, generate_negotiation_email,
)
from backend.price_service import estimate_price, estimate_price_from_vin, compare_contract_to_market

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ──────────────── App Setup ──────────────── #

app = FastAPI(
    title="Car Lease / Loan Contract Review API",
    version="4.0",
    description="AI-powered contract analysis, VIN intelligence, pricing, and negotiation",
)

# CORS middleware — allows the Flutter app to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # Allow all origins (for development)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()
    logger.info("Database initialized")
```

**What is CORS?** Cross-Origin Resource Sharing. Without it, a Flutter app running on `localhost:3000` cannot call an API on `localhost:8000` — browsers block cross-origin requests by default. The CORS middleware allows all origins for development.

---

## 8.3 The 12 API Endpoints

### Endpoint 1-2: Health Checks

```python
@app.get("/")
def home():
    return {"message": "Car Loan / Lease AI API is running", "version": "4.0"}

@app.get("/health")
def health():
    return {"status": "ok"}
```

### Endpoint 3: Contract Analysis (the Core Pipeline)

This is the most complex endpoint — it orchestrates the entire analysis flow:

```python
@app.post("/analyze")
async def analyze_contract_api(file: UploadFile = File(...)):
    """Upload a PDF → get full analysis."""
    try:
        # 1. Validate file type
        if file.content_type != "application/pdf":
            return {"error": "Only PDF files are supported"}

        pdf_bytes = await file.read()

        # 2. Validate file size (10 MB limit)
        if len(pdf_bytes) > 10 * 1024 * 1024:
            return {"error": "File too large (maximum 10MB)"}

        # 3. Extract text (digital PDF → OCR fallback)
        contract_text = extract_text_from_pdf(pdf_bytes)
        if not contract_text or not contract_text.strip():
            return {"error": "No text could be extracted from the PDF"}

        # 4. Save raw contract to DB
        contract_id = save_contract(file.filename, contract_text)

        # 5. Rule-based SLA extraction
        rule_sla = analyze_contract(contract_text)

        # 6. LLM extraction (graceful fallback)
        extraction_method = "rule_based"
        try:
            llm_sla = extract_sla_with_llm(contract_text)
            final_sla = merge_rule_and_llm(rule_sla, llm_sla)
            extraction_method = "merged"
        except (ConnectionError, ValueError, Exception):
            final_sla = rule_sla

        # 7. Price comparison (if vehicle info available)
        price_comparison = None
        make = final_sla.get("vehicle_make")
        model = final_sla.get("vehicle_model")
        year = final_sla.get("vehicle_year")
        if make and model and year:
            try:
                price_comparison = compare_contract_to_market(
                    final_sla, make=make, model=model, year=int(year)
                )
            except Exception:
                pass

        # 8. Calculate fairness score
        fairness = calculate_fairness_score(final_sla, price_comparison=price_comparison)

        # 9. Generate negotiation points
        negotiation = generate_negotiation_points(final_sla, fairness)

        # 10. Store everything in DB
        save_sla(contract_id, {
            "sla": final_sla, "fairness": fairness,
            "negotiation_points": negotiation, "price_comparison": price_comparison,
        }, extraction_method=extraction_method)

        return {
            "contract_id": contract_id,
            "sla": final_sla,
            "fairness": fairness,
            "negotiation_points": negotiation,
            "extraction_method": extraction_method,
        }
    except Exception:
        traceback.print_exc()
        return {"error": "Internal server error during analysis"}
```

### Endpoints 4-6: Contract Retrieval & VIN

```python
@app.get("/contract/{contract_id}")
def get_contract_analysis(contract_id: int):
    """Retrieve a previously analyzed contract."""
    contract = get_contract(contract_id)
    if not contract:
        return {"error": "Contract not found"}
    sla_record = get_sla_for_contract(contract_id)
    return {"contract_id": contract_id, "analysis": sla_record["sla_json"] if sla_record else None}

@app.get("/vin/{vin}")
def vin_lookup(vin: str):
    """Full VIN lookup with recalls and complaints."""
    if len(vin) != 17:
        return {"error": "VIN must be exactly 17 characters"}
    return get_vehicle_details(vin)

@app.get("/vin/{vin}/recalls")
def vin_recalls(vin: str):
    """Dedicated VIN-based recall lookup."""
    if len(vin) != 17:
        return {"error": "VIN must be exactly 17 characters"}
    return get_recalls_for_vin(vin)
```

### Endpoints 7-8: Price Estimation

```python
class PriceEstimateRequest(BaseModel):
    make: str
    model: str
    year: int
    mileage: Optional[int] = None
    condition: str = "good"

@app.post("/price-estimate")
def price_estimate_api(req: PriceEstimateRequest):
    """Estimate vehicle fair market value."""
    result = estimate_price(make=req.make, model=req.model, year=req.year,
                            mileage=req.mileage, condition=req.condition)
    save_price_recommendation(result=result)
    return result

@app.get("/price-estimate/{vin}")
def price_estimate_by_vin(vin: str):
    """Estimate price by decoding a VIN first."""
    if len(vin) != 17:
        return {"error": "VIN must be exactly 17 characters"}
    return estimate_price_from_vin(vin)
```

### Endpoints 9-12: Negotiation

```python
@app.post("/negotiate/start")
def negotiate_start(req: NegotiationStartRequest):
    """Start a negotiation session for a contract."""
    contract = get_contract(req.contract_id)
    if not contract:
        return {"error": "Contract not found"}

    # Load contract analysis
    sla_record = get_sla_for_contract(req.contract_id)
    analysis = sla_record.get("sla_json")

    # Create thread with context
    context = {"sla": analysis.get("sla", {}), "fairness": analysis.get("fairness", {})}
    thread_id = create_negotiation_thread(
        contract_id=req.contract_id, context_json=json.dumps(context)
    )

    points = generate_negotiation_points(context["sla"], context["fairness"])
    welcome = f"Welcome! I've analyzed your contract (score: {context['fairness'].get('fairness_score')}/100)."
    save_negotiation_message(thread_id, "assistant", welcome)

    return {"thread_id": thread_id, "welcome_message": welcome, "negotiation_points": points}

@app.post("/negotiate/chat")
def negotiate_chat(req: NegotiationChatRequest):
    """Send a message in the negotiation chat."""
    save_negotiation_message(req.thread_id, "user", req.message)
    # Load thread context and history, get AI response
    response = chat_with_negotiator(user_message=req.message, context=context, chat_history=history)
    save_negotiation_message(req.thread_id, "assistant", response)
    return {"thread_id": req.thread_id, "response": response}

@app.get("/negotiate/history/{thread_id}")
def negotiate_history(thread_id: int):
    """Get full chat history for a thread."""
    return {"messages": get_negotiation_history(thread_id)}

@app.post("/negotiate/email")
def negotiate_email(req: NegotiationEmailRequest):
    """Generate a professional negotiation email."""
    context = load_context_for_contract(req.contract_id)
    email = generate_negotiation_email(context, req.specific_requests, req.tone)
    return {"email": email}
```

---

## 8.4 Running the Server

```bash
# Activate virtual environment
source venv/bin/activate

# Start the development server
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# --reload: auto-restarts when code changes (dev only)
# --host 0.0.0.0: accessible from other devices on network
# --port 8000: the port to listen on
```

Visit `http://localhost:8000/docs` to see the interactive Swagger documentation.

### Testing with curl

```bash
# Health check
curl http://localhost:8000/health

# Price estimate
curl -X POST http://localhost:8000/price-estimate \
  -H "Content-Type: application/json" \
  -d '{"make": "Toyota", "model": "Camry", "year": 2023}'

# Upload a contract
curl -X POST http://localhost:8000/analyze \
  -F "file=@contract.pdf"
```

---

[← Previous: Negotiation Chatbot](07-negotiation-chatbot.md) | [Back to Contents](../DOCUMENTATION.md) | [Next: Flutter App →](09-flutter-app.md)
