# Chapter 7: Negotiation Chatbot

[← Previous: VIN & Price](06-vin-price.md) | [Back to Contents](../DOCUMENTATION.md) | [Next: FastAPI Backend →](08-fastapi-backend.md)

---

## 7.1 Overview

The negotiation assistant has **three components**:

1. **Rule-based negotiation point generator** — Analyzes SLA + fairness data to create structured suggestions
2. **LLM-powered conversational chatbot** — Multi-turn chat with contract context
3. **Email generator** — Creates professional negotiation letters

---

## 7.2 Rule-Based Negotiation Points

Before involving the LLM, we generate initial negotiation suggestions based on the extracted contract data. This ensures the user always gets actionable advice, even if Ollama is offline.

### File: `backend/negotiation_assistant.py`

```python
def generate_negotiation_points(sla: dict, fairness: dict) -> list:
    """
    Generate negotiation suggestions based on extracted SLA and fairness data.
    Returns a list of dicts with: category, severity, point, strategy.
    """
    points = []

    # 1. Interest rate negotiation
    apr = sla.get("apr_percent") or sla.get("interest_rate_apr")
    if apr:
        try:
            apr_val = float(apr)
            if apr_val > 15:
                points.append({
                    "category": "interest_rate",
                    "severity": "high",
                    "point": f"Interest rate of {apr_val}% is very high.",
                    "strategy": "Present competing offers from other lenders."
                })
            elif apr_val > 8:
                points.append({
                    "category": "interest_rate",
                    "severity": "medium",
                    "point": f"Interest rate of {apr_val}% is above average.",
                    "strategy": "Get pre-approved at a credit union first."
                })
        except (ValueError, TypeError):
            pass

    # 2. Fee negotiation
    fees = sla.get("fees", {})
    for fee_name, fee_val in fees.items():
        if fee_val:
            try:
                fv = float(fee_val)
                if fv > 3000:
                    points.append({
                        "category": "fees",
                        "severity": "medium",
                        "point": f"{fee_name.replace('_', ' ').title()} of ${fv:,.0f} is negotiable.",
                        "strategy": "Ask for 50% reduction or full waiver."
                    })
            except (ValueError, TypeError):
                pass

    # 3. Early termination  |  4. Mileage overage  |  5. Down payment
    # ... (similar pattern for each category)

    # 6. Overall fairness assessment
    score = fairness.get("fairness_score", 100)
    if score < 50:
        points.append({
            "category": "overall",
            "severity": "high",
            "point": "This contract scores poorly. Consider walking away.",
            "strategy": "Get 2-3 competing offers first."
        })

    if not points:
        points.append({
            "category": "overall",
            "severity": "low",
            "point": "This contract appears fair.",
            "strategy": "Even fair contracts have room — ask for small concessions."
        })

    return points
```

### Output Example

```json
[
  {
    "category": "interest_rate",
    "severity": "high",
    "point": "Interest rate of 18.9% is very high.",
    "strategy": "Present competing offers from other lenders."
  },
  {
    "category": "fees",
    "severity": "medium",
    "point": "Documentation Fee of $5,000 is negotiable.",
    "strategy": "Ask for 50% reduction or full waiver."
  },
  {
    "category": "overall",
    "severity": "high",
    "point": "This contract scores poorly. Consider walking away.",
    "strategy": "Get 2-3 competing offers first."
  }
]
```

---

## 7.3 LLM-Powered Chatbot

The chatbot uses Ollama to have context-aware conversations about the user's specific contract.

### System Prompt

```python
NEGOTIATION_SYSTEM_PROMPT = """You are an expert car lease and loan
negotiation advisor.

GUIDELINES:
- Be professional, concise, and supportive
- Provide specific, actionable negotiation advice
- Reference the contract details provided in the context
- Suggest specific talking points, counter-offers, and strategies
- Keep responses focused (3-5 key points max)
- Never give legal advice — recommend consulting a lawyer

TONE: Friendly, knowledgeable, empowering — like a trusted advisor."""
```

### Context Builder

Before each chat, we build a summary of the contract for the LLM:

```python
def _build_context_summary(context: dict) -> str:
    """Build a human-readable contract context summary for the LLM."""
    parts = []
    sla = context.get("sla", {})
    fairness = context.get("fairness", {})

    contract_type = sla.get("contract_type") or sla.get("loan_type") or "Unknown"
    parts.append(f"Contract Type: {contract_type}")

    apr = sla.get("apr_percent") or sla.get("interest_rate_apr")
    if apr:
        parts.append(f"Interest Rate (APR): {apr}%")

    monthly = sla.get("monthly_payment")
    if monthly:
        parts.append(f"Monthly Payment: ${monthly:,}")

    # ... fees, penalties, red flags, fairness score ...

    score = fairness.get("fairness_score")
    if score is not None:
        parts.append(f"Fairness Score: {score}/100")

    return "\n".join(parts)
```

### Chat Function

