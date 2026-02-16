"""
Unit tests for backend.fairness_engine
Tests: scoring dimensions, rating thresholds, edge cases
"""

import pytest
from backend.fairness_engine import calculate_fairness_score


# ──────────── APR Scoring ──────────── #

class TestAPRScoring:
    def test_very_high_apr(self):
        sla = {"apr_percent": 22.0}
        result = calculate_fairness_score(sla)
        assert result["fairness_score"] <= 75
        assert any("interest" in r.lower() for r in result["reasons"])

    def test_high_apr(self):
        sla = {"apr_percent": 15.0}
        result = calculate_fairness_score(sla)
        assert result["fairness_score"] <= 85

    def test_moderate_apr(self):
        sla = {"apr_percent": 9.0}
        result = calculate_fairness_score(sla)
        assert result["fairness_score"] <= 95

    def test_low_apr_no_penalty(self):
        sla = {"apr_percent": 3.0}
        result = calculate_fairness_score(sla)
        # Low APR should not cause deductions
        assert not any("interest" in r.lower() for r in result["reasons"])


# ──────────── Early Termination ──────────── #

class TestEarlyTermination:
    def test_heavy_penalty(self):
        sla = {"penalties": {"early_termination": 15000}}
        result = calculate_fairness_score(sla)
        assert result["fairness_score"] <= 85
        assert any("termination" in r.lower() for r in result["reasons"])

    def test_moderate_penalty(self):
        sla = {"penalties": {"early_termination": 5000}}
        result = calculate_fairness_score(sla)
        assert any("termination" in r.lower() for r in result["reasons"])

    def test_no_penalty(self):
        sla = {"penalties": {"early_termination": "No penalty"}}
        result = calculate_fairness_score(sla)
        assert not any("termination" in r.lower() for r in result["reasons"])


# ──────────── Fee Checks ──────────── #

class TestFeeChecks:
    def test_very_high_doc_fee(self):
        sla = {"fees": {"documentation_fee": 15000}}
        result = calculate_fairness_score(sla)
        assert any("documentation" in r.lower() for r in result["reasons"])

    def test_high_processing_fee(self):
        sla = {"fees": {"processing_fee": 8000}}
        result = calculate_fairness_score(sla)
        assert any("processing" in r.lower() for r in result["reasons"])

    def test_no_fees_no_penalty(self):
        sla = {"fees": {"documentation_fee": None, "processing_fee": None}}
        result = calculate_fairness_score(sla)
        assert not any("fee" in r.lower() for r in result["reasons"])


# ──────────── Red Flags ──────────── #

class TestRedFlags:
    def test_multiple_flags(self):
        sla = {"red_flags": ["flag1", "flag2", "flag3"]}
        result = calculate_fairness_score(sla)
        assert any("red flag" in r.lower() for r in result["reasons"])

    def test_no_flags_bonus(self):
        sla = {"red_flags": []}
        result = calculate_fairness_score(sla)
        assert any("no red flags" in r.lower() for r in result["reasons"])


# ──────────── Price Comparison ──────────── #

class TestPriceComparison:
    def test_overpriced(self, price_comparison_bad):
        sla = {"red_flags": []}
        result = calculate_fairness_score(sla, price_comparison_bad)
        assert any("overpriced" in r.lower() for r in result["reasons"])

    def test_good_deal(self, price_comparison_good):
        sla = {"red_flags": []}
        result = calculate_fairness_score(sla, price_comparison_good)
        assert any("good deal" in r.lower() or "below market" in r.lower() for r in result["reasons"])


# ──────────── Rating Thresholds ──────────── #

class TestRatingThresholds:
    def test_excellent_rating(self, fair_deal_sla):
        result = calculate_fairness_score(fair_deal_sla)
        assert result["fairness_score"] >= 85
        assert result["rating"] == "Excellent"

    def test_poor_rating(self, high_apr_sla):
        result = calculate_fairness_score(high_apr_sla)
        assert result["fairness_score"] < 55
        assert result["rating"] in ["Poor", "Below Average"]

    def test_score_bounds(self):
        # Worst case: should not go below 0
        sla = {
            "apr_percent": 50.0,
            "fees": {"documentation_fee": 50000, "processing_fee": 50000},
            "penalties": {"early_termination": 50000},
            "red_flags": ["f1", "f2", "f3", "f4", "f5"],
        }
        result = calculate_fairness_score(sla)
        assert 0 <= result["fairness_score"] <= 100

    def test_result_structure(self, sample_sla):
        result = calculate_fairness_score(sample_sla)
        assert "fairness_score" in result
        assert "rating" in result
        assert "summary" in result
        assert "reasons" in result
        assert isinstance(result["reasons"], list)


# ──────────── Payment Burden ──────────── #

class TestPaymentBurden:
    def test_high_interest_ratio(self):
        sla = {
            "monthly_payment": 800,
            "finance_amount": 20000,
            "term_months": 60,
            "red_flags": [],
        }
        # total_paid = 48000, interest = 28000, ratio = 1.4 (140%)
        result = calculate_fairness_score(sla)
        assert any("interest" in r.lower() and "principal" in r.lower() for r in result["reasons"])
