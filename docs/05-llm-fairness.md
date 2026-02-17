# Chapter 5: LLM Integration & Fairness Scoring

[← Previous: PDF & Contract Analysis](04-pdf-contract-analysis.md) | [Back to Contents](../DOCUMENTATION.md) | [Next: VIN & Price →](06-vin-price.md)

---

## 5.1 LLM-Based SLA Extraction

While regex patterns work well for structured text, many contracts use natural language that regex can't parse. The LLM (Large Language Model) handles these cases by **understanding the meaning** of the text.

### How It Works

1. We send the contract text to **Ollama** (running locally)
2. The LLM reads the text and extracts fields as JSON
3. We validate the JSON against our schema
4. Missing fields are set to `None`

### File: `backend/llm_sla_extracter.py`

```python
"""
LLM-based SLA extraction using Ollama (local) via LangChain.
Falls back gracefully if Ollama is not running.
"""

import json
import logging
from backend.sla_schema import SLA_SCHEMA

logger = logging.getLogger(__name__)

# ──────────────── Ollama config ──────────────── #

OLLAMA_MODEL = "qwen3:8b"
OLLAMA_BASE_URL = "http://localhost:11434"

SYSTEM_PROMPT = """You are an AI assistant specialized in analyzing car lease
and car loan contracts.
Extract ONLY the requested fields from the contract text.
Return STRICT JSON only — no explanation, no markdown fences, no extra text.
Do NOT guess missing values. Use null if information is not present.
Be precise with numbers: extract exact values from the contract."""

USER_PROMPT_TEMPLATE = """Extract the following SLA details from this car
lease or loan contract.

Return a JSON object with EXACTLY these keys:
{schema_keys}

Field descriptions:
- contract_type: "Vehicle Lease" or "Car Loan" or null
- interest_rate_apr: Annual percentage rate as a number (e.g. 8.5)
- lease_term_months: Duration in months as integer
- monthly_payment: Amount as number
- down_payment: Amount as number
- residual_value: Vehicle residual value as number
- mileage_allowance: Annual mileage limit as integer
- overage_charge_per_mile: Cost per excess mile as number
- early_termination_clause: Description of early termination terms
- purchase_option_price: Buyout price as number
- maintenance_responsibility: Who is responsible for maintenance
- warranty_coverage: Warranty details
- insurance_requirements: Insurance requirements
- late_payment_penalty: Late fee details
- red_flags: List of concerning terms (as array of strings)
- contract_fairness_score: null (will be calculated separately)

Contract text:
\"\"\"
{contract_text}
\"\"\"
"""
```

### The Extraction Function

```python
def _check_ollama_available() -> bool:
    """Check if Ollama server is reachable."""
    try:
        import requests
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        return resp.status_code == 200
    except Exception:
        return False


def extract_sla_with_llm(contract_text: str) -> dict:
    """
    Extract SLA fields from contract text using Ollama LLM.
    Returns a dict matching SLA_SCHEMA keys, or raises on failure.
    """
    if not _check_ollama_available():
        logger.warning("Ollama not available — skipping LLM extraction")
        raise ConnectionError("Ollama server is not running")

    from langchain_ollama import ChatOllama
    from langchain_core.messages import SystemMessage, HumanMessage

    llm = ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0,       # Deterministic output — no randomness
        num_predict=2048,    # Max tokens in response
    )

    truncated = contract_text[:8000]  # Fit context window

    user_prompt = USER_PROMPT_TEMPLATE.format(
        schema_keys=json.dumps(list(SLA_SCHEMA.keys()), indent=2),
        contract_text=truncated,
    )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]

    response = llm.invoke(messages)
    raw_output = response.content.strip()

    # Strip markdown fences if the model wraps in ```json ... ```
    if raw_output.startswith("```"):
        lines = raw_output.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        raw_output = "\n".join(lines)

    try:
        sla = json.loads(raw_output)
    except json.JSONDecodeError as e:
        logger.error("LLM returned invalid JSON: %s", raw_output[:500])
        raise ValueError(f"LLM returned invalid JSON: {e}")

    # Ensure all schema keys exist
    for key in SLA_SCHEMA:
        sla.setdefault(key, None)

    # Normalize red_flags to always be a list
    if not isinstance(sla.get("red_flags"), list):
        sla["red_flags"] = [] if sla.get("red_flags") is None else [str(sla["red_flags"])]

    return sla
