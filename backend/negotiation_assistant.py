"""
Negotiation Assistant — AI-powered car lease/loan negotiation chatbot.

Features:
  1. Rule-based negotiation point generation (from SLA + fairness data)
  2. LLM-powered conversational chatbot (Ollama qwen3:8b)
  3. Context-aware responses using contract analysis as context
  4. Multi-turn chat with history persistence
  5. Negotiation email/letter generation
  6. Strategy suggestions based on contract weaknesses
"""

import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ──────────────────── Ollama Config ──────────────────── #

OLLAMA_MODEL = "qwen3:8b"
OLLAMA_BASE_URL = "http://localhost:11434"

# ──────────────────── System Prompts ──────────────────── #

NEGOTIATION_SYSTEM_PROMPT = """You are an expert car lease and loan negotiation advisor. 
Your role is to help consumers negotiate better terms on their car financing contracts.

GUIDELINES:
- Be professional, concise, and supportive
- Provide specific, actionable negotiation advice
- Reference the contract details provided in the context
- Suggest specific talking points, counter-offers, and strategies
- Explain WHY certain terms are unfavorable when applicable
- Keep responses focused and practical (3-5 key points max)
- If the user asks about something not related to car financing, politely redirect
- Use bullet points for actionable advice
- Never give legal advice — recommend consulting a lawyer for legal matters
- Do NOT wrap your response in markdown fences or JSON

TONE: Friendly, knowledgeable, empowering — like a trusted advisor helping a friend."""

EMAIL_SYSTEM_PROMPT = """You are an expert at drafting professional negotiation communications 
for car lease and loan contracts.

GUIDELINES:
- Write clear, professional, and assertive (not aggressive) emails/letters
- Reference specific contract terms and market data
- Include specific counter-proposals with justification
- Maintain a respectful and collaborative tone
- Structure with: greeting, context, specific requests, supporting evidence, closing
- Keep the email concise but comprehensive
- Do NOT wrap your response in markdown fences"""


# ──────────────────── Rule-Based Points ──────────────────── #

