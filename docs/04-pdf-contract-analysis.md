# Chapter 4: PDF Processing & Contract Analysis

[← Previous: Architecture](03-project-architecture.md) | [Back to Contents](../DOCUMENTATION.md) | [Next: LLM & Fairness →](05-llm-fairness.md)

---

## 4.1 Overview

This chapter covers the first two steps of the analysis pipeline:
1. **Extracting text** from a PDF file (digital or scanned)
2. **Analyzing the text** with regular expressions to extract financial data

---

## 4.2 PDF Text Extraction

### The Problem

Car contracts come in two forms:
- **Digital PDFs** — created by software, text is selectable (copy-pasteable)
- **Scanned PDFs** — photographs or scans of paper documents, text is embedded in images

Our system needs to handle both. We use a **fallback strategy**:

1. **Try digital extraction first** (fast, accurate) using `pdfminer`
2. **If that fails, fall back to OCR** (slower, but handles scans) using `pytesseract`

### File: `backend/pdf_reader.py`

```python
from pdfminer.high_level import extract_text
from pdf2image import convert_from_bytes
import pytesseract
import io
import os

TESSERACT_PATH = os.getenv("TESSERACT_PATH")
if TESSERACT_PATH:
    pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

MAX_PAGES = 5


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    # Strategy 1: Try digital PDF extraction (pdfminer)
    try:
        text = extract_text(io.BytesIO(pdf_bytes))
        if text and text.strip():
            return text
    except Exception:
        pass

    # Strategy 2: Fall back to OCR (for scanned documents)
    try:
        images = convert_from_bytes(
            pdf_bytes,
            dpi=300,          # High DPI = better OCR accuracy
            first_page=1,
            last_page=MAX_PAGES  # Limit to prevent memory issues
        )
        ocr_text = ""
        for img in images:
            ocr_text += pytesseract.image_to_string(img)

        ocr_text = ocr_text.replace("\n", " ")
        return " ".join(ocr_text.split())  # Collapse whitespace

    except Exception:
        return ""
```

### Line-by-Line Explanation

| Line | What It Does | Why |
|------|-------------|-----|
| `extract_text(io.BytesIO(pdf_bytes))` | pdfminer reads PDF text directly | Fast and accurate for digital PDFs |
| `if text and text.strip()` | Checks if we got actual text | Scanned PDFs return empty strings |
| `convert_from_bytes(pdf_bytes, dpi=300)` | Converts each PDF page to a 300 DPI image | Higher DPI = better OCR quality |
| `MAX_PAGES = 5` | Only process first 5 pages | Most contracts have key terms in first pages; prevents memory issues |
| `pytesseract.image_to_string(img)` | Tesseract reads text from the image | This is OCR — Optical Character Recognition |
| `" ".join(ocr_text.split())` | Collapses all whitespace to single spaces | OCR output often has irregular spacing |

---

## 4.3 Contract Analyzer — Rule-Based Extraction

This is the core of the analysis system. It uses **regular expressions (regex)** to find financial information in the contract text.

### What Are Regular Expressions?

Regular expressions are pattern-matching tools. Instead of searching for an exact word, you search for a **pattern**. For example:

| Pattern | What It Matches | Example Match |
|---------|----------------|---------------|
| `\d+` | One or more digits | "123", "45" |
| `\d+\.\d+%` | A decimal percentage | "8.5%", "12.99%" |
| `\$[\d,]+\.?\d*` | A dollar amount | "$25,000", "$499.99" |
| `(lease\|loan)` | Either "lease" or "loan" | "lease", "loan" |

### File: `backend/contract_analyzer.py`

