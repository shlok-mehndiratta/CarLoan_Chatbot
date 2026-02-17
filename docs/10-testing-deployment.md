# Chapter 10: Testing & Deployment

[← Previous: Flutter App](09-flutter-app.md) | [Back to Contents](../DOCUMENTATION.md)

---

## 10.1 Testing Strategy

Testing ensures that code works correctly and continues to work as you make changes. Our test suite covers **79 tests** across 4 modules.

### Test File Structure

```
backend/tests/
├── __init__.py              ← Makes tests a Python package
├── conftest.py              ← Shared fixtures used by all tests
├── test_contract_analyzer.py ← 23 tests
├── test_fairness_engine.py  ← 19 tests
├── test_price_service.py    ← 28 tests
└── test_api.py              ← 12 tests (integration)
```

### What Is a Test Fixture?

A **fixture** is reusable test data or setup code. Instead of repeating the same setup in every test, you define it once in `conftest.py`.

### File: `backend/tests/conftest.py`

```python
"""
Shared test fixtures for the entire test suite.
pytest automatically discovers and loads conftest.py.
"""

import pytest
import os
import tempfile


@pytest.fixture
def sample_sla():
    """A typical car loan SLA for testing."""
    return {
        "loan_type": "Car Loan",
        "apr_percent": 8.5,
        "monthly_payment": 450.0,
        "term_months": 60,
        "down_payment": 5000.0,
        "finance_amount": 25000.0,
        "fees": {"documentation_fee": 500.0},
        "penalties": {"late_payment": 50.0},
        "red_flags": [],
    }


@pytest.fixture
def bad_sla():
    """An unfair contract with many red flags."""
    return {
        "loan_type": "Car Loan",
        "apr_percent": 22.0,
        "monthly_payment": 800.0,
        "term_months": 72,
        "finance_amount": 35000.0,
        "fees": {"documentation_fee": 6000.0, "processing_fee": 3000.0},
        "penalties": {"early_termination": "8000", "late_payment": 200.0},
        "red_flags": ["High APR", "Excessive fees", "Hidden clauses"],
    }


@pytest.fixture
def sample_contract_text():
    """Simulated contract text with extractable data."""
    return """
    CAR LOAN AGREEMENT
    Annual Percentage Rate (APR): 9.5%
    Monthly Payment: $499.99
    Loan Term: 60 months
    Down Payment: $5,000
    Amount Financed: $25,000
    Documentation Fee: $500
    Late Payment Fee: $50
    Early Termination Penalty: $2,000
    """


@pytest.fixture
def sample_price_comparison():
    """Price comparison data for fairness engine."""
    return {
        "comparison_available": True,
        "finance_amount": 30000,
        "market_price": 25000,
        "diff_percent": 20.0,
        "assessment": "overpriced",
    }
```

---

## 10.2 Unit Tests

### Contract Analyzer Tests (23 tests)

```python
# backend/tests/test_contract_analyzer.py

from backend.contract_analyzer import analyze_contract, clean_text, extract_amount, merge_rule_and_llm

class TestCleanText:
    def test_collapses_whitespace(self):
        assert clean_text("hello   world") == "hello world"

    def test_removes_commas(self):
        assert clean_text("25,000") == "25000"

    def test_strips_edges(self):
        assert clean_text("  hello  ") == "hello"


class TestExtractAmount:
    def test_finds_percentage(self):
        assert extract_amount("APR is 8.5%", r"(\d+\.?\d*)%") == 8.5

    def test_finds_dollar_amount(self):
        assert extract_amount("payment of $499.99", r"\$?([\d.]+)") == 499.99

    def test_returns_none_when_not_found(self):
        assert extract_amount("no numbers here", r"(\d+)%") is None


class TestAnalyzeContract:
    def test_detects_loan_type(self):
        result = analyze_contract("This car loan agreement has a finance rate of 5%")
        assert result["loan_type"] == "Car Loan"

    def test_detects_lease_type(self):
        result = analyze_contract("This vehicle lease agreement has terms for 36 months")
        assert result["loan_type"] == "Vehicle Lease"

    def test_extracts_apr(self):
        result = analyze_contract("The APR is 9.5% for this car loan agreement over 60 months")
        assert result["apr_percent"] == 9.5

    def test_extracts_monthly_payment(self):
        result = analyze_contract("Monthly payment of $450 for this car loan over 60 months")
        assert result["monthly_payment"] == 450.0

    def test_flags_high_apr(self):
        result = analyze_contract("This car loan has an APR of 22% over 60 months")
        assert any("High interest" in f for f in result["red_flags"])


class TestMerge:
    def test_rule_takes_priority(self):
        rule = {"apr_percent": 8.5, "monthly_payment": None}
        llm = {"apr_percent": 8.0, "monthly_payment": 499.0}
        merged = merge_rule_and_llm(rule, llm)
        assert merged["apr_percent"] == 8.5      # Rule wins
        assert merged["monthly_payment"] == 499.0  # LLM fills gap
```

