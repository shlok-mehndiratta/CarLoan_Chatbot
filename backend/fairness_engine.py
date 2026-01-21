# fairness_engine.py
def calculate_fairness_score(sla: dict) -> dict:
    """
    Calculate a fairness score (0–100) for a car lease/loan contract
    based on extracted SLA fields.
    """

    score = 100
    reasons = []

    # 1️⃣ Interest rate check
    apr = sla.get("apr_percent")
    if apr:
        try:
            apr = float(apr)
            if apr > 12:
                score -= 20
                reasons.append("High interest rate")
        except ValueError:
            pass

    # 2️⃣ Early termination penalty
    penalties = sla.get("penalties", {})
    if penalties.get("early_termination") not in [None, "No penalty"]:
        score -= 15
        reasons.append("Early termination penalty present")

    # 3️⃣ High documentation fee
    fees = sla.get("fees", {})
    doc_fee = fees.get("documentation_fee")
    if doc_fee:
        try:
            if float(doc_fee) > 5000:
                score -= 10
                reasons.append("High documentation fee")
        except ValueError:
            pass

    # 4️⃣ No red flags bonus
    red_flags = sla.get("red_flags", [])
    if not red_flags:
        score += 5

    # 5️⃣ Ensure score boundaries
    score = max(0, min(score, 100))

    return {
        "fairness_score": score,
        "reasons": reasons
    }