```

### Key Design Decisions

| Decision | Reasoning |
|----------|-----------|
| `temperature=0` | We want consistent, predictable extraction — not creative writing |
| `num_predict=2048` | JSON output needs enough tokens; too low and it gets cut off |
| `contract_text[:8000]` | LLMs have limited context windows; most key terms are in the first pages |
| Markdown fence stripping | Many LLMs wrap JSON in ```json ... ``` despite instructions not to |
| Graceful fallback | If Ollama isn't running, we raise `ConnectionError` and the caller uses regex-only results |

---

## 5.2 Fairness Scoring Engine

The fairness engine evaluates a contract across **6 dimensions**, each contributing to a score out of 100.

### File: `backend/fairness_engine.py`

```python
"""
Fairness scoring engine for car lease/loan contracts.

Takes extracted SLA data and optionally a price comparison,
and produces a fairness score (0–100) with detailed reasons.

Scoring Dimensions:
  1. Interest Rate / APR        → up to -30 points
  2. Early Termination Penalties → up to -20 points
  3. Fees (documentation, etc.) → up to -15 points
  4. Red Flags                  → up to -15 points
  5. Price vs Market Comparison → up to -20 / +5 points
  6. Payment Burden (interest)  → up to -10 points
"""


def calculate_fairness_score(sla: dict, price_comparison: dict = None) -> dict:
    score = 100
    reasons = []

    # ────── 1. APR Scoring ────── #
    apr = sla.get("apr_percent") or sla.get("interest_rate_apr")
    if apr:
        try:
            apr_val = float(apr)
            if apr_val > 20:        # Extremely high
                score -= 30
                reasons.append(f"Very high interest rate: {apr_val}%")
            elif apr_val > 15:      # High
                score -= 25
                reasons.append(f"High interest rate: {apr_val}%")
            elif apr_val > 10:      # Above average
                score -= 15
                reasons.append(f"Above-average interest rate: {apr_val}%")
            elif apr_val > 7:       # Slightly elevated
                score -= 5
                reasons.append(f"Slightly elevated interest rate: {apr_val}%")
            # 0-7% = no penalty (market rate)
        except (ValueError, TypeError):
            pass