def generate_negotiation_points(sla: dict, fairness: dict) -> list:
    """
    Generate negotiation suggestions based on extracted SLA and fairness data.
    This is the rule-based component that feeds into the chatbot context.
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
                    "point": f"Interest rate of {apr_val}% is very high. Request reduction to market rate (typically 4-8% for good credit).",
                    "strategy": "Present competing offers from other lenders. Mention your credit score if strong."
                })
            elif apr_val > 8:
                points.append({
                    "category": "interest_rate",
                    "severity": "medium",
                    "point": f"Interest rate of {apr_val}% is above average. Ask for a rate match or reduction.",
                    "strategy": "Get pre-approved at a credit union first, then use that as leverage."
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
                        "point": f"{fee_name.replace('_', ' ').title()} of ₹{fv:,.0f} is negotiable.",
                        "strategy": "Many fees are profit centers for dealers. Ask for 50% reduction or full waiver."
                    })
            except (ValueError, TypeError):
                pass

    # 3. Early termination
    penalties = sla.get("penalties", {})
    early_term = penalties.get("early_termination")
    if early_term and early_term not in [None, "No penalty", "Not specified"]:
        points.append({
            "category": "early_termination",
            "severity": "medium",
            "point": "Early termination penalty detected. Negotiate flexibility.",
            "strategy": "Ask for a graduated penalty that decreases over time, or a penalty-free window."
        })

    # 4. Mileage overage
    overage = sla.get("overage_charge_per_mile") or penalties.get("over_mileage")
    if overage:
        try:
            ov = float(overage)
            if ov > 0.20:
                points.append({
                    "category": "mileage",
                    "severity": "medium",
                    "point": f"Mileage overage charge of ${ov:.2f}/mile is high (typical: $0.10-$0.20).",
                    "strategy": "Negotiate a higher mileage allowance upfront — it's cheaper than overage charges."
                })
        except (ValueError, TypeError):
            pass

    # 5. Down payment
    down = sla.get("down_payment")
    finance = sla.get("finance_amount")
    if down and finance:
        try:
            down_val = float(down)
            fin_val = float(finance)
            if fin_val > 0:
                down_pct = (down_val / (down_val + fin_val)) * 100
                if down_pct > 25:
                    points.append({
                        "category": "down_payment",
                        "severity": "low",
                        "point": f"Down payment of {down_pct:.0f}% is high. Consider negotiating vehicle price instead.",
                        "strategy": "A lower vehicle price saves more long-term than a smaller down payment."
                    })
        except (ValueError, TypeError):
            pass

    # 6. General fairness
    score = fairness.get("fairness_score", 100)
    if score < 50:
        points.append({
            "category": "overall",
            "severity": "high",
            "point": "This contract scores poorly on fairness. Consider walking away or major renegotiation.",
            "strategy": "You have the strongest position when you're willing to walk away. Get 2-3 competing offers."
        })
    elif score < 70:
        points.append({
            "category": "overall",
            "severity": "medium",
            "point": "Several terms could be improved. Negotiate before signing.",
            "strategy": "Focus on the highest-impact items first (interest rate, then fees)."
        })

    if not points:
        points.append({
            "category": "overall",
            "severity": "low",
            "point": "This contract appears fair. You may still ask for small concessions.",
            "strategy": "Even fair contracts have room — ask for floor mats, maintenance package, or small rate reduction."
        })

    return points


# ──────────────────── LLM Chat ──────────────────── #

def _check_ollama() -> bool:
    """Check if Ollama server is accessible."""
    import requests
    try:
        r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def _build_context_summary(context: dict) -> str:
    """Build a human-readable contract context summary for the LLM."""
    parts = []

    sla = context.get("sla", {})
    fairness = context.get("fairness", {})
    price_comp = context.get("price_comparison")
    neg_points = context.get("negotiation_points", [])

    # Contract basics
    contract_type = sla.get("contract_type") or sla.get("loan_type") or "Unknown"
    parts.append(f"Contract Type: {contract_type}")

    apr = sla.get("apr_percent") or sla.get("interest_rate_apr")
    if apr:
        parts.append(f"Interest Rate (APR): {apr}%")

    monthly = sla.get("monthly_payment")
    if monthly:
        parts.append(f"Monthly Payment: ₹{monthly:,}" if isinstance(monthly, (int, float)) else f"Monthly Payment: {monthly}")

    term = sla.get("term_months") or sla.get("lease_term_months")
    if term:
        parts.append(f"Term: {term} months")

    finance = sla.get("finance_amount")
    if finance:
        parts.append(f"Finance Amount: ₹{finance:,}" if isinstance(finance, (int, float)) else f"Finance Amount: {finance}")

    down = sla.get("down_payment")
    if down:
        parts.append(f"Down Payment: {down}")

    # Fees
    fees = sla.get("fees", {})
    fee_parts = []
    for k, v in fees.items():
        if v:
            fee_parts.append(f"  - {k.replace('_', ' ').title()}: {v}")
    if fee_parts:
        parts.append("Fees:\n" + "\n".join(fee_parts))

    # Penalties
    penalties = sla.get("penalties", {})
    pen_parts = []
    for k, v in penalties.items():
        if v and v not in ["Not specified", None]:
            pen_parts.append(f"  - {k.replace('_', ' ').title()}: {v}")
    if pen_parts:
        parts.append("Penalties:\n" + "\n".join(pen_parts))

    # Red flags
    red_flags = sla.get("red_flags", [])
    if red_flags:
        parts.append("Red Flags: " + "; ".join(red_flags))

    # Fairness
    score = fairness.get("fairness_score")
    rating = fairness.get("rating", "")
    if score is not None:
        parts.append(f"Fairness Score: {score}/100 ({rating})")

    # Price comparison
    if price_comp and price_comp.get("comparison_available"):
        parts.append(f"Market Price: {price_comp.get('price_range', 'N/A')}")
        parts.append(f"Price Assessment: {price_comp.get('message', 'N/A')}")

    # Negotiation points
    if neg_points:
        pts_text = []
        for p in neg_points:
            if isinstance(p, dict):
                pts_text.append(f"  - {p.get('point', '')}")
            else:
                pts_text.append(f"  - {p}")
        parts.append("Key Negotiation Points:\n" + "\n".join(pts_text))

    return "\n".join(parts)


def chat_with_negotiator(
    user_message: str,
    context: dict = None,
    chat_history: list = None,
) -> str:
    """
    Send a message to the negotiation chatbot and get a response.

    Args:
        user_message: The user's question or request
        context: Contract analysis context (SLA, fairness, negotiation points)
        chat_history: List of previous messages [{"role": "user"|"assistant", "content": "..."}]

    Returns:
        Assistant's response string
    """
    if not _check_ollama():
        # Fallback to rule-based response
        return _rule_based_response(user_message, context)

    from langchain_ollama import ChatOllama
    from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

    llm = ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0.7,
        num_predict=1024,
    )

    # Build messages
    messages = [SystemMessage(content=NEGOTIATION_SYSTEM_PROMPT)]

    # Add contract context as system context
    if context:
        context_text = _build_context_summary(context)
        messages.append(SystemMessage(
            content=f"CONTRACT ANALYSIS CONTEXT:\n{context_text}\n\nUse this information to provide specific, relevant negotiation advice."
        ))

    # Add chat history
    if chat_history:
        for msg in chat_history[-10:]:  # last 10 messages for context window
            if msg.get("role") == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg.get("role") == "assistant":
                messages.append(AIMessage(content=msg["content"]))

    # Add current user message
    messages.append(HumanMessage(content=user_message))

    try:
        response = llm.invoke(messages)
        content = response.content.strip()

        # Strip thinking tags if present (qwen3 sometimes adds these)
        if "<think>" in content:
            import re
            content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()

        return content

    except Exception as e:
        logger.error("LLM negotiation chat failed: %s", e)
        return _rule_based_response(user_message, context)


def _rule_based_response(user_message: str, context: dict = None) -> str:
    """Fallback rule-based response when LLM is unavailable."""
    msg_lower = user_message.lower()

    if not context:
        return ("I'd be happy to help with your car lease/loan negotiation! "
                "Please start a negotiation session with a contract analysis first, "
                "so I can provide specific advice based on your contract terms.")

    sla = context.get("sla", {})
    fairness = context.get("fairness", {})
    score = fairness.get("fairness_score", 100)

    if any(kw in msg_lower for kw in ["interest", "rate", "apr"]):
        apr = sla.get("apr_percent") or sla.get("interest_rate_apr")
        if apr:
            return (f"Your contract has an interest rate of {apr}%. "
                    f"Current market rates for auto loans are typically 4-8% for good credit. "
                    f"I recommend getting pre-approved at a credit union and using that "
                    f"as leverage to negotiate a lower rate with your dealer.")
        return "I couldn't find the interest rate in your contract. Please check the APR section."

    if any(kw in msg_lower for kw in ["fee", "charge", "documentation", "processing"]):
        fees = sla.get("fees", {})
        fee_list = [f"{k.replace('_', ' ').title()}: {v}" for k, v in fees.items() if v]
        if fee_list:
            return (f"Your contract includes these fees: {', '.join(fee_list)}. "
                    f"Many fees are negotiable — documentation fees and processing fees "
                    f"are common profit centers. Ask for a 50% reduction or full waiver.")
        return "No specific fees were detected in your contract analysis."

    if any(kw in msg_lower for kw in ["email", "letter", "draft", "write"]):
        return ("I can help draft a negotiation email! Use the /negotiate/email endpoint "
                "with your specific requests, and I'll generate a professional letter.")

    if any(kw in msg_lower for kw in ["walk away", "cancel", "terminate", "early"]):
        penalties = sla.get("penalties", {})
        early_term = penalties.get("early_termination")
        if early_term and early_term not in ["Not specified", None]:
            return (f"Your contract has an early termination clause: {early_term}. "
                    f"Try negotiating a graduated penalty or penalty-free window. "
                    f"Remember, your strongest negotiating position is being willing to walk away.")
        return ("No early termination penalty was found. Being willing to walk away "
                "is your strongest negotiation tool.")

    if any(kw in msg_lower for kw in ["fair", "score", "overall", "good deal"]):
        rating = fairness.get("rating", "Unknown")
        reasons = fairness.get("reasons", [])
        reason_text = "; ".join(reasons) if reasons else "No specific issues found"
        return (f"Your contract's fairness score is {score}/100 ({rating}). "
                f"Key factors: {reason_text}. "
                f"{'Consider negotiating the flagged items.' if score < 70 else 'The terms are reasonable.'}")

    # Default response
    return (f"Based on your contract analysis (fairness score: {score}/100), "
            f"I recommend focusing on the highest-impact negotiation areas first. "
            f"Ask me about specific terms like interest rate, fees, or penalties "
            f"for detailed negotiation strategies.")


# ──────────────────── Email Generation ──────────────────── #

def generate_negotiation_email(
    context: dict,
    specific_requests: list = None,
    tone: str = "professional",
) -> str:
    """
    Generate a professional negotiation email/letter based on contract analysis.

    Args:
        context: Contract analysis (SLA, fairness, negotiation points)
        specific_requests: User's specific negotiation requests
        tone: "professional", "assertive", or "friendly"

    Returns:
        Generated email text
    """
    if not _check_ollama():
        return _rule_based_email(context, specific_requests)

    from langchain_ollama import ChatOllama
    from langchain_core.messages import SystemMessage, HumanMessage

    llm = ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0.5,
        num_predict=2048,
    )

    context_text = _build_context_summary(context) if context else "No contract details available."

    requests_text = ""
    if specific_requests:
        requests_text = "\n\nUser's specific requests:\n" + "\n".join(f"- {r}" for r in specific_requests)

    prompt = f"""Based on the following contract analysis, draft a {tone} negotiation email 
