# Chapter 3: Project Architecture & Database

[← Previous: Environment Setup](02-environment-setup.md) | [Back to Contents](../DOCUMENTATION.md) | [Next: PDF & Contract Analysis →](04-pdf-contract-analysis.md)

---

## 3.1 System Architecture

The system follows a **layered architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────┐
│                Flutter Mobile App                    │
│         (Dart — iOS/Android/Web)                     │
└────────────────────────┬────────────────────────────┘
                         │ HTTP REST API
┌────────────────────────▼────────────────────────────┐
│               FastAPI Backend (main.py)               │
│           12 endpoints — JSON request/response        │
├───────────────────────────────────────────────────────┤
│  Service Layer (business logic modules):              │
│                                                       │
│  ┌─────────────────┐  ┌──────────────────┐           │
│  │contract_analyzer│  │llm_sla_extracter │           │
│  │  (regex rules)  │  │  (Ollama LLM)    │           │
│  └────────┬────────┘  └────────┬─────────┘           │
│           │    merge_rule_and_llm()   │               │
│           └────────────┬─────────────┘               │
│                        ▼                              │
│  ┌─────────────────┐  ┌──────────────────┐           │
│  │fairness_engine  │  │price_service     │           │
│  │(scoring 0-100)  │  │(MSRP+depreciation│           │
│  └─────────────────┘  └──────────────────┘           │
│  ┌─────────────────┐  ┌──────────────────┐           │
│  │vin_service      │  │negotiation_asst  │           │
│  │(NHTSA APIs)     │  │(chatbot+email)   │           │
│  └─────────────────┘  └──────────────────┘           │
├───────────────────────────────────────────────────────┤
│  Data Layer:                                          │
│  ┌───────────┐  ┌────────────┐  ┌──────────────┐    │
│  │  db.py    │  │db_models.py│  │sla_schema.py │    │
│  │ (SQLite)  │  │ (Pydantic) │  │(field defs)  │    │
│  └───────────┘  └────────────┘  └──────────────┘    │
└───────────────────────────────────────────────────────┘
         │                              │
   ┌─────▼─────┐              ┌────────▼────────┐
   │  SQLite    │              │  Ollama Server  │
   │ database.db│              │ localhost:11434  │
   └────────────┘              └─────────────────┘
```

### Why This Architecture?

1. **Separation of concerns** — Each module does one thing well. `contract_analyzer.py` only does regex extraction. `fairness_engine.py` only does scoring. This makes the code easier to understand, test, and modify.

2. **Graceful degradation** — If Ollama isn't running, the system still works using only rule-based extraction. If NHTSA is down, VIN lookup fails gracefully without crashing the whole app.

3. **Stateless API** — The FastAPI backend doesn't store any session state in memory. All persistent data goes to SQLite. This means you can restart the server without losing any data.

---

## 3.2 The SLA Schema — Defining What to Extract

Before building any extraction logic, we need to define **what fields** we want to extract from contracts. This is the "schema" — a template with all possible fields.

### File: `backend/sla_schema.py`

```python
SLA_SCHEMA = {
    "contract_type": None,
    "interest_rate_apr": None,
    "lease_term_months": None,
    "monthly_payment": None,
    "down_payment": None,
    "residual_value": None,
    "mileage_allowance": None,
    "overage_charge_per_mile": None,
    "early_termination_clause": None,
    "purchase_option_price": None,
    "maintenance_responsibility": None,
    "warranty_coverage": None,
    "insurance_requirements": None,
    "late_payment_penalty": None,
    "red_flags": [],
    "contract_fairness_score": None
}
```

**Why this file exists:**
- It acts as a **contract** (ironic!) between the extraction systems and the rest of the app
- Both the rule-based extractor and the LLM extractor know exactly which fields to populate
- The LLM receives this list to know what to extract
- Missing values stay as `None` — the system knows what it couldn't find

---

## 3.3 Pydantic Data Models

Pydantic models enforce **type safety** on API inputs and outputs. When you send a request like `{"year": "abc"}` to an endpoint that expects an integer, Pydantic automatically rejects it with a clear error message.

### File: `backend/db_models.py`

```python
"""
Pydantic models for request / response validation.
Shared across API endpoints, services, and DB layer.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ──────────────── SLA / Contract Analysis ──────────────── #

class SLAResult(BaseModel):
    """Structured output from contract analysis (rule + LLM merged)."""
    loan_type: Optional[str] = Field(None, description="Vehicle Lease or Car Loan")
    apr_percent: Optional[float] = Field(None, description="Annual interest rate")
    monthly_payment: Optional[float] = None
    term_months: Optional[int] = None
    down_payment: Optional[float] = None
    finance_amount: Optional[float] = None
    residual_value: Optional[float] = None
    mileage_allowance: Optional[int] = None
    overage_charge_per_mile: Optional[float] = None
    early_termination_clause: Optional[str] = None
    purchase_option_price: Optional[float] = None
    maintenance_responsibility: Optional[str] = None
    warranty_coverage: Optional[str] = None
    insurance_requirements: Optional[str] = None
    fees: Optional[dict] = Field(default_factory=dict)
    penalties: Optional[dict] = Field(default_factory=dict)
    red_flags: list[str] = Field(default_factory=list)
    negotiation_points: list[str] = Field(default_factory=list)


class FairnessResult(BaseModel):
    """Output from the fairness scoring engine."""
    fairness_score: float = Field(ge=0, le=100)
    reasons: list[str] = Field(default_factory=list)


class ContractAnalysisResponse(BaseModel):
    """Full response from /analyze."""
    contract_id: int
    sla: SLAResult
    fairness: FairnessResult
    extraction_method: str = "rule_based"


# ──────────────── Vehicle / VIN ──────────────── #

class VehicleInfo(BaseModel):
    vin: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[str] = None
    trim: Optional[str] = None
    body_class: Optional[str] = None
    engine: Optional[str] = None
    fuel_type: Optional[str] = None
    drive_type: Optional[str] = None
    plant_info: Optional[str] = None


class RecallInfo(BaseModel):
    nhtsa_campaign: Optional[str] = None
    component: Optional[str] = None
    summary: Optional[str] = None
    consequence: Optional[str] = None
    remedy: Optional[str] = None
    report_date: Optional[str] = None


class VINResponse(BaseModel):
    vehicle: VehicleInfo
    recalls: list[RecallInfo] = Field(default_factory=list)
    recalls_count: int = 0


# ──────────────── Negotiation ──────────────── #

class NegotiationStartRequest(BaseModel):
    contract_id: int
    user_message: Optional[str] = None


class ChatMessage(BaseModel):
    role: str
    content: str
    created_at: Optional[str] = None


class NegotiationChatRequest(BaseModel):
    thread_id: int
    message: str


class NegotiationChatResponse(BaseModel):
    thread_id: int
    reply: str
    history: list[ChatMessage] = Field(default_factory=list)


# ──────────────── Price Estimation ──────────────── #

class PriceEstimateRequest(BaseModel):
    make: str
    model: str
    year: int
    mileage: Optional[int] = None
    condition: Optional[str] = Field("good", description="excellent/good/fair/poor")


class PriceEstimateResponse(BaseModel):
    make: str
    model: str
    year: int
    low_price: float
    market_price: float
    high_price: float
    confidence: float = Field(ge=0, le=1)
    source: str = "estimation_engine"
    notes: list[str] = Field(default_factory=list)
```

**Key Pydantic concepts used:**

| Concept | Example | What It Does |
|---------|---------|--------------|
| `Optional[str]` | `loan_type: Optional[str] = None` | Field can be a string OR None |
| `Field(ge=0, le=100)` | `fairness_score: float` | Must be between 0 and 100 |
| `default_factory=list` | `red_flags: list[str]` | Each instance gets its own empty list |
| `Field(description=...)` | `apr_percent` | Auto-generates API documentation |

---

## 3.4 Database Schema

SQLite is our database — it stores everything in a single file called `database.db`. No database server installation needed.

### File: `backend/db.py`

The database has **11 tables**. Here's each table and why it exists:

```
┌──────────────────────────────────────────────────────────┐
│                    DATABASE SCHEMA                        │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  users ──────┐                                           │
│              ├──→ contracts ──→ sla_extractions          │
│  dealers ────┘        │    └──→ extracted_clauses        │
│                       │    └──→ contract_files           │
│  vehicles ───→ vehicle_recalls                           │
│       │                                                  │
│       └──→ price_recommendations                         │
│                                                          │
│  negotiation_threads ──→ negotiation_messages            │
│                                                          │
│  price_sources                                           │
│  offer_comparisons                                       │
└──────────────────────────────────────────────────────────┘
```

Here's the schema SQL (the most important tables excerpted):

```sql
-- Contracts: stores the uploaded PDF data
CREATE TABLE IF NOT EXISTS contracts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER,
    dealer_id       INTEGER,
    vehicle_id      INTEGER,
    file_name       TEXT NOT NULL,
    raw_text        TEXT NOT NULL,       -- full extracted text
    contract_type   TEXT,                -- "lease" or "loan"
    status          TEXT DEFAULT 'analyzed',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)   REFERENCES users(id),
    FOREIGN KEY (dealer_id) REFERENCES dealers(id),
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
);

-- SLA Extractions: stores the JSON result of analysis
CREATE TABLE IF NOT EXISTS sla_extractions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id     INTEGER NOT NULL,
    sla_json        TEXT NOT NULL,          -- JSON blob
    extraction_method TEXT DEFAULT 'rule_based',  -- or 'merged'
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contract_id) REFERENCES contracts(id)
);

-- Vehicles: decoded from VIN
CREATE TABLE IF NOT EXISTS vehicles (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    vin             TEXT UNIQUE,
    make            TEXT,
    model           TEXT,
    year            INTEGER,
    body_class      TEXT,
    engine          TEXT,
    raw_nhtsa_json  TEXT,       -- complete NHTSA response for reference
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Negotiation: threaded chat conversations
CREATE TABLE IF NOT EXISTS negotiation_threads (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id     INTEGER,
    title           TEXT,
    status          TEXT DEFAULT 'active',
    context_json    TEXT,        -- contract context for the chatbot
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS negotiation_messages (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    thread_id       INTEGER NOT NULL,
    role            TEXT CHECK(role IN ('user', 'assistant')) NOT NULL,
    content         TEXT NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (thread_id) REFERENCES negotiation_threads(id)
);
```

### CRUD Helper Functions

The `db.py` file also contains helper functions for common database operations. Here are the key ones:

```python
def save_contract(file_name: str, raw_text: str, ...) -> int:
    """Save a new contract and return its ID."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO contracts (...) VALUES (...)", (...))
    contract_id = cur.lastrowid
    conn.commit()
    conn.close()
    return contract_id