```

**Why these thresholds?** According to Experian's State of the Auto Finance Market report:
- Average new car loan APR: 5.2% – 7.0%
- Average used car loan APR: 7.0% – 10.5%
- Subprime borrowers: 10% – 20%+

So we penalize anything above 7% (slightly) and escalate penalties as rates increase.

```python
    # ────── 2. Early Termination ────── #
    penalties = sla.get("penalties", {})
    early_term = penalties.get("early_termination")
    if early_term and early_term not in [None, "No penalty", "Not specified"]:
        try:
            et_val = float(early_term)
            if et_val > 5000:
                score -= 20
                reasons.append(f"Severe early termination penalty: ${et_val}")
            elif et_val > 1000:
                score -= 10
                reasons.append(f"Moderate early termination penalty: ${et_val}")
        except (ValueError, TypeError):
            score -= 5
            reasons.append("Early termination clause detected")

    # ────── 3. Fees ────── #
    fees = sla.get("fees", {})
    for fee_name, fee_val in fees.items():
        if fee_val:
            try:
                fv = float(fee_val)
                if fv > 5000:
                    score -= 15
                    reasons.append(f"Excessive {fee_name}: ${fv}")
                elif fv > 2000:
                    score -= 8
                    reasons.append(f"High {fee_name}: ${fv}")
                elif fv > 1000:
                    score -= 3
                    reasons.append(f"Elevated {fee_name}: ${fv}")
            except (ValueError, TypeError):
                pass

    # ────── 4. Red Flags ────── #
    red_flags = sla.get("red_flags", [])
    if red_flags:
        flag_penalty = min(len(red_flags) * 5, 15)  # Cap at 15
        score -= flag_penalty
        reasons.append(f"{len(red_flags)} red flag(s) detected")
    else:
        score += 5  # Bonus for clean contract
        reasons.append("No red flags detected (bonus)")

    # ────── 5. Price Comparison ────── #
    if price_comparison and price_comparison.get("comparison_available"):
        diff_pct = price_comparison.get("diff_percent", 0)
        if diff_pct > 15:       # >15% overpriced
            score -= 20
            reasons.append(f"Vehicle overpriced by {diff_pct:.0f}%")
        elif diff_pct > 5:      # 5-15% overpriced
            score -= 10
            reasons.append(f"Vehicle slightly overpriced by {diff_pct:.0f}%")
        elif diff_pct < -5:     # Good deal!
            score += 5
            reasons.append("Vehicle priced below market value")

    # ────── 6. Payment Burden ────── #
    monthly = sla.get("monthly_payment")
    finance = sla.get("finance_amount")
    term = sla.get("term_months")
    if monthly and finance and term:
        try:
            total_paid = float(monthly) * int(term)
            interest_ratio = (total_paid - float(finance)) / float(finance)
            if interest_ratio > 0.5:    # Paying >50% extra in interest
                score -= 10
                reasons.append(f"High total interest burden: {interest_ratio:.0%} of principal")
        except (ValueError, TypeError, ZeroDivisionError):
            pass

    # ────── Final Score & Rating ────── #
    score = max(0, min(score, 100))   # Clamp to 0–100

    if score >= 85:
        rating, summary = "Excellent", "This contract has very fair terms."
    elif score >= 70:
        rating, summary = "Good", "Generally fair with minor concerns."
    elif score >= 55:
        rating, summary = "Fair", "Several terms could be improved."
    elif score >= 40:
        rating, summary = "Below Average", "Significant concerns identified."
    else:
        rating, summary = "Poor", "This contract has many unfavorable terms."

    return {
        "fairness_score": score,
        "rating": rating,
        "summary": summary,
        "reasons": reasons,
    }
```

### How the Score Flows

```
Start: 100 points
  └─ APR 12%?        → -15   (85 remaining)
  └─ Early term $3000 → -10  (75 remaining)
  └─ Doc fee $800    →  -0   (75 remaining, under threshold)
  └─ 2 red flags     → -10   (65 remaining)
  └─ No price comp   →  +0   (65 remaining)
  └─ No burden issue  →  +0  (65 remaining)
  Final: 65/100 = "Fair" rating
```

---

## 5.3 Verification

```bash
python -c "
from backend.fairness_engine import calculate_fairness_score

# Test 1: Perfect contract
result = calculate_fairness_score({'apr_percent': 5.0})
print(f'Perfect: {result[\"fairness_score\"]}/100 ({result[\"rating\"]})')

# Test 2: Bad contract
result = calculate_fairness_score({
    'apr_percent': 22.0,
    'fees': {'documentation_fee': 6000},
    'red_flags': ['High APR', 'Excessive fees', 'Hidden clauses']
})
print(f'Bad: {result[\"fairness_score\"]}/100 ({result[\"rating\"]})')
print(f'Reasons: {result[\"reasons\"]}')
"
```

---

[← Previous: PDF & Contract Analysis](04-pdf-contract-analysis.md) | [Back to Contents](../DOCUMENTATION.md) | [Next: VIN & Price →](06-vin-price.md)
