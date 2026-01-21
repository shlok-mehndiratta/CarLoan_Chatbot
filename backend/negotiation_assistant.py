def generate_negotiation_points(sla: dict, fairness: dict) -> list:
    """
    Generate negotiation suggestions based on SLA and fairness score.
    """

    points = []

    # Interest rate negotiation
    apr = sla.get("apr_percent")
    if apr and apr > 12:
        points.append(
            "Ask the dealer or bank if the interest rate can be reduced to current market rates."
        )

    # Documentation fee
    fees = sla.get("fees", {})
    if fees.get("documentation_fee"):
        points.append(
            "Request reduction or waiver of the documentation fee."
        )

    # Early termination penalty
    penalties = sla.get("penalties", {})
    if penalties.get("early_termination") not in ["No penalty", "Not specified"]:
        points.append(
            "Negotiate early termination charges or request flexibility."
        )

    # Overall fairness check
    score = fairness.get("fairness_score", 100)
    if score < 70:
        points.append(
            "Ask the dealer to justify pricing and offer better overall terms."
        )

    if not points:
        points.append(
            "This contract appears fair, but you may still ask for small concessions."
        )

    return points