from fastapi import FastAPI, UploadFile
from backend.db import save_contract, save_sla
from backend.pdf_reader import extract_text_from_pdf
from backend.contract_analyzer import analyze_contract
import json
import traceback

app = FastAPI()

@app.get("/")
def home():
    return {"message": "API is running"}

@app.post("/analyze")
async def analyze_contract_api(file: UploadFile):
    try:
        print("🚀 API HIT")
        print("📄 File:", file.filename)

        pdf_bytes = await file.read()
        text = extract_text_from_pdf(pdf_bytes)

        print("📝 Text length:", len(text))

        if not text.strip():
            return {"error": "No readable text extracted from PDF"}

        contract_id = save_contract(file.filename, text)
        print("💾 Contract saved:", contract_id)

        sla = analyze_contract(text)
        print("🤖 SLA:", sla)

        save_sla(contract_id, json.dumps(sla))

        return {
            "contract_id": contract_id,
            "sla": sla
        }

    except Exception as e:
        print("❌ ERROR")
        traceback.print_exc()
        return {"error": str(e)}