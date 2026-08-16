"""Public, serializable domain types shared by CLI, API, and MCP surfaces."""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl, model_validator


class DueState(StrEnum):
    DUE_NOW = "due_now"
    DUE_SOON = "due_soon"
    TIME_DUE = "time_due"
    FORECAST = "forecast"
    DEALER_RECOMMENDED = "dealer_recommended"
    UNKNOWN = "unknown"


class Origin(StrEnum):
    VEHICLE_DISPLAYED = "vehicle_displayed"
    DEALER_RECOMMENDED = "dealer_recommended"
    USER_REQUESTED = "user_requested"


class Decision(StrEnum):
    AUTHORIZE_NOW = "authorize_now"
    CLARIFY = "clarify_before_authorizing"
    DEFER_AND_QUOTE = "defer_and_quote"
    SAFETY_ADVICE = "seek_professional_safety_advice"


class Vehicle(BaseModel):
    id: str
    market: str = "US"
    model_year: int
    make: str
    model: str
    trim: str
    drivetrain: str
    purchase_month: date | None = None
    vin_last4: str | None = Field(default=None, min_length=4, max_length=4)


class MaintenanceReading(BaseModel):
    vehicle_id: str
    captured_at: datetime
    odometer_miles: int = Field(ge=0)
    minder_code: str | None = None
    oil_life_percent: int | None = Field(default=None, ge=0, le=100)
    origin: Origin = Origin.VEHICLE_DISPLAYED


class MaintenanceRule(BaseModel):
    code: str
    title: str
    summary: str
    market: str
    model_applicability: str
    source_url: HttpUrl
    retrieved_date: date
    time_fallback_months: int | None = None
    time_fallback_note: str | None = None


class DueAssessment(BaseModel):
    code: str
    state: DueState
    reason: str
    rule: MaintenanceRule | None = None


class ServiceLineItem(BaseModel):
    description: str
    labor_cents: int = Field(default=0, ge=0)
    parts_cents: int = Field(default=0, ge=0)
    fees_cents: int = Field(default=0, ge=0)
    tax_cents: int = Field(default=0, ge=0)
    total_cents: int = Field(ge=0)
    maintenance_codes: list[str] = []


class ServiceEvent(BaseModel):
    id: str
    vehicle_id: str
    service_date: date
    odometer_miles: int = Field(ge=0)
    displayed_code: str | None = None
    total_cents: int = Field(ge=0)
    provider_name: str | None = None
    line_items: list[ServiceLineItem] = []


class Document(BaseModel):
    id: str
    event_id: str | None = None
    original_name: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    local_path: str
    reviewed: bool = False
    extracted_text_path: str | None = None


class Shop(BaseModel):
    id: str
    name: str
    category: Literal["dealer", "specialist", "other"]
    distance_miles: float = Field(ge=0)
    honda_hybrid_experience: float = Field(ge=0, le=1)
    source_url: HttpUrl | None = None
    verified_at: date | None = None


class QuoteRequest(BaseModel):
    shop_id: str
    service_codes: list[str]
    text: str


class Quote(BaseModel):
    id: str
    shop_id: str
    plan_id: str
    received_at: date
    out_the_door_cents: int = Field(gt=0)
    warranty_score: float = Field(ge=0, le=1)
    travel_minutes: int = Field(ge=0)
    completeness_score: float = Field(ge=0, le=1)
    honda_hybrid_experience: float = Field(ge=0, le=1)
    comparable_scope: bool = True
    written: bool = True
    bundle_notes: str | None = None


class Authorization(BaseModel):
    event_id: str
    recorded_at: datetime
    decision: Decision
    amount_cents: int | None = Field(default=None, ge=0)
    evidence: str


class CostBenchmark(BaseModel):
    service_code: str
    market: str
    low_cents: int = Field(ge=0)
    median_cents: int = Field(ge=0)
    high_cents: int = Field(ge=0)
    retrieved_at: date
    source_url: HttpUrl

    @model_validator(mode="after")
    def ordered_range(self) -> CostBenchmark:
        if not self.low_cents <= self.median_cents <= self.high_cents:
            raise ValueError("benchmark range must be low <= median <= high")
        return self


class RankedQuote(BaseModel):
    quote: Quote
    score: float
    stale: bool
    eligible: bool
    reasons: list[str]


class QuoteComparison(BaseModel):
    ranked: list[RankedQuote]
    comparable_current_count: int
    best_value_declared: bool
    best_quote_id: str | None
    notice: str


class BreakEvenResult(BaseModel):
    dealer_cents: int
    alternative_cents: int
    savings_cents: int
    break_even_hours: dict[str, float]
    explanation: str


class PrivacyFinding(BaseModel):
    path: str
    kind: str
    detail: str


class PrivacyReport(BaseModel):
    root: str
    passed: bool
    scanned_files: int
    findings: list[PrivacyFinding]


class MutationPreview(BaseModel):
    operation: str
    payload: dict[str, Any]
    commit: bool
    confirmation_token: str | None = None
    expires_at: datetime | None = None
    result: dict[str, Any] | None = None
