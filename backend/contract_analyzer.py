import os
import json
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

SLA_SCHEMA = {
    "loan_type": None,
    "apr_percent": None,
    "monthly_payment": None,
    "term_months": None,
    "down_payment": None,
    "finance_amount": None,
    "fees": {},
    "penalties": {},
    "red_flags": [],
    "negotiation_points": []
}

def analyze_contract(text: str):
    """
    MOCK SLA extraction for demo & interviews
    """

    return {
        "loan_type": "Lease",
        "apr_percent": 8.5,
        "monthly_payment": 14500,
        "term_months": 36,
        "down_payment": 50000,
        "finance_amount": 780000,
        "fees": {
            "documentation_fee": 2500,
            "acquisition_fee": 3000,
            "registration_fee": 1800,
            "other_fees": 0
        },
        "penalties": {
            "late_payment": "₹500 per delay",
            "early_termination": "₹25,000",
            "over_mileage": "₹10/km"
        },
        "red_flags": [
            "High early termination penalty"
        ],
        "negotiation_points": [
            "Reduce documentation fee",
            "Lower APR"
        ]
    }