def get_contract(contract_id: int) -> dict | None:
    """Retrieve a contract by ID. Returns None if not found."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM contracts WHERE id = ?", (contract_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def save_negotiation_message(thread_id: int, role: str, content: str):
    """Save a chat message (user or assistant) to a thread."""
    conn = get_connection()
    conn.execute("INSERT INTO negotiation_messages (...) VALUES (...)", (...))
    conn.commit()
    conn.close()

def get_negotiation_history(thread_id: int) -> list:
    """Get all messages in a thread, ordered chronologically."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT role, content, created_at FROM negotiation_messages WHERE thread_id = ? ORDER BY id ASC",
        (thread_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
```

### Database Initialization: `backend/init_db.py`

```python
"""Initialize the database with the full schema."""
from backend.db import init_db

if __name__ == "__main__":
    init_db()
    print("✅ Database initialized with full schema")
```

Run it with:
```bash
python -m backend.init_db
```

This creates all 11 tables. It's safe to run multiple times — `CREATE TABLE IF NOT EXISTS` prevents errors.

---

## 3.5 Create Empty `__init__.py`

Python needs an `__init__.py` file in directories to treat them as packages:

```bash
touch backend/__init__.py
touch backend/tests/__init__.py
```

---

## 3.6 Verification

After creating all files in this chapter, verify:

```bash
# Run the init script
python -m backend.init_db
# Expected: ✅ Database initialized with full schema

# Check that the database file was created
ls -la backend/database.db
# Should show the file with some size

# Test that imports work
python -c "from backend.db_models import SLAResult; print('✅ Models OK')"
python -c "from backend.sla_schema import SLA_SCHEMA; print(f'✅ Schema has {len(SLA_SCHEMA)} fields')"
```

---

[← Previous: Environment Setup](02-environment-setup.md) | [Back to Contents](../DOCUMENTATION.md) | [Next: PDF & Contract Analysis →](04-pdf-contract-analysis.md)
