"""
LLM-based SLA extraction using Ollama (local) via LangChain.
Falls back gracefully if Ollama is not running.
"""

import json
import logging
from backend.sla_schema import SLA_SCHEMA

logger = logging.getLogger(__name__)

# ──────────────────── Ollama config ──────────────────── #

OLLAMA_MODEL = "qwen3:8b"
OLLAMA_BASE_URL = "http://localhost:11434"

SYSTEM_PROMPT = """You are an AI assistant specialized in analyzing car lease and car loan contracts.
Extract ONLY the requested fields from the contract text.
Return STRICT JSON only — no explanation, no markdown fences, no extra text.
Do NOT guess missing values. Use null if information is not present.
Be precise with numbers: extract exact values from the contract."""

USER_PROMPT_TEMPLATE = """Extract the following SLA details from this car lease or loan contract.

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
        temperature=0,
        num_predict=2048,
    )

    # Truncate very long contracts to fit context window
    truncated = contract_text[:8000]

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
        # Remove first and last lines (fences)
        lines = [l for l in lines if not l.strip().startswith("```")]
        raw_output = "\n".join(lines)

    try:
        sla = json.loads(raw_output)
    except json.JSONDecodeError as e:
        logger.error("LLM returned invalid JSON: %s", raw_output[:500])
        raise ValueError(f"LLM returned invalid JSON: {e}")

    # Ensure schema completeness
    for key in SLA_SCHEMA:
        sla.setdefault(key, None)

    # Normalize red_flags to always be a list
    if not isinstance(sla.get("red_flags"), list):
        sla["red_flags"] = [] if sla.get("red_flags") is None else [str(sla["red_flags"])]

    logger.info("LLM extraction completed — %d fields populated",
                sum(1 for v in sla.values() if v is not None))

    return sla