"""SQLAlchemy persistence for the private, local SQLite store."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship

from .paths import data_paths


class Base(DeclarativeBase):
    pass


class VehicleRow(Base):
    __tablename__ = "vehicles"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    market: Mapped[str] = mapped_column(String, default="US")
    model_year: Mapped[int] = mapped_column(Integer)
    make: Mapped[str] = mapped_column(String)
    model: Mapped[str] = mapped_column(String)
    trim: Mapped[str] = mapped_column(String)
    drivetrain: Mapped[str] = mapped_column(String)
    purchase_month: Mapped[date | None] = mapped_column(Date)
    vin_last4: Mapped[str | None] = mapped_column(String(4))


class ReadingRow(Base):
    __tablename__ = "maintenance_readings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vehicle_id: Mapped[str] = mapped_column(ForeignKey("vehicles.id"), index=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime)
    odometer_miles: Mapped[int] = mapped_column(Integer)
    minder_code: Mapped[str | None] = mapped_column(String)
    oil_life_percent: Mapped[int | None] = mapped_column(Integer)
    origin: Mapped[str] = mapped_column(String)


class ServiceEventRow(Base):
    __tablename__ = "service_events"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    vehicle_id: Mapped[str] = mapped_column(ForeignKey("vehicles.id"), index=True)
    service_date: Mapped[date] = mapped_column(Date)
    odometer_miles: Mapped[int] = mapped_column(Integer)
    displayed_code: Mapped[str | None] = mapped_column(String)
    total_cents: Mapped[int] = mapped_column(Integer)
    provider_name: Mapped[str | None] = mapped_column(String)
    notes: Mapped[str | None] = mapped_column(Text)
    line_items: Mapped[list[ServiceLineItemRow]] = relationship(back_populates="event", cascade="all, delete-orphan")


class ServiceLineItemRow(Base):
    __tablename__ = "service_line_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(ForeignKey("service_events.id"), index=True)
    description: Mapped[str] = mapped_column(String)
    labor_cents: Mapped[int] = mapped_column(Integer, default=0)
    parts_cents: Mapped[int] = mapped_column(Integer, default=0)
    fees_cents: Mapped[int] = mapped_column(Integer, default=0)
    tax_cents: Mapped[int] = mapped_column(Integer, default=0)
    total_cents: Mapped[int] = mapped_column(Integer)
    maintenance_codes: Mapped[str] = mapped_column(String, default="")
    event: Mapped[ServiceEventRow] = relationship(back_populates="line_items")


class DocumentRow(Base):
    __tablename__ = "documents"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    event_id: Mapped[str | None] = mapped_column(ForeignKey("service_events.id"), index=True)
    original_name: Mapped[str] = mapped_column(String)
    sha256: Mapped[str] = mapped_column(String(64), unique=True)
    local_path: Mapped[str] = mapped_column(Text)
    reviewed: Mapped[bool] = mapped_column(Boolean, default=False)
    extracted_text_path: Mapped[str | None] = mapped_column(Text)


class ShopRow(Base):
    __tablename__ = "shops"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String)
    distance_miles: Mapped[float] = mapped_column(Float)
    honda_hybrid_experience: Mapped[float] = mapped_column(Float)
    source_url: Mapped[str | None] = mapped_column(Text)
    verified_at: Mapped[date | None] = mapped_column(Date)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class PlanRow(Base):
    __tablename__ = "service_plans"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    vehicle_id: Mapped[str] = mapped_column(ForeignKey("vehicles.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    service_codes: Mapped[str] = mapped_column(String)
    odometer_miles: Mapped[int] = mapped_column(Integer)
    origin: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="active")


class QuoteRow(Base):
    __tablename__ = "quotes"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    shop_id: Mapped[str] = mapped_column(ForeignKey("shops.id"), index=True)
    plan_id: Mapped[str] = mapped_column(ForeignKey("service_plans.id"), index=True)
    received_at: Mapped[date] = mapped_column(Date)
    out_the_door_cents: Mapped[int] = mapped_column(Integer)
    warranty_score: Mapped[float] = mapped_column(Float)
    travel_minutes: Mapped[int] = mapped_column(Integer)
    completeness_score: Mapped[float] = mapped_column(Float)
    honda_hybrid_experience: Mapped[float] = mapped_column(Float)
    comparable_scope: Mapped[bool] = mapped_column(Boolean, default=True)
    written: Mapped[bool] = mapped_column(Boolean, default=True)
    bundle_notes: Mapped[str | None] = mapped_column(Text)


class AuthorizationRow(Base):
    __tablename__ = "authorizations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(ForeignKey("service_events.id"), index=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime)
    decision: Mapped[str] = mapped_column(String)
    amount_cents: Mapped[int | None] = mapped_column(Integer)
    evidence: Mapped[str] = mapped_column(Text)


class BenchmarkRow(Base):
    __tablename__ = "cost_benchmarks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    service_code: Mapped[str] = mapped_column(String, index=True)
    market: Mapped[str] = mapped_column(String)
    low_cents: Mapped[int] = mapped_column(Integer)
    median_cents: Mapped[int] = mapped_column(Integer)
    high_cents: Mapped[int] = mapped_column(Integer)
    retrieved_at: Mapped[date] = mapped_column(Date)
    source_url: Mapped[str] = mapped_column(Text)


class DecisionPacketRow(Base):
    __tablename__ = "decision_packets"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    plan_id: Mapped[str] = mapped_column(ForeignKey("service_plans.id"), index=True)
    imported_at: Mapped[datetime] = mapped_column(DateTime)
    support_state: Mapped[str] = mapped_column(String)
    payload_json: Mapped[str] = mapped_column(Text)


def get_engine(database: str | Path | None = None):
    target = Path(database) if database else data_paths().ensure().database
    target.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{target}", future=True)


def initialize_database(database: str | Path | None = None) -> Path:
    engine = get_engine(database)
    Base.metadata.create_all(engine)
    return Path(engine.url.database or "")


@contextmanager
def session_scope(database: str | Path | None = None) -> Iterator[Session]:
    engine = get_engine(database)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
