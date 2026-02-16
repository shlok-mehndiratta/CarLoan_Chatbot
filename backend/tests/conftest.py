"""
Shared fixtures for the backend test suite.
"""

import os
import sys
import tempfile
import pytest

# Ensure the project root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi.testclient import TestClient


# ──────────────────── Sample data ──────────────────── #

SAMPLE_CONTRACT_TEXT = """
Vehicle Lease Agreement

Lease Term: 36 months
APR: 5.9%
Monthly Payment: $450
Down Payment: $3000
Residual Value: $18500
Mileage Allowance: 12000 miles/year
Overage Charge: $0.25 per mile
Early Termination: $2500 penalty
Documentation Fee: $500
Processing Fee: $200
Late Payment Penalty: $50
Vehicle: 2023 Toyota Camry SE
VIN: 4T1BF1FK5HU123456
"""

SAMPLE_SLA = {
    "loan_type": "Vehicle Lease",
    "apr_percent": 5.9,
    "monthly_payment": 450,
    "term_months": 36,
    "down_payment": 3000,
    "finance_amount": 25000,
    "fees": {
        "documentation_fee": 500,
        "registration_fee": None,
        "processing_fee": 200,
    },
    "penalties": {
        "late_payment": 50,
        "early_termination": 2500,
        "over_mileage": None,
    },
    "red_flags": [],
    "negotiation_points": ["Ask for lower interest rate", "Negotiate documentation fee"],
}

HIGH_APR_SLA = {
    "apr_percent": 22.0,
    "monthly_payment": 800,
    "term_months": 60,
    "finance_amount": 30000,
    "fees": {"documentation_fee": 15000, "processing_fee": 8000},
    "penalties": {"early_termination": 15000, "late_payment": 200},
    "red_flags": ["High interest rate", "Excessive fees", "Hidden penalty"],
}

FAIR_DEAL_SLA = {
    "apr_percent": 3.5,
    "monthly_payment": 350,
    "term_months": 36,
    "finance_amount": 12000,
    "fees": {"documentation_fee": None, "processing_fee": None},
    "penalties": {"early_termination": "No penalty"},
    "red_flags": [],
}


# ──────────────────── Fixtures ──────────────────── #

@pytest.fixture
def sample_sla():
    return SAMPLE_SLA.copy()


@pytest.fixture
def high_apr_sla():
    return HIGH_APR_SLA.copy()


@pytest.fixture
def fair_deal_sla():
    return FAIR_DEAL_SLA.copy()


@pytest.fixture
def sample_contract_text():
    return SAMPLE_CONTRACT_TEXT


@pytest.fixture
def test_client():
    """FastAPI test client with isolated temp DB."""
    import backend.db as db_module
    from backend.main import app

    # Use a temporary database
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    original_db = db_module.DB_PATH
    db_module.DB_PATH = db_path

    # Initialize tables
    from backend.init_db import init_db
    init_db()

    client = TestClient(app)
    yield client

    # Cleanup
    db_module.DB_PATH = original_db
    try:
        os.unlink(db_path)
    except OSError:
        pass


@pytest.fixture
def price_comparison_good():
    return {
        "comparison_available": True,
        "assessment": "good_deal",
        "deviation_percent": -8.0,
        "message": "Price is below market value",
    }


@pytest.fixture
def price_comparison_bad():
    return {
        "comparison_available": True,
        "assessment": "overpriced",
        "deviation_percent": 25.0,
        "message": "Vehicle appears overpriced",
    }
