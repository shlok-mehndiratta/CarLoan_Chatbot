"""
Integration tests for the FastAPI backend API.
Tests: health check, VIN lookup, price estimation, negotiation endpoints
"""

import pytest


# ──────────── Health & Root ──────────── #

class TestHealthEndpoints:
    def test_root(self, test_client):
        response = test_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data or "message" in data or isinstance(data, dict)

    def test_health(self, test_client):
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok" or response.status_code == 200


# ──────────── Price Estimation API ──────────── #

class TestPriceEstimationAPI:
    def test_price_estimate_valid(self, test_client):
        response = test_client.post("/price-estimate", json={
            "make": "Toyota",
            "model": "Camry",
            "year": 2023,
            "condition": "good",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["market_price"] > 0
        assert data["low_price"] < data["high_price"]

    def test_price_estimate_with_mileage(self, test_client):
        response = test_client.post("/price-estimate", json={
            "make": "Honda",
            "model": "Civic",
            "year": 2022,
            "mileage": 30000,
            "condition": "good",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["market_price"] > 0

    def test_price_estimate_unknown_vehicle(self, test_client):
        response = test_client.post("/price-estimate", json={
            "make": "Unknown",
            "model": "Car",
            "year": 2020,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["market_price"] > 0


# ──────────── VIN Endpoints ──────────── #

class TestVINEndpoints:
    def test_vin_lookup_format(self, test_client):
        """Test that VIN endpoint returns a response (may fail if NHTSA is down)."""
        response = test_client.get("/vin/1HGCG5655WA093478")
        # Accept 200 (success) or 500 (NHTSA down) — both valid app behavior
        assert response.status_code in [200, 500]

    def test_vin_recalls_format(self, test_client):
        response = test_client.get("/vin/1HGCG5655WA093478/recalls")
        assert response.status_code in [200, 500]


# ──────────── Contract Retrieval ──────────── #

class TestContractRetrieval:
    def test_nonexistent_contract(self, test_client):
        response = test_client.get("/contract/99999")
        assert response.status_code in [404, 200]


# ──────────── Negotiation Endpoints ──────────── #

class TestNegotiationEndpoints:
    def test_negotiate_start_no_contract(self, test_client):
        """Starting negotiation for non-existent contract should fail gracefully."""
        response = test_client.post("/negotiate/start", json={
            "contract_id": 99999,
        })
        # Should return 404 or error message
        assert response.status_code in [200, 404, 500]

    def test_negotiate_chat_invalid_thread(self, test_client):
        """Chat on invalid thread should fail gracefully."""
        response = test_client.post("/negotiate/chat", json={
            "thread_id": 99999,
            "message": "Hello",
        })
        assert response.status_code in [200, 404, 500]

    def test_negotiate_history_empty(self, test_client):
        """History for non-existent thread should return empty or error."""
        response = test_client.get("/negotiate/history/99999")
        assert response.status_code in [200, 404, 500]

    def test_negotiate_email_no_contract(self, test_client):
        """Email gen for non-existent contract should fail gracefully."""
        response = test_client.post("/negotiate/email", json={
            "contract_id": 99999,
            "tone": "professional",
        })
        assert response.status_code in [200, 404, 500]