to the dealer/lender requesting better terms.

CONTRACT DETAILS:
{context_text}
{requests_text}

The email should:
1. Open professionally with context about the car deal
2. Reference specific contract terms that need improvement
3. Include concrete counter-proposals with justification
4. Mention market data or competing offers as leverage
5. Close with a clear call to action
6. Be well-structured and about 200-300 words

Write ONLY the email text, starting with the greeting. Do not include subject line instructions or meta-commentary."""

    try:
        messages = [
            SystemMessage(content=EMAIL_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]
        response = llm.invoke(messages)
        content = response.content.strip()

        # Strip thinking tags
        if "<think>" in content:
            import re
            content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()

        return content

    except Exception as e:
        logger.error("Email generation failed: %s", e)
        return _rule_based_email(context, specific_requests)


def _rule_based_email(context: dict, specific_requests: list = None) -> str:
    """Fallback rule-based email when LLM is unavailable."""
    sla = context.get("sla", {}) if context else {}
    fairness = context.get("fairness", {}) if context else {}

    apr = sla.get("apr_percent") or sla.get("interest_rate_apr") or "N/A"
    monthly = sla.get("monthly_payment") or "N/A"
    score = fairness.get("fairness_score", "N/A")

    requests_text = ""
    if specific_requests:
        requests_text = "\n\nSpecifically, I would like to discuss:\n" + "\n".join(f"- {r}" for r in specific_requests)

    email = f"""Dear Dealer/Financing Team,

Thank you for providing the financing proposal for my vehicle purchase. After careful review, I would like to discuss some of the terms before proceeding.

Having reviewed the contract and compared it with current market offerings, I have identified several areas where I believe we can reach more competitive terms:

1. Interest Rate: The current APR of {apr}% appears above current market rates. I have received competitive offers in the 4-7% range and would appreciate a rate reduction.

2. Fees: I would like to discuss the possibility of reducing or waiving certain fees included in the agreement.

3. Monthly Payment: The current monthly payment of {monthly} could be adjusted with improvements to the rate and fee structure.
{requests_text}

I am genuinely interested in completing this transaction and believe that with some adjustments, we can reach terms that work for both parties. I would appreciate the opportunity to discuss these points at your earliest convenience.

Thank you for your time and consideration.

Best regards,
[Your Name]"""

    return email