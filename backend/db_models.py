"""
Pydantic models for request / response validation.
Shared across API endpoints, services, and DB layer.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ──────────────────── SLA / Contract Analysis ──────────────────── #

class SLAResult(BaseModel):
    """Structured output from contract analysis (rule + LLM merged)."""
    loan_type: Optional[str] = Field(None, description="Vehicle Lease or Car Loan")
    apr_percent: Optional[float] = Field(None, description="Annual interest rate")
    monthly_payment: Optional[float] = None
    term_months: Optional[int] = None
    down_payment: Optional[float] = None
    finance_amount: Optional[float] = None
    residual_value: Optional[float] = None
    mileage_allowance: Optional[int] = None
    overage_charge_per_mile: Optional[float] = None
    early_termination_clause: Optional[str] = None
    purchase_option_price: Optional[float] = None
    maintenance_responsibility: Optional[str] = None
    warranty_coverage: Optional[str] = None
    insurance_requirements: Optional[str] = None
    fees: Optional[dict] = Field(default_factory=dict)
    penalties: Optional[dict] = Field(default_factory=dict)
    red_flags: list[str] = Field(default_factory=list)
    negotiation_points: list[str] = Field(default_factory=list)


class FairnessResult(BaseModel):
    """Output from the fairness scoring engine."""
    fairness_score: float = Field(ge=0, le=100)
    reasons: list[str] = Field(default_factory=list)


class ContractAnalysisResponse(BaseModel):
    """Full response from /analyze."""
    contract_id: int
    sla: SLAResult
    fairness: FairnessResult
    extraction_method: str = "rule_based"


# ──────────────────── Vehicle / VIN ──────────────────── #

class VehicleInfo(BaseModel):
    vin: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[str] = None
    trim: Optional[str] = None
    body_class: Optional[str] = None
    engine: Optional[str] = None
    fuel_type: Optional[str] = None
    drive_type: Optional[str] = None
    plant_info: Optional[str] = None


class RecallInfo(BaseModel):
    nhtsa_campaign: Optional[str] = None
    component: Optional[str] = None
    summary: Optional[str] = None
    consequence: Optional[str] = None
    remedy: Optional[str] = None
    report_date: Optional[str] = None


class VINResponse(BaseModel):
    vehicle: VehicleInfo
    recalls: list[RecallInfo] = Field(default_factory=list)
    recalls_count: int = 0


# ──────────────────── Negotiation ──────────────────── #

class NegotiationStartRequest(BaseModel):
    contract_id: int
    user_message: Optional[str] = None


class ChatMessage(BaseModel):
    role: str
    content: str
    created_at: Optional[str] = None


class NegotiationChatRequest(BaseModel):
    thread_id: int
    message: str


class NegotiationChatResponse(BaseModel):
    thread_id: int
    reply: str
    history: list[ChatMessage] = Field(default_factory=list)


# ──────────────────── Price Estimation ──────────────────── #

class PriceEstimateRequest(BaseModel):
    make: str
    model: str
    year: int
    mileage: Optional[int] = None
    condition: Optional[str] = Field("good", description="excellent/good/fair/poor")


class PriceEstimateResponse(BaseModel):
    make: str
    model: str
    year: int
    low_price: float
    market_price: float
    high_price: float
    confidence: float = Field(ge=0, le=1)
    source: str = "estimation_engine"
    notes: list[str] = Field(default_factory=list)
