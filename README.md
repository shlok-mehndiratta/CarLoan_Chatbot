# 🚗 AI-Powered Car Lease & Loan Contract Review & Negotiation Assistant

> Developed as part of the **Infosys Virtual Internship Program**

---

## 📌 Overview

The **Car Lease / Loan Contract Review & Negotiation Assistant** is an AI-powered application that helps users understand, analyze, and negotiate car lease or loan agreements.

Car financing contracts are often long, complex, and filled with financial terms that are difficult to interpret. This system uses **Large Language Models (LLMs)** to automatically extract important clauses, analyze pricing fairness, verify vehicle details using VIN data, and assist users in negotiating better terms.

> **Goal:** Turn confusing car contracts into clear, structured, and actionable insights.

---

## 🎯 Problem Statement

Most consumers sign auto lease or loan contracts without fully understanding:

- Actual APR (Annual Percentage Rate)
- Hidden fees and penalties
- Early termination conditions
- Mileage overage charges
- Residual value structure
- Whether the deal is fair compared to the market

This creates **information asymmetry** between dealers and customers. This project reduces that gap using AI.

---

## 🚀 Key Features

### 1️⃣ AI-Based Contract Analysis
Upload a lease/loan contract (PDF or image), and the system extracts:
- Interest Rate / APR, Lease Term, Monthly Payment
- Down Payment, Residual Value, Finance Amount
- Mileage Allowance & Overage Charges
- Early Termination Clause, Buyout Option
- Warranty, Insurance, Maintenance Coverage
- Late Fees / Penalties

**Dual extraction:** Rule-based regex + LLM (Ollama) extraction are merged for best accuracy.

**Output:** Structured JSON + Fairness Score (0–100)

### 2️⃣ Vehicle Price Estimation
Depreciation-based fair market value estimation using:
- Built-in MSRP database (10+ makes, 25+ models, 10 years of data)
- Age-based depreciation curves
- Mileage and condition adjustments
- Category-based fallback for unlisted vehicles

**Output:** Low / Market / High price range with confidence score

### 3️⃣ VIN-Based Vehicle Information
Using the vehicle's VIN number, the app retrieves from NHTSA:
- Vehicle make, model, year, body class, engine specs
- **Recall history** with severity and remedy details
- **Safety complaints** count

### 4️⃣ AI Negotiation Assistant
An intelligent chatbot powered by Ollama/LLM that:
- Analyzes contract context to identify leverage points
- Provides turn-by-turn negotiation guidance
- Generates professional negotiation emails
- Maintains conversation history per thread

### 5️⃣ Mobile-First Interface (Flutter)
The app includes:
- **Analyze** — PDF upload and contract analysis
- **VIN Lookup** — Vehicle decode with recalls and complaints
- **Price Estimate** — Manual or VIN-based price estimation
- **Dashboard** — Summary view with quick actions
- **Negotiation Chat** — AI-powered chat with strategy suggestions

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| **Backend API** | Python 3.12, FastAPI, Uvicorn |
| **LLM Engine** | Ollama (Llama 3.2), LangChain |
| **PDF Processing** | PyPDF2, pdfplumber, pdfminer, Tesseract OCR |
| **Vehicle Data** | NHTSA Decode/Recalls/Complaints APIs |
| **Database** | SQLite (via Python `sqlite3`) |
| **Mobile App** | Flutter / Dart |
| **HTTP Client** | httpx (testing), requests (VIN/API calls) |
| **Containerization** | Docker, docker-compose |

---

## 📂 Project Structure