```python
"""
Rule-based SLA extraction from car lease / loan contracts.

Uses regex patterns to extract financial terms:
  - Interest rate / APR
  - Monthly payment, down payment, finance amount
  - Fees (documentation, processing, acquisition)
  - Penalties (early termination, late payment, over-mileage)
  - Lease-specific: residual value, mileage allowance, buyout option
"""

import re
from datetime import datetime

# ──────────────── Helper Functions ──────────────── #

def clean_text(text: str) -> str:
    """Normalize contract text for consistent parsing."""
    text = text.replace(",", "")    # Remove commas from numbers: 25,000 → 25000
    text = re.sub(r"\s+", " ", text)  # Collapse multiple spaces into one
    return text.strip()


def extract_amount(text: str, *patterns) -> float | None:
    """
    Try multiple regex patterns to find a dollar amount.
    Returns the first match found, or None.
    
    Example:
        extract_amount(text, r"monthly payment.*?\$?([\d.]+)")
        → 499.99
    """
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except (ValueError, IndexError):
                pass
    return None


def calculate_term_from_dates(text: str) -> int | None:
    """
    If start and end dates are mentioned, calculate term in months.
    
    Example: "from 01/15/2024 to 01/15/2027" → 36 months
    """
    date_pattern = r"(\d{1,2}/\d{1,2}/\d{4})"
    dates = re.findall(date_pattern, text)
    if len(dates) >= 2:
        try:
            d1 = datetime.strptime(dates[0], "%m/%d/%Y")
            d2 = datetime.strptime(dates[1], "%m/%d/%Y")
            months = (d2.year - d1.year) * 12 + (d2.month - d1.month)
            if months > 0:
                return months
        except ValueError:
            pass
    return None
```

### The Main Analysis Function

This is the heart of the system — it takes raw contract text and returns structured data:

```python
def analyze_contract(contract_text: str) -> dict:
    """
    Analyze contract text and extract all SLA fields.
    
    Returns a dict with keys like:
      loan_type, apr_percent, monthly_payment, term_months,
      fees, penalties, red_flags, negotiation_points, etc.
    """
    if not contract_text or len(contract_text.strip()) < 50:
        raise ValueError("Contract text is too short to analyze")

    text = clean_text(contract_text)
    lower = text.lower()

    # ── Contract Type Detection ──
    # Count occurrences of "lease" vs "loan" to determine type
    lease_count = lower.count("lease")
    loan_count = lower.count("loan") + lower.count("finance")
    loan_type = "Vehicle Lease" if lease_count > loan_count else "Car Loan"

    # ── Interest Rate / APR ──
    # Try multiple patterns because contracts write APR differently
    apr = extract_amount(text,
        r"(?:APR|annual percentage rate)\s*(?:of|is|:)?\s*(\d+\.?\d*)%",
        r"(\d+\.?\d*)%\s*(?:APR|annual percentage rate)",
        r"interest rate\s*(?:of|is|:)?\s*(\d+\.?\d*)%",
    )

    # ── Monthly Payment ──
    monthly = extract_amount(text,
        r"monthly payment\s*(?:of|is|:)?\s*\$?([\d.]+)",
        r"\$?([\d.]+)\s*per month",
        r"monthly\s*(?:installment|amount)\s*(?:of|is|:)?\s*\$?([\d.]+)",
    )

    # ── Term ──
    term = extract_amount(text,
        r"(?:term|duration|period)\s*(?:of|is|:)?\s*(\d+)\s*months",
        r"(\d+)\s*month\s*(?:term|lease|loan)",
    )
    if term:
        term = int(term)
    else:
        term = calculate_term_from_dates(text)

    # ── Down Payment ──
    down = extract_amount(text,
        r"down payment\s*(?:of|is|:)?\s*\$?([\d.]+)",
        r"initial payment\s*(?:of|is|:)?\s*\$?([\d.]+)",
    )

    # ── Finance Amount ──
    finance = extract_amount(text,
        r"(?:finance|financed|total)\s*amount\s*(?:of|is|:)?\s*\$?([\d.]+)",
        r"amount financed\s*(?:of|is|:)?\s*\$?([\d.]+)",
    )

    # ── Fees ──
    fees = {
        "documentation_fee": extract_amount(text, r"doc(?:umentation)?\s*fee\s*(?:of|:)?\s*\$?([\d.]+)"),
        "processing_fee": extract_amount(text, r"processing\s*fee\s*(?:of|:)?\s*\$?([\d.]+)"),
        "acquisition_fee": extract_amount(text, r"acquisition\s*fee\s*(?:of|:)?\s*\$?([\d.]+)"),
        "disposition_fee": extract_amount(text, r"disposition\s*fee\s*(?:of|:)?\s*\$?([\d.]+)"),
    }

    # ── Penalties ──
    early_term = None
    early_match = re.search(
        r"early\s*termination.*?(?:penalty|fee|charge).*?(?:of|is|:)?\s*\$?([\d.]+)",
        text, re.IGNORECASE
    )
    if early_match:
        early_term = early_match.group(1)
    elif "early termination" in lower:
        # Even if we can't find the exact amount, note that it exists
        early_term = "See contract for details"

    penalties = {
        "early_termination": early_term,
        "late_payment": extract_amount(text, r"late\s*(?:payment)?\s*(?:fee|penalty|charge)\s*(?:of|:)?\s*\$?([\d.]+)"),
        "over_mileage": extract_amount(text, r"(?:excess|over)\s*mileage.*?\$?([\d.]+)\s*(?:per|/)\s*mile"),
    }

    # ── Red Flags ──
    red_flags = []
    if apr and apr > 15:
        red_flags.append(f"High interest rate: {apr}% (typical: 4-8%)")
    if fees.get("documentation_fee") and fees["documentation_fee"] > 1000:
        red_flags.append(f"High documentation fee: ${fees['documentation_fee']}")
    if early_term and early_term not in ["Not specified", None]:
        red_flags.append("Early termination penalty present")

    # ── Build Result ──
    return {
        "loan_type": loan_type,
        "apr_percent": apr,
        "monthly_payment": monthly,
        "term_months": term,
        "down_payment": down,
        "finance_amount": finance,
        "residual_value": extract_amount(text, r"residual value\s*(?:of|is|:)?\s*\$?([\d.]+)"),
        "mileage_allowance": extract_amount(text, r"mileage\s*(?:allowance|limit)\s*(?:of|is|:)?\s*(\d+)"),
        "overage_charge_per_mile": penalties.get("over_mileage"),
        "fees": {k: v for k, v in fees.items() if v},
        "penalties": {k: v for k, v in penalties.items() if v},
        "red_flags": red_flags,
        "negotiation_points": [],
    }
```

