"""
Unit tests for backend.contract_analyzer
Tests: clean_text, extract_amount, analyze_contract, merge_rule_and_llm
"""

import pytest
from backend.contract_analyzer import (
    clean_text,
    extract_amount,
    analyze_contract,
    merge_rule_and_llm,
    calculate_term_from_dates,
)


# ──────────── clean_text ──────────── #

class TestCleanText:
    def test_removes_commas(self):
        assert clean_text("1,000,000") == "1000000"

    def test_collapses_whitespace(self):
        assert clean_text("hello   world\n\tnew") == "hello world new"

    def test_strips_whitespace(self):
        assert clean_text("  hello  ") == "hello"

    def test_empty_string(self):
        assert clean_text("") == ""


# ──────────── extract_amount ──────────── #

class TestExtractAmount:
    def test_extracts_float(self):
        result = extract_amount([r"APR.*?(\d+\.?\d*)%"], "APR is 5.9%", float)
        assert result == 5.9

    def test_extracts_integer(self):
        result = extract_amount([r"tenure.*?(\d+)\s*months"], "tenure is 36 months", int)
        assert result == 36

    def test_returns_none_no_match(self):
        result = extract_amount([r"xyz.*?(\d+)"], "no match here", float)
        assert result is None

    def test_first_pattern_wins(self):
        result = extract_amount(
            [r"APR.*?(\d+\.?\d*)%", r"rate.*?(\d+\.?\d*)%"],
            "APR is 3.5%",
            float,
        )
        assert result == 3.5

    def test_fallback_to_second_pattern(self):
        result = extract_amount(
            [r"APR.*?(\d+\.?\d*)%", r"interest.*?(\d+\.?\d*)%"],
            "interest rate 7.2%",
            float,
        )
        assert result == 7.2


# ──────────── calculate_term_from_dates ──────────── #

class TestCalculateTermFromDates:
    def test_valid_dates(self):
        text = "beginning on January 2023 and ending on January 2026"
        assert calculate_term_from_dates(text) == 36

    def test_no_dates(self):
        assert calculate_term_from_dates("no date info here") is None


# ──────────── analyze_contract ──────────── #

class TestAnalyzeContract:
    def test_valid_lease_contract(self, sample_contract_text):
        result = analyze_contract(sample_contract_text)
        assert result["loan_type"] == "Vehicle Lease"
        assert result["apr_percent"] == 5.9
        assert result["term_months"] == 36

    def test_extracts_monthly_payment(self, sample_contract_text):
        result = analyze_contract(sample_contract_text)
        assert result["monthly_payment"] is not None

    def test_extracts_fees(self, sample_contract_text):
        result = analyze_contract(sample_contract_text)
        assert result["fees"]["documentation_fee"] == 500

    def test_extracts_penalties(self, sample_contract_text):
        result = analyze_contract(sample_contract_text)
        assert result["penalties"]["early_termination"] is not None

    def test_too_short_raises(self):
        with pytest.raises(ValueError, match="too short"):
            analyze_contract("short")

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            analyze_contract("")

    def test_loan_type_detection(self):
        loan_text = "Car Loan Agreement. Loan amount $25000. APR 6.5%. tenure is 48 months. Monthly payment $500."
        result = analyze_contract(loan_text)
        assert result["loan_type"] == "Car Loan"

    def test_red_flags_high_apr(self):
        text = "Vehicle Lease agreement. APR is 25%. Lease Term: 36 months. Monthly payment $800."
        result = analyze_contract(text)
        assert "High interest rate" in result["red_flags"]


# ──────────── merge_rule_and_llm ──────────── #

class TestMergeRuleAndLlm:
    def test_llm_fills_gaps(self):
        rule = {"apr_percent": 5.0, "loan_type": None}
        llm = {"apr_percent": 5.5, "loan_type": "Lease"}
        result = merge_rule_and_llm(rule, llm)
        assert result["apr_percent"] == 5.0  # rule wins (non-null)
        assert result["loan_type"] == "Lease"  # llm fills gap

    def test_rule_values_preserved(self):
        rule = {"apr_percent": 5.0, "term_months": 36}
        llm = {"apr_percent": 6.0, "term_months": 48}
        result = merge_rule_and_llm(rule, llm)
        assert result["apr_percent"] == 5.0
        assert result["term_months"] == 36

    def test_empty_list_filled(self):
        rule = {"red_flags": []}
        llm = {"red_flags": ["High APR"]}
        result = merge_rule_and_llm(rule, llm)
        assert result["red_flags"] == ["High APR"]

    def test_empty_llm(self):
        rule = {"apr_percent": 5.0}
        result = merge_rule_and_llm(rule, {})
        assert result["apr_percent"] == 5.0