```
CARChatbot/
├── backend/
│   ├── main.py                    # FastAPI app — all API endpoints
│   ├── contract_analyzer.py       # Rule-based SLA extraction (regex)
│   ├── llm_sla_extracter.py       # LLM-based SLA extraction (Ollama)
│   ├── fairness_engine.py         # Fairness score calculator (0–100)
│   ├── price_service.py           # MSRP database + depreciation engine
│   ├── vin_service.py             # NHTSA VIN decode, recalls, complaints
│   ├── negotiation_assistant.py   # AI negotiation chatbot
│   ├── pdf_reader.py              # PDF text extraction (multi-method)
│   ├── db.py                      # SQLite database connection/queries
│   ├── db_models.py               # Pydantic data models
│   ├── init_db.py                 # Database schema initialization
│   ├── sla_schema.py              # SLA field definitions
│   └── tests/
│       ├── conftest.py            # Shared fixtures & test data
│       ├── test_contract_analyzer.py  # 23 unit tests
│       ├── test_fairness_engine.py    # 19 unit tests
│       ├── test_price_service.py      # 28 unit tests
│       └── test_api.py               # 12 integration tests
├── app/                           # Flutter mobile application
│   └── lib/
│       ├── main.dart              # App entry + bottom navigation
│       ├── models/
│       │   └── contract_model.dart # 10 data models
│       ├── screens/
│       │   ├── home_screen.dart           # PDF upload
│       │   ├── result_screen.dart         # Analysis results
│       │   ├── vin_lookup_screen.dart     # VIN decoder
│       │   ├── price_estimation_screen.dart # Price estimator
│       │   ├── negotiation_chat_screen.dart # AI chat
│       │   └── comparison_dashboard_screen.dart # Dashboard
│       └── services/
│           └── api_service.dart   # 10 API integration methods
├── requirements.txt               # Python dependencies
├── pytest.ini                     # Test configuration
├── Dockerfile                     # Backend container
├── docker-compose.yml             # Multi-service orchestration
└── README.md                      # This file
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Service banner |
| `GET` | `/health` | Health check |
| `POST` | `/analyze` | Upload PDF → full contract analysis |
| `GET` | `/contract/{id}` | Retrieve saved analysis |
| `GET` | `/vin/{vin}` | Full VIN decode + recalls + complaints |
| `GET` | `/vin/{vin}/recalls` | VIN recall lookup |
| `POST` | `/price-estimate` | Estimate vehicle price (manual input) |
| `GET` | `/price-estimate/vin/{vin}` | Estimate price by VIN |
| `POST` | `/negotiate/start` | Start negotiation session |
| `POST` | `/negotiate/chat` | Send message in negotiation |
| `GET` | `/negotiate/history/{id}` | Get chat history |
| `POST` | `/negotiate/email` | Generate negotiation email |

---

## ▶️ How to Run

### Prerequisites
- Python 3.12+
- [Ollama](https://ollama.ai/) with `llama3.2` model pulled
- Flutter SDK (for mobile app)

### Backend

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the API server
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`. Swagger docs at `http://localhost:8000/docs`.

### Flutter App

```bash
cd app
cp .env.example .env   # Set API_URL=http://<your-ip>:8000

flutter pub get
flutter run
```

### Running Tests

```bash
source venv/bin/activate
python -m pytest backend/tests/ -v
```

### Docker

```bash
docker-compose up --build
```

This starts:
- **Backend** on port `8000`
- **Ollama** LLM service on port `11434`

---

## 📊 Contract Fairness Score

The fairness score (0–100) is computed across 6 dimensions:

| Dimension | Impact |
|-----------|--------|
| APR vs market rates | Up to −30 points |
| Early termination penalties | Up to −20 points |
| Documentation/processing fees | Up to −15 points |
| Red flags detected | Up to −15 points |
| Price comparison vs market | Up to −20 / +5 points |
| Total interest burden | Up to −10 points |

**Ratings:** Excellent (85+), Good (70–84), Fair (55–69), Below Average (40–54), Poor (0–39)

---

## 🧪 Test Coverage

| Module | Tests | Coverage |
|--------|-------|----------|
| `contract_analyzer.py` | 23 | clean_text, extract_amount, analyze_contract, merge_rule_and_llm |
| `fairness_engine.py` | 19 | APR tiers, fees, penalties, red flags, price comparison, ratings |
| `price_service.py` | 28 | MSRP lookup, depreciation, mileage/condition, full estimation |
| API Integration | 12 | Health, price, VIN, contract retrieval, negotiation |
| **Total** | **79** | **All passing ✅** |

---

## 🔮 Future Improvements

- Fine-tuned legal LLM model for better contract understanding
- Dealer-side analytics dashboard
- Integration with paid vehicle history APIs (e.g., Carfax)
- Web version alongside mobile app
- Advanced fairness scoring using ML models
- User authentication and contract history

---

## ⚠️ Limitations

- LLM outputs may require validation for legal accuracy
- OCR quality affects extraction precision
- Some vehicle pricing APIs offer limited free access
- NHTSA data may have delays for recent recalls
- Ollama must be running locally for LLM features

---

## 🎓 Internship Acknowledgment

This project was developed as part of the **Infosys Virtual Internship Program**, where the objective was to design and prototype an AI-driven solution addressing real-world financial and consumer transparency challenges.

---

## 📜 License

MIT License

---

## ✨ Final Note

Car contracts are complex by design.
This project transforms them into structured, understandable, and negotiable financial documents using AI.