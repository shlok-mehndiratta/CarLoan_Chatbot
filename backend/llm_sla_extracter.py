
import os
import openai
import json
from backend.sla_schema import SLA_SCHEMA

openai.api_key = os.getenv("OPENAI_API_KEY")

SYSTEM_PROMPT = """
You are an AI assistant specialized in analyzing car lease and car loan contracts.
Extract ONLY the requested fields.
Return STRICT JSON only.
Do NOT explain.
Do NOT guess missing values.
Use null if information is not present.
"""

def extract_sla_with_llm(contract_text: str) -> dict:
    user_prompt = f"""
Extract the following SLA details from this car lease or loan contract.

Return JSON with these keys ONLY:
{list(SLA_SCHEMA.keys())}

Contract text:
\"\"\"
{contract_text[:6000]}
\"\"\"
"""

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0
    )

    raw_output = response.choices[0].message["content"]

    try:
        sla = json.loads(raw_output)
    except Exception:
        raise ValueError("LLM returned invalid JSON")

    # Ensure schema completeness
    for key in SLA_SCHEMA:
        sla.setdefault(key, None)

    return sla