```python
def chat_with_negotiator(user_message, context=None, chat_history=None):
    """
    Send a message to the negotiation chatbot.
    Falls back to rule-based responses if Ollama is unavailable.
    """
    if not _check_ollama():
        return _rule_based_response(user_message, context)

    from langchain_ollama import ChatOllama
    from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

    llm = ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0.7,     # Slightly creative for conversational responses
        num_predict=1024,
    )

    messages = [SystemMessage(content=NEGOTIATION_SYSTEM_PROMPT)]

    # Add contract context
    if context:
        context_text = _build_context_summary(context)
        messages.append(SystemMessage(
            content=f"CONTRACT ANALYSIS CONTEXT:\n{context_text}"
        ))

    # Add chat history (last 10 messages for context window)
    if chat_history:
        for msg in chat_history[-10:]:
            if msg.get("role") == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg.get("role") == "assistant":
                messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=user_message))

    try:
        response = llm.invoke(messages)
        content = response.content.strip()

        # Strip thinking tags (qwen3 sometimes adds <think>...</think>)
        if "<think>" in content:
            import re
            content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()

        return content
    except Exception as e:
        return _rule_based_response(user_message, context)
```

### Rule-Based Fallback

When Ollama is offline, keyword matching provides basic responses:

```python
def _rule_based_response(user_message: str, context: dict = None) -> str:
    msg_lower = user_message.lower()

    if any(kw in msg_lower for kw in ["interest", "rate", "apr"]):
        apr = context.get("sla", {}).get("apr_percent")
        if apr:
            return (f"Your contract has an interest rate of {apr}%. "
                    f"Current market rates are typically 4-8%. "
                    f"Get pre-approved at a credit union for leverage.")

    if any(kw in msg_lower for kw in ["fee", "charge"]):
        # ... fee-specific advice ...

    if any(kw in msg_lower for kw in ["walk away", "cancel"]):
        # ... early termination advice ...

    # Default response
    return f"Based on your contract (score: {score}/100), focus on the highest-impact areas first."
```

---

## 7.4 Email Generation

The system can draft professional negotiation emails:

```python
def generate_negotiation_email(context, specific_requests=None, tone="professional"):
    """Generate a professional negotiation email based on contract analysis."""
    if not _check_ollama():
        return _rule_based_email(context, specific_requests)

    from langchain_ollama import ChatOllama
    from langchain_core.messages import SystemMessage, HumanMessage

    llm = ChatOllama(model=OLLAMA_MODEL, temperature=0.5, num_predict=2048)

    context_text = _build_context_summary(context)

    prompt = f"""Based on the following contract analysis, draft a {tone}
negotiation email to the dealer requesting better terms.

CONTRACT DETAILS:
{context_text}

The email should:
1. Open professionally
2. Reference specific contract terms
3. Include concrete counter-proposals
4. Mention market data as leverage
5. Close with a clear call to action
6. Be about 200-300 words"""

    messages = [
        SystemMessage(content=EMAIL_SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ]
    response = llm.invoke(messages)
    return response.content.strip()
```

### Fallback Email Template

```python
def _rule_based_email(context, specific_requests=None):
    """Template-based email when LLM is unavailable."""
    sla = context.get("sla", {})
    apr = sla.get("apr_percent") or "N/A"
    monthly = sla.get("monthly_payment") or "N/A"

    return f"""Dear Dealer/Financing Team,

Thank you for providing the financing proposal for my vehicle purchase.
After careful review, I would like to discuss some terms:

1. Interest Rate: The current APR of {apr}% appears above market rates.
   I have received competitive offers in the 4-7% range.

2. Fees: I would like to discuss reducing or waiving certain fees.

3. Monthly Payment: The current payment of {monthly} could be adjusted.

I am genuinely interested in completing this transaction and believe
we can reach terms that work for both parties.

Best regards,
[Your Name]"""
```

---

## 7.5 Multi-Turn Chat Architecture

The chat system uses a **thread-based** model:

```
User starts negotiation → Thread created (with contract context)
  └─ User sends message #1 → Saved to DB → LLM responds → Saved to DB
  └─ User sends message #2 → Load history → LLM sees full context → Responds
  └─ User sends message #N → Load last 10 msgs → LLM responds
```

Each thread stores:
- `contract_id` — which contract this negotiation is about
- `context_json` — the full SLA + fairness data (loaded once at thread creation)
- Messages are stored individually with `role` (user/assistant) and timestamps

---

## 7.6 Verification

```bash
python -c "
from backend.negotiation_assistant import generate_negotiation_points

# Test with a bad contract
points = generate_negotiation_points(
    sla={'apr_percent': 18.0, 'fees': {'documentation_fee': 5000}},
    fairness={'fairness_score': 35}
)
for p in points:
    print(f'[{p[\"severity\"].upper()}] {p[\"point\"]}')
    print(f'  Strategy: {p[\"strategy\"]}')
"
```

---

[← Previous: VIN & Price](06-vin-price.md) | [Back to Contents](../DOCUMENTATION.md) | [Next: FastAPI Backend →](08-fastapi-backend.md)
