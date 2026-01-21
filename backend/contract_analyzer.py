import re
from datetime import datetime


def clean_text(text: str) -> str:
    text = text.replace(",", "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_amount(patterns, text, cast=float):
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return cast(match.group(1))
            except:
                return None
    return None


def calculate_term_from_dates(text):
    match = re.search(
        r"beginning on (\w+ \d{4}).*?ending on (\w+ \d{4})",
        text,
        re.IGNORECASE
    )
    if match:
        start = datetime.strptime(match.group(1), "%B %Y")
        end = datetime.strptime(match.group(2), "%B %Y")
        return (end.year - start.year) * 12 + (end.month - start.month)
    return None


def analyze_contract(contract_text: str) -> dict:
    if not contract_text or len(contract_text) < 50:
        raise ValueError("Contract text too short")

    text = clean_text(contract_text)

    loan_type = (
        "Vehicle Lease" if re.search(r"lease", text, re.I)
        else "Car Loan" if re.search(r"loan|finance|emi", text, re.I)
        else None
    )

    apr_percent = extract_amount(
        [r"APR.*?(\d+\.?\d*)%", r"interest.*?(\d+\.?\d*)%"],
        text,
        float
    )

    monthly_payment = extract_amount(
        [r"monthly.*?₹?\s*([\d]+)", r"EMI.*?₹?\s*([\d]+)"],
        text,
        int
    )

    term_months = extract_amount(
        [r"(?:tenure|loan term|lease term).*?(\d+)\s*months"],
        text,
        int
    ) or calculate_term_from_dates(text)

    down_payment = extract_amount(
        [r"down payment.*?₹?\s*([\d]+)"],
        text,
        int
    )

    finance_amount = extract_amount(
        [r"loan amount.*?₹?\s*([\d]+)", r"amount financed.*?₹?\s*([\d]+)"],
        text,
        int
    )

    fees = {
        "documentation_fee": extract_amount([r"documentation fee.*?₹?\s*([\d]+)"], text, int),
        "registration_fee": extract_amount([r"registration fee.*?₹?\s*([\d]+)"], text, int),
        "processing_fee": extract_amount([r"processing fee.*?₹?\s*([\d]+)"], text, int)
    }

    early_term = extract_amount([r"early termination.*?₹?\s*([\d]+)"], text, int)

    penalties = {
        "late_payment": extract_amount([r"late payment.*?₹?\s*([\d]+)"], text, int),
        "early_termination": (
            "No penalty" if re.search(r"without penalty", text, re.I)
            else early_term if early_term else "Not specified"
        ),
        "over_mileage": extract_amount([r"over mileage.*?₹?\s*([\d]+)"], text, int)
    }

    red_flags = []
    if apr_percent and apr_percent > 12:
        red_flags.append("High interest rate")

    if penalties["early_termination"] not in ["No penalty", "Not specified"]:
        red_flags.append("Early termination penalty present")

    negotiation_points = []
    if apr_percent:
        negotiation_points.append("Ask for lower interest rate")
    if fees["documentation_fee"]:
        negotiation_points.append("Negotiate documentation fee")

    return {
        "loan_type": loan_type,
        "apr_percent": apr_percent,
        "monthly_payment": monthly_payment,
        "term_months": term_months,
        "down_payment": down_payment,
        "finance_amount": finance_amount,
        "fees": fees,
        "penalties": penalties,
        "red_flags": red_flags,
        "negotiation_points": negotiation_points
    }
def merge_rule_and_llm(rule_sla: dict, llm_sla: dict) -> dict:
    final = rule_sla.copy()
    for key, value in llm_sla.items():
        if final.get(key) in [None, "", []]:
            final[key] = value
    return final