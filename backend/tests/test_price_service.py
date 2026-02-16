"""
Unit tests for backend.price_service
Tests: MSRP lookup, depreciation, mileage/condition adjustments, estimate_price
"""

import pytest
from backend.price_service import (
    _find_msrp,
    _get_depreciation_factor,
    _mileage_adjustment,
    _condition_multiplier,
    _estimate_msrp_by_category,
    estimate_price,
    compare_contract_to_market,
)


# ──────────── MSRP Lookup ──────────── #

class TestMSRPLookup:
    def test_exact_match(self):
        msrp, source = _find_msrp("Toyota", "Camry", 2023)
        assert msrp is not None
        assert msrp > 20000
        assert source == "msrp_database"

    def test_case_insensitive(self):
        msrp1, _ = _find_msrp("TOYOTA", "camry", 2023)
        msrp2, _ = _find_msrp("toyota", "Camry", 2023)
        assert msrp1 == msrp2

    def test_unknown_model_fallback(self):
        msrp, source = _find_msrp("UnknownMake", "UnknownModel", 2023)
        # _find_msrp returns None for unknown models; fallback is in estimate_price
        assert msrp is None
        # But estimate_price should still work via category fallback
        result = estimate_price("UnknownMake", "UnknownModel", 2023)
        assert result["market_price"] > 0

    def test_multiple_makes_available(self):
        for make, model in [("Honda", "Civic"), ("Ford", "F-150"), ("BMW", "3 Series")]:
            msrp, _ = _find_msrp(make, model, 2023)
            assert msrp is not None, f"MSRP not found for {make} {model}"

    def test_category_fallback(self):
        msrp = _estimate_msrp_by_category("sedan")
        assert msrp == 28000

    def test_category_default(self):
        msrp = _estimate_msrp_by_category("unknown_type")
        assert msrp == 30000  # default


# ──────────── Depreciation ──────────── #

class TestDepreciation:
    def test_new_car(self):
        factor = _get_depreciation_factor(0)
        assert factor == 1.0

    def test_one_year_old(self):
        factor = _get_depreciation_factor(1)
        assert 0.7 <= factor < 1.0

    def test_five_year_old(self):
        factor = _get_depreciation_factor(5)
        assert 0.3 <= factor <= 0.6

    def test_very_old(self):
        factor = _get_depreciation_factor(20)
        assert factor > 0  # should never be zero

    def test_monotonically_decreasing(self):
        factors = [_get_depreciation_factor(age) for age in range(0, 15)]
        for i in range(1, len(factors)):
            assert factors[i] <= factors[i - 1], f"Depreciation not decreasing at age {i}"


# ──────────── Mileage Adjustment ──────────── #

class TestMileageAdjustment:
    def test_average_mileage(self):
        # 3-year-old car with 36k miles = average (12k/yr)
        adj = _mileage_adjustment(36000, 3)
        assert 0.95 <= adj <= 1.05  # near 1.0

    def test_low_mileage_bonus(self):
        adj = _mileage_adjustment(5000, 3)
        assert adj > 1.0

    def test_high_mileage_penalty(self):
        adj = _mileage_adjustment(100000, 3)
        assert adj < 1.0


# ──────────── Condition Multiplier ──────────── #

class TestConditionMultiplier:
    def test_excellent(self):
        assert _condition_multiplier("excellent") > _condition_multiplier("good")

    def test_good(self):
        assert _condition_multiplier("good") > _condition_multiplier("fair")

    def test_fair(self):
        assert _condition_multiplier("fair") > _condition_multiplier("poor")

    def test_unknown_defaults(self):
        mult = _condition_multiplier("unknown")
        assert mult > 0


# ──────────── Full Estimation ──────────── #

class TestEstimatePrice:
    def test_known_vehicle(self):
        result = estimate_price("Toyota", "Camry", 2023)
        assert result["market_price"] > 0
        assert result["low_price"] < result["market_price"] < result["high_price"]
        assert 0 < result["confidence"] <= 1.0

    def test_with_mileage(self):
        low_mi = estimate_price("Toyota", "Camry", 2023, mileage=10000)
        high_mi = estimate_price("Toyota", "Camry", 2023, mileage=100000)
        assert low_mi["market_price"] > high_mi["market_price"]

    def test_condition_affects_price(self):
        excellent = estimate_price("Honda", "Civic", 2022, condition="excellent")
        poor = estimate_price("Honda", "Civic", 2022, condition="poor")
        assert excellent["market_price"] > poor["market_price"]

    def test_result_structure(self):
        result = estimate_price("Toyota", "Camry", 2023)
        assert "low_price" in result
        assert "market_price" in result
        assert "high_price" in result
        assert "confidence" in result
        assert "make" in result
        assert "model" in result
        assert "year" in result

    def test_unknown_vehicle_still_works(self):
        result = estimate_price("UnknownMake", "UnknownModel", 2020)
        assert result["market_price"] > 0
        assert result["confidence"] < 1.0  # lower confidence


# ──────────── Contract-to-Market Comparison ──────────── #

class TestCompareContractToMarket:
    def test_with_known_vehicle(self):
        sla = {"finance_amount": 30000}
        result = compare_contract_to_market(sla, "Toyota", "Camry", 2023)
        assert "comparison_available" in result

    def test_no_finance_amount(self):
        sla = {}
        result = compare_contract_to_market(sla, "Toyota", "Camry", 2023)
        assert result["comparison_available"] is False