### The Merge Function

This function combines rule-based and LLM extraction results:

```python
def merge_rule_and_llm(rule_sla: dict, llm_sla: dict) -> dict:
    """
    Merge rule-based and LLM extractions.
    Strategy: Rule-based values take priority (more precise),
              LLM fills in any gaps where rules found nothing.
    
    Example:
        rule_sla = {"apr_percent": 8.5, "monthly_payment": None}
        llm_sla  = {"apr_percent": 8.0, "monthly_payment": 499.99}
        result   = {"apr_percent": 8.5, "monthly_payment": 499.99}
    """
    merged = dict(rule_sla)   # Start with all rule-based values

    for key, llm_val in llm_sla.items():
        rule_val = merged.get(key)

        # If rule-based found nothing, use LLM's value
        if rule_val is None and llm_val is not None:
            merged[key] = llm_val
        elif isinstance(rule_val, list) and len(rule_val) == 0 and isinstance(llm_val, list):
            merged[key] = llm_val                          # Empty list → use LLM's
        elif isinstance(rule_val, dict) and len(rule_val) == 0 and isinstance(llm_val, dict):
            merged[key] = llm_val                          # Empty dict → use LLM's

    return merged
```

### Why Two Extraction Systems?

| Approach | Strengths | Weaknesses |
|----------|-----------|------------|
| **Regex (rule-based)** | Exact number extraction, fast, predictable | Can't handle unusual phrasing |
| **LLM** | Understands natural language, handles variations | May hallucinate numbers, slower |
| **Merged** | Best of both worlds | More complex code |

**Example:** A contract says "The annual rate of interest applicable to this agreement shall be set at eight point five percent."
- Regex would **miss** this (it's written as words, not "8.5%")
- The LLM would correctly extract `interest_rate_apr: 8.5`
- After merging, we get the correct value

---

## 4.4 Verification

```bash
# Test that imports work
python -c "
from backend.contract_analyzer import analyze_contract, clean_text, extract_amount
print('✅ Contract analyzer imports OK')

# Test clean_text
assert clean_text('  hello   world  ') == 'hello world'
print('✅ clean_text works')

# Test extract_amount
assert extract_amount('APR is 8.5%', r'(\d+\.?\d*)%') == 8.5
print('✅ extract_amount works')

# Test analyze_contract
result = analyze_contract('This is a car loan with an APR of 9.5% and monthly payment of \$450 for 60 months term.')
assert result['apr_percent'] == 9.5
assert result['monthly_payment'] == 450.0
print(f'✅ analyze_contract: APR={result[\"apr_percent\"]}%, Monthly=\${result[\"monthly_payment\"]}')
"
```

---

[← Previous: Architecture](03-project-architecture.md) | [Back to Contents](../DOCUMENTATION.md) | [Next: LLM & Fairness →](05-llm-fairness.md)
