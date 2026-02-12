"""
Fairness Engine — Contract Fairness Score Calculator

Evaluates a car lease/loan contract on multiple dimensions:
  1. Interest rate (APR) vs market norms
  2. Early termination penalties
  3. Documentation / processing fees
  4. Red flags from extraction
  5. Price comparison vs market value (when available)
  6. Monthly payment burden analysis

Produces a score from 0 (very unfair) to 100 (excellent deal).
"""

import logging

logger = logging.getLogger(__name__)


def calculate_fairness_score(sla: dict, price_comparison: dict = None) -> dict:
    """
    Calculate a fairness score (0–100) for a car lease/loan contract.

    Args:
        sla: Extracted SLA fields from the contract
        price_comparison: Optional price comparison result from price_service

    Returns:
        dict with fairness_score, rating, reasons, and summary
    """
    score = 100
    reasons = []

    # ─── 1. Interest rate check ─── #
    apr = sla.get("apr_percent") or sla.get("interest_rate_apr")
    if apr:
        try:
            apr = float(apr)
            if apr > 18:
                score -= 30
                reasons.append(f"Very high interest rate ({apr}%)")
            elif apr > 12:
                score -= 20
                reasons.append(f"High interest rate ({apr}%)")
            elif apr > 8:
                score -= 10
                reasons.append(f"Above-average interest rate ({apr}%)")
        except (ValueError, TypeError):
            pass

    # ─── 2. Early termination penalty ─── #
    penalties = sla.get("penalties", {})
    early_term = penalties.get("early_termination")
    if early_term and early_term not in [None, "No penalty", "Not specified"]:
        try:
            early_val = float(early_term)
            if early_val > 10000:
                score -= 20
                reasons.append(f"Heavy early termination penalty (₹{early_val:,.0f})")
            else:
                score -= 10
                reasons.append("Early termination penalty present")
        except (ValueError, TypeError):
            score -= 15
            reasons.append("Early termination penalty present")

    # ─── 3. Fee checks ─── #
    fees = sla.get("fees", {})

    doc_fee = fees.get("documentation_fee")
    if doc_fee:
        try:
            doc_val = float(doc_fee)
            if doc_val > 10000:
                score -= 15
                reasons.append(f"Very high documentation fee (₹{doc_val:,.0f})")
            elif doc_val > 5000:
                score -= 10
                reasons.append(f"High documentation fee (₹{doc_val:,.0f})")
        except (ValueError, TypeError):
            pass

    processing_fee = fees.get("processing_fee")
    if processing_fee:
        try:
            proc_val = float(processing_fee)
            if proc_val > 5000:
                score -= 8
                reasons.append(f"High processing fee (₹{proc_val:,.0f})")
        except (ValueError, TypeError):
            pass

    # ─── 4. Red flags penalty ─── #
    red_flags = sla.get("red_flags", [])
    if red_flags:
        flag_penalty = min(len(red_flags) * 5, 15)
        score -= flag_penalty
        reasons.append(f"{len(red_flags)} red flag(s) detected")
    else:
        score += 5
        reasons.append("No red flags — positive indicator")

    # ─── 5. Price comparison (if available) ─── #
    if price_comparison and price_comparison.get("comparison_available"):
        assessment = price_comparison.get("assessment", "")
        deviation = price_comparison.get("deviation_percent", 0)

        if assessment == "overpriced":
            score -= 20
            reasons.append(f"Vehicle appears overpriced by {deviation:.0f}%")
        elif assessment == "slightly_above_market":
            score -= 8
            reasons.append(f"Price slightly above market by {deviation:.0f}%")
        elif assessment == "good_deal":
            score += 5
            reasons.append(f"Price is {abs(deviation):.0f}% below market — good deal")

    # ─── 6. Monthly payment analysis ─── #
    monthly = sla.get("monthly_payment")
    finance = sla.get("finance_amount")
    term = sla.get("term_months")

    if monthly and finance and term:
        try:
            monthly = float(monthly)
            finance = float(finance)
            term = int(term)
            if term > 0:
                total_paid = monthly * term
                total_interest = total_paid - finance
                interest_ratio = total_interest / finance if finance > 0 else 0

                if interest_ratio > 0.30:
                    score -= 10
                    reasons.append(f"Total interest is {interest_ratio*100:.0f}% of principal")
                elif interest_ratio > 0.20:
                    score -= 5
                    reasons.append(f"Moderate total interest ({interest_ratio*100:.0f}% of principal)")
        except (ValueError, TypeError):
            pass

    # ─── Final score ─── #
    score = max(0, min(score, 100))

    # Generate rating
    if score >= 85:
        rating = "Excellent"
        summary = "This contract has fair terms and competitive pricing."
    elif score >= 70:
        rating = "Good"
        summary = "This contract is reasonable with minor areas for negotiation."
    elif score >= 55:
        rating = "Fair"
        summary = "This contract has some unfavorable terms. Consider negotiating."
    elif score >= 40:
        rating = "Below Average"
        summary = "Several concerning terms found. Strongly recommend negotiation."
    else:
        rating = "Poor"
        summary = "This contract has multiple unfair terms. Seek better alternatives."

    logger.info("Fairness score: %d (%s) — %d reasons", score, rating, len(reasons))

    return {
        "fairness_score": score,
        "rating": rating,
        "summary": summary,
        "reasons": reasons,
    }