### Fairness Engine Tests (19 tests)

```python
# backend/tests/test_fairness_engine.py

from backend.fairness_engine import calculate_fairness_score

class TestAPRScoring:
    def test_low_apr_no_penalty(self):
        result = calculate_fairness_score({"apr_percent": 5.0})
        assert result["fairness_score"] >= 95

    def test_high_apr_major_penalty(self):
        result = calculate_fairness_score({"apr_percent": 22.0})
        assert result["fairness_score"] <= 75

    def test_moderate_apr(self):
        result = calculate_fairness_score({"apr_percent": 12.0})
        assert 70 <= result["fairness_score"] <= 95


class TestRedFlags:
    def test_no_flags_gives_bonus(self):
        result = calculate_fairness_score({"red_flags": []})
        assert result["fairness_score"] > 100  # Clamped to 100

    def test_many_flags_penalize(self):
        result = calculate_fairness_score({
            "red_flags": ["flag1", "flag2", "flag3"]
        })
        assert result["fairness_score"] < 100


class TestRatings:
    def test_excellent_rating(self):
        result = calculate_fairness_score({"apr_percent": 4.0})
        assert result["rating"] == "Excellent"

    def test_poor_rating(self):
        result = calculate_fairness_score({
            "apr_percent": 25.0,
            "fees": {"documentation_fee": 8000},
            "red_flags": ["a", "b", "c"],
        })
        assert result["rating"] == "Poor"
```

### Price Service Tests (28 tests)

```python
# backend/tests/test_price_service.py

from backend.price_service import estimate_price, _find_msrp, _get_depreciation_factor

class TestMSRPLookup:
    def test_exact_match(self):
        msrp, source = _find_msrp("Toyota", "Camry", 2023)
        assert msrp > 0
        assert source == "msrp_database"

    def test_unknown_model(self):
        msrp, source = _find_msrp("UnknownMake", "UnknownModel", 2023)
        assert msrp is None


class TestDepreciation:
    def test_new_car(self):
        assert _get_depreciation_factor(0) == 1.0

    def test_one_year_old(self):
        assert _get_depreciation_factor(1) == 0.80

    def test_ten_year_old(self):
        assert _get_depreciation_factor(10) == 0.23


class TestEstimatePrice:
    def test_known_vehicle(self):
        result = estimate_price("Toyota", "Camry", 2023)
        assert result["low_price"] < result["market_price"] < result["high_price"]
        assert result["confidence"] > 0.5

    def test_mileage_affects_price(self):
        low_mile = estimate_price("Honda", "Civic", 2022, mileage=10000)
        high_mile = estimate_price("Honda", "Civic", 2022, mileage=100000)
        assert low_mile["market_price"] > high_mile["market_price"]

    def test_condition_affects_price(self):
        excellent = estimate_price("Ford", "F-150", 2023, condition="excellent")
        poor = estimate_price("Ford", "F-150", 2023, condition="poor")
        assert excellent["market_price"] > poor["market_price"]
```

---

## 10.3 Integration Tests

### API Tests (12 tests)

```python
# backend/tests/test_api.py

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

class TestHealthEndpoints:
    def test_home(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "running" in response.json()["message"]

    def test_health(self):
        response = client.get("/health")
        assert response.json()["status"] == "ok"

class TestPriceEstimate:
    def test_valid_request(self):
        response = client.post("/price-estimate", json={
            "make": "Toyota", "model": "Camry", "year": 2023
        })
        data = response.json()
        assert "market_price" in data
        assert data["market_price"] > 0

    def test_with_mileage(self):
        response = client.post("/price-estimate", json={
            "make": "Honda", "model": "Civic", "year": 2022,
            "mileage": 50000, "condition": "good"
        })
        assert response.status_code == 200

class TestVINEndpoints:
    def test_invalid_vin_length(self):
        response = client.get("/vin/SHORT")
        assert "error" in response.json()
```

---

## 10.4 Running the Test Suite

### Configuration: `pytest.ini`

```ini
[pytest]
testpaths = backend/tests
asyncio_mode = auto
addopts = -v -p no:launch_ros -p no:launch_testing -p no:ament_pep257
          -p no:ament_copyright -p no:ament_flake8 -p no:ament_lint_cmake
          -p no:ament_xmllint -p no:launch
```

> **Note:** The `-p no:launch_ros` flags disable ROS 2 pytest plugins that may be installed system-wide. Without these, the tests crash with `INTERNALERROR`.

### Running Tests

```bash
# Run all tests with verbose output
python -m pytest -v

# Run a specific test file
python -m pytest backend/tests/test_price_service.py -v

# Run tests matching a pattern
python -m pytest -k "test_apr" -v

# Run with coverage report
python -m pytest --cov=backend -v
```

### Expected Output

```
backend/tests/test_contract_analyzer.py::TestCleanText::test_collapses_whitespace     PASSED
backend/tests/test_contract_analyzer.py::TestCleanText::test_removes_commas           PASSED
...
backend/tests/test_api.py::TestHealthEndpoints::test_home                             PASSED
backend/tests/test_api.py::TestHealthEndpoints::test_health                           PASSED

======================== 79 passed in 8.48s ========================
```

---

## 10.5 Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.12-slim

# Install system dependencies for PDF/OCR processing
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Create uploads directory
RUN mkdir -p uploads

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml

```yaml
version: "3.8"

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OLLAMA_HOST=http://ollama:11434
    depends_on:
      - ollama
    volumes:
      - db_data:/app/backend
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    restart: unless-stopped

volumes:
  db_data:
  ollama_data:
```

### .dockerignore

```
venv/
app/
.git/
__pycache__/
*.pyc
uploads/*
backend/database.db
.env
```

### Running with Docker

```bash
# Build and start all services
docker-compose up --build -d

# Pull the LLM model into the Ollama container
docker exec -it carchatbot_ollama_1 ollama pull llama3.2

# View logs
docker-compose logs -f backend

# Stop all services
docker-compose down
```

---

## 10.6 Complete Verification Checklist

```
✅ All 79 tests passing (python -m pytest -v)
✅ Backend starts without errors (uvicorn backend.main:app --reload)
✅ /docs endpoint shows Swagger UI
✅ /health returns {"status": "ok"}
✅ /price-estimate works with valid input
✅ /vin/{vin} returns vehicle data (with real VIN)
✅ /analyze accepts PDF uploads
✅ Flutter app connects to backend
✅ Docker build succeeds
✅ docker-compose up starts both services
```

---

## Congratulations! 🎉

You've built a complete AI-powered contract review system from scratch. The system includes:

- **Smart contract analysis** with dual extraction (regex + LLM)
- **Fairness scoring** across 6 dimensions
- **VIN-based vehicle intelligence** via NHTSA
- **Price estimation** with depreciation modeling
- **AI negotiation chatbot** with multi-turn conversations
- **Professional email generation**
- **Flutter mobile app** with 6 screens
- **79 automated tests** for confidence
- **Docker deployment** for production

---

[← Previous: Flutter App](09-flutter-app.md) | [Back to Contents](../DOCUMENTATION.md)
