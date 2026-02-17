# Chapter 1: Introduction & Problem Statement

[← Back to Table of Contents](../DOCUMENTATION.md) | [Next: Environment Setup →](02-environment-setup.md)

---

## 1.1 What Is This Project?

The **AI-Powered Car Lease & Loan Contract Review and Negotiation Assistant** is a software platform that helps everyday consumers understand, analyze, and negotiate car financing contracts using artificial intelligence.

When you lease or buy a car through financing, you sign a contract that is often **20–40 pages** of dense legal and financial language. Most people don't read these contracts carefully, and even if they do, they may not understand what they are agreeing to. This creates a situation called **information asymmetry** — the dealer knows much more about the terms than the customer.

### The Real-World Problem

Consider this scenario: You go to a car dealership, test drive a car, and agree to buy it. The finance manager shows you a contract with these terms:
- **APR: 18.9%** (but the average market rate is 6–8%)
- **Documentation fee: ₹15,000** (but the actual cost is ₹500)
- **Early termination penalty: 6 months of remaining payments** (extremely harsh)
- **Mileage overage: $0.35/mile** (typical is $0.15–0.20)

Most people would not catch all these red flags. **This project catches them automatically.**

### What This System Does

1. **You upload a PDF** of your car financing contract
2. **The AI reads the contract** and extracts every important financial term
3. **It scores the contract** for fairness (0–100) based on market standards
4. **It suggests negotiation strategies** — specific talking points and counter-offers
5. **You can chat with an AI advisor** who knows your contract inside-out
6. **It generates professional emails** to send to the dealer for renegotiation

---

## 1.2 Feature List

### Feature 1: Smart Contract Analysis (PDF → Structured Data)

**What it does:** Takes a PDF contract (digital or scanned) and extracts every important financial data point.

**How it works:** Two extraction systems run in parallel:
1. **Rule-based extraction** — Uses regular expressions (regex patterns) to find numbers, percentages, and key phrases in the text
2. **LLM extraction** — Sends the text to a Large Language Model (Ollama/Llama) which understands natural language and can find information even when it's phrased unusually

The results from both are **merged** — rule-based values take priority (they're more precise with numbers), and the LLM fills in any gaps.

**Data extracted includes:**

| Field | Example Value | Why It Matters |
|-------|---------------|----------------|
| APR (Interest Rate) | 8.5% | Determines how much extra you pay |
| Monthly Payment | ₹25,000 | Your monthly cost |
| Term | 60 months | How long you're locked in |
| Down Payment | ₹100,000 | Money paid upfront |
| Finance Amount | ₹1,200,000 | Total amount being financed |
| Mileage Allowance | 12,000/year | For leases — how far you can drive |
| Early Termination Fee | 4 months payment | Cost to exit early |
| Documentation Fee | ₹5,000 | A common negotiable fee |
| Red Flags | [ "APR above 15%", "High penalty" ] | Warning signs |

### Feature 2: Fairness Score (0–100)

The system evaluates the contract across **6 dimensions**:

| Dimension | Max Penalty | What It Checks |
|-----------|-------------|----------------|
| Interest Rate (APR) | -30 points | Is the APR above market rates? |
| Early Termination | -20 points | Are the penalties too harsh? |
| Fees | -15 points | Are documentation/processing fees inflated? |
| Red Flags | -15 points | Are there concerning terms in the contract? |
| Price vs Market | -20 / +5 points | Is the vehicle price fair vs actual market value? |
| Payment Burden | -10 points | Is the total interest too high relative to the price? |

**Rating scale:**
- **85–100:** Excellent — fair deal
- **70–84:** Good — minor issues
- **55–69:** Fair — negotiate before signing
- **40–54:** Below Average — significant concerns
- **0–39:** Poor — walk away or major renegotiation needed

### Feature 3: VIN-Based Vehicle Intelligence

A Vehicle Identification Number (VIN) is a unique 17-character code on every car. By entering a VIN, the system fetches:
- **Vehicle details** — make, model, year, engine, trim, body class
- **Recall history** — safety recalls issued by the manufacturer
- **Consumer complaints** — problems reported by other owners

This uses the **NHTSA (National Highway Traffic Safety Administration)** public API.

### Feature 4: Price Estimation Engine

Estimates the fair market value of a vehicle using:
- A built-in **MSRP database** (10+ manufacturers, 25+ models)
- **Depreciation curves** — cars lose value over time in a predictable pattern
- **Mileage adjustments** — high mileage reduces value
- **Condition multipliers** — excellent, good, fair, poor

Returns a **price range** (low / market / high) with a **confidence score**.

### Feature 5: AI Negotiation Chatbot

A conversational AI that:
- Knows your specific contract details
- Suggests specific talking points and counter-offers
- Maintains conversation history for multi-turn discussions
- Can generate professional negotiation emails

### Feature 6: Flutter Mobile App

A cross-platform mobile application with 4 main tabs:
- **Analyze** — Upload PDFs and view analysis results
- **VIN Lookup** — Decode a VIN and see recalls
- **Price Estimate** — Get fair vehicle pricing
- **Dashboard** — Summary view with quick actions

---

## 1.3 Technology Stack Explained

| Technology | What It Is | Why We Use It |
|------------|-----------|---------------|
| **Python 3.12** | Programming language | Industry standard for AI/ML, vast library ecosystem |
| **FastAPI** | Web framework | Modern, fast, automatic API documentation, async support |
| **Uvicorn** | ASGI server | Runs FastAPI in production with high performance |
| **Ollama** | Local LLM runner | Runs AI models on your machine — no cloud API costs |
| **LangChain** | LLM framework | Simplifies prompting and chaining LLM calls |
| **SQLite** | Database | Zero-config, file-based, perfect for single-server apps |
| **Pydantic** | Data validation | Type-safe request/response handling |
| **PyPDF2 / pdfminer** | PDF readers | Extract text from digital PDFs |
| **Tesseract OCR** | Image-to-text | Read scanned/photographed contracts |
| **Flutter** | Mobile framework | Single codebase for iOS + Android |
| **Docker** | Containerization | Consistent deployment across environments |

---

## 1.4 What You Will Build

By the end of this documentation, you will have:

```
CARChatbot/
├── backend/                    ← Python FastAPI server (12 endpoints)
│   ├── main.py                 ← API routes
│   ├── contract_analyzer.py    ← Regex-based extraction
│   ├── llm_sla_extracter.py    ← LLM-based extraction
│   ├── fairness_engine.py      ← Scoring engine
│   ├── price_service.py        ← Vehicle pricing
│   ├── vin_service.py          ← NHTSA API integration
│   ├── negotiation_assistant.py← Chatbot + email generation
│   ├── pdf_reader.py           ← PDF text extraction
│   ├── db.py                   ← Database schema + CRUD
│   ├── db_models.py            ← Pydantic models
│   ├── sla_schema.py           ← SLA field definitions
│   ├── init_db.py              ← DB initialization script
│   └── tests/                  ← 79 automated tests
├── app/                        ← Flutter mobile app
├── Dockerfile                  ← Container configuration
├── docker-compose.yml          ← Multi-service orchestration
├── requirements.txt            ← Python dependencies
└── pytest.ini                  ← Test configuration
```

---

[← Back to Table of Contents](../DOCUMENTATION.md) | [Next: Environment Setup →](02-environment-setup.md)
