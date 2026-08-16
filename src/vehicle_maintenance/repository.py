"""Private database operations used across human and agent interfaces."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from uuid import uuid4

from sqlalchemy import desc, select

from .catalog import expand_minder_code
from .db import (
    BenchmarkRow,
    PlanRow,
    QuoteRow,
    ReadingRow,
    ServiceEventRow,
    ServiceLineItemRow,
    ShopRow,
    VehicleRow,
    session_scope,
)
from .decision import compare_quotes
from .models import Origin, Quote

DEFAULT_VEHICLE_ID = "crv-2024-sport-l-hybrid-awd"


def bootstrap_vehicle(database: str | Path | None = None) -> dict[str, object]:
    with session_scope(database) as session:
        vehicle = session.get(VehicleRow, DEFAULT_VEHICLE_ID)
        created = vehicle is None
        if vehicle is None:
            vehicle = VehicleRow(
                id=DEFAULT_VEHICLE_ID,
                market="US",
                model_year=2024,
                make="Honda",
                model="CR-V",
                trim="Sport-L Hybrid",
                drivetrain="AWD",
                purchase_month=date(2023, 9, 1),
                vin_last4=None,
            )
            session.add(vehicle)
        return {"vehicle_id": vehicle.id, "created": created}


def record_reading(payload: dict[str, object], database: str | Path | None = None) -> dict[str, object]:
    bootstrap_vehicle(database)
    with session_scope(database) as session:
        row = ReadingRow(
            vehicle_id=str(payload.get("vehicle_id", DEFAULT_VEHICLE_ID)),
            captured_at=datetime.fromisoformat(str(payload.get("captured_at", datetime.now().isoformat()))),
            odometer_miles=int(payload["odometer_miles"]),
            minder_code=str(payload["minder_code"]) if payload.get("minder_code") else None,
            oil_life_percent=(
                int(payload["oil_life_percent"]) if payload.get("oil_life_percent") is not None else None
            ),
            origin=str(payload.get("origin", Origin.VEHICLE_DISPLAYED.value)),
        )
        session.add(row)
        session.flush()
        return {"reading_id": row.id, "vehicle_id": row.vehicle_id}


def status(database: str | Path | None = None) -> dict[str, object]:
    bootstrap_vehicle(database)
    with session_scope(database) as session:
        vehicle = session.get(VehicleRow, DEFAULT_VEHICLE_ID)
        reading = session.scalar(
            select(ReadingRow)
            .where(ReadingRow.vehicle_id == DEFAULT_VEHICLE_ID)
            .order_by(desc(ReadingRow.captured_at))
            .limit(1)
        )
        events = session.scalars(
            select(ServiceEventRow)
            .where(ServiceEventRow.vehicle_id == DEFAULT_VEHICLE_ID)
            .order_by(desc(ServiceEventRow.service_date))
        ).all()
        plans = session.scalars(
            select(PlanRow).where(PlanRow.vehicle_id == DEFAULT_VEHICLE_ID, PlanRow.status == "active")
        ).all()
        return {
            "vehicle": {
                "id": vehicle.id,
                "display_name": (
                    f"{vehicle.model_year} {vehicle.make} {vehicle.model} {vehicle.trim} {vehicle.drivetrain}"
                ),
                "purchase_month": vehicle.purchase_month.isoformat()[:7] if vehicle.purchase_month else None,
                "service_pass_approximate_expiration": "2025-09",
            },
            "latest_reading": (
                {
                    "odometer_miles": reading.odometer_miles,
                    "minder_code": reading.minder_code,
                    "captured_at": reading.captured_at.isoformat(),
                    "origin": reading.origin,
                }
                if reading
                else None
            ),
            "service_event_count": len(events),
            "last_service": (
                {
                    "date": events[0].service_date.isoformat(),
                    "odometer_miles": events[0].odometer_miles,
                    "total_cents": events[0].total_cents,
                    "displayed_code": events[0].displayed_code,
                }
                if events
                else None
            ),
            "active_plan_ids": [plan.id for plan in plans],
        }


def create_plan(
    displayed_codes: str,
    odometer_miles: int,
    *,
    origin: Origin = Origin.VEHICLE_DISPLAYED,
    database: str | Path | None = None,
) -> dict[str, object]:
    bootstrap_vehicle(database)
    codes = expand_minder_code(displayed_codes)
    plan_id = f"plan-{datetime.now():%Y%m%d}-{uuid4().hex[:8]}"
    with session_scope(database) as session:
        session.add(
            PlanRow(
                id=plan_id,
                vehicle_id=DEFAULT_VEHICLE_ID,
                created_at=datetime.now(),
                service_codes=",".join(codes),
                odometer_miles=odometer_miles,
                origin=origin.value,
                status="active",
            )
        )
    return {
        "plan_id": plan_id,
        "service_codes": codes,
        "odometer_miles": odometer_miles,
        "origin": origin.value,
        "status": "active",
    }


def resolve_plan(plan_id: str, database: str | Path | None = None) -> PlanRow:
    with session_scope(database) as session:
        if plan_id.upper() == "ACTIVE":
            plan = session.scalar(
                select(PlanRow).where(PlanRow.status == "active").order_by(desc(PlanRow.created_at)).limit(1)
            )
        else:
            plan = session.get(PlanRow, plan_id)
        if plan is None:
            raise ValueError(f"service plan not found: {plan_id}")
        session.expunge(plan)
        return plan


def list_shops(database: str | Path | None = None) -> list[dict[str, object]]:
    with session_scope(database) as session:
        shops = session.scalars(
            select(ShopRow)
            .where(ShopRow.active.is_(True), ShopRow.distance_miles <= 30)
            .order_by(ShopRow.category, ShopRow.distance_miles)
        ).all()
        return [
            {
                "id": shop.id,
                "name": shop.name,
                "category": shop.category,
                "distance_miles": shop.distance_miles,
                "honda_hybrid_experience": shop.honda_hybrid_experience,
                "source_url": shop.source_url,
                "verified_at": shop.verified_at.isoformat() if shop.verified_at else None,
            }
            for shop in shops
        ]


def add_shop(payload: dict[str, object], database: str | Path | None = None) -> dict[str, object]:
    row_id = str(payload.get("id") or f"shop-{uuid4().hex[:10]}")
    with session_scope(database) as session:
        row = ShopRow(
            id=row_id,
            name=str(payload["name"]),
            category=str(payload["category"]),
            distance_miles=float(payload["distance_miles"]),
            honda_hybrid_experience=float(payload.get("honda_hybrid_experience", 0.5)),
            source_url=str(payload["source_url"]) if payload.get("source_url") else None,
            verified_at=date.fromisoformat(str(payload.get("verified_at", date.today().isoformat()))),
            active=True,
        )
        session.merge(row)
    return {"shop_id": row_id}


def add_quote(payload: dict[str, object], database: str | Path | None = None) -> dict[str, object]:
    quote_id = str(payload.get("id") or f"quote-{uuid4().hex[:10]}")
    plan = resolve_plan(str(payload.get("plan_id", "ACTIVE")), database)
    with session_scope(database) as session:
        row = QuoteRow(
            id=quote_id,
            shop_id=str(payload["shop_id"]),
            plan_id=plan.id,
            received_at=date.fromisoformat(str(payload.get("received_at", date.today().isoformat()))),
            out_the_door_cents=int(payload["out_the_door_cents"]),
            warranty_score=float(payload.get("warranty_score", 0.5)),
            travel_minutes=int(payload.get("travel_minutes", 30)),
            completeness_score=float(payload.get("completeness_score", 0.5)),
            honda_hybrid_experience=float(payload.get("honda_hybrid_experience", 0.5)),
            comparable_scope=bool(payload.get("comparable_scope", True)),
            written=bool(payload.get("written", True)),
            bundle_notes=str(payload["bundle_notes"]) if payload.get("bundle_notes") else None,
        )
        session.add(row)
    return {"quote_id": quote_id, "plan_id": plan.id}


def add_benchmark(payload: dict[str, object], database: str | Path | None = None) -> dict[str, object]:
    low = int(payload["low_cents"])
    median = int(payload["median_cents"])
    high = int(payload["high_cents"])
    if not low <= median <= high:
        raise ValueError("benchmark range must be low <= median <= high")
    with session_scope(database) as session:
        row = BenchmarkRow(
            service_code=str(payload["service_code"]),
            market=str(payload["market"]),
            low_cents=low,
            median_cents=median,
            high_cents=high,
            retrieved_at=date.fromisoformat(str(payload.get("retrieved_at", date.today().isoformat()))),
            source_url=str(payload["source_url"]),
        )
        session.add(row)
        session.flush()
        return {"benchmark_id": row.id, "service_code": row.service_code}


def quote_comparison(plan_id: str, database: str | Path | None = None) -> dict[str, object]:
    plan = resolve_plan(plan_id, database)
    with session_scope(database) as session:
        rows = session.scalars(select(QuoteRow).where(QuoteRow.plan_id == plan.id)).all()
        quotes = [
            Quote(
                id=row.id,
                shop_id=row.shop_id,
                plan_id=row.plan_id,
                received_at=row.received_at,
                out_the_door_cents=row.out_the_door_cents,
                warranty_score=row.warranty_score,
                travel_minutes=row.travel_minutes,
                completeness_score=row.completeness_score,
                honda_hybrid_experience=row.honda_hybrid_experience,
                comparable_scope=row.comparable_scope,
                written=row.written,
                bundle_notes=row.bundle_notes,
            )
            for row in rows
        ]
    return compare_quotes(quotes).model_dump(mode="json")


def seed_august_2026_event(database: str | Path | None = None) -> dict[str, object]:
    bootstrap_vehicle(database)
    with session_scope(database) as session:
        existing = session.get(ServiceEventRow, "service-2026-08-15")
        if existing:
            return {"event_id": existing.id, "created": False, "total_cents": existing.total_cents}
        event = ServiceEventRow(
            id="service-2026-08-15",
            vehicle_id=DEFAULT_VEHICLE_ID,
            service_date=date(2026, 8, 15),
            odometer_miles=8462,
            displayed_code="A67",
            total_cents=60521,
            provider_name="Dealer (private record)",
            notes="Imported from reviewed source documents; identifying fields excluded.",
        )
        event.line_items = [
            ServiceLineItemRow(
                description="Engine oil service",
                labor_cents=4351,
                parts_cents=5549,
                fees_cents=136,
                tax_cents=0,
                total_cents=10036,
                maintenance_codes="A",
            ),
            ServiceLineItemRow(
                description="Rear differential fluid service",
                labor_cents=5388,
                parts_cents=4570,
                fees_cents=246,
                tax_cents=0,
                total_cents=10204,
                maintenance_codes="6",
            ),
            ServiceLineItemRow(
                description="Brake fluid service",
                labor_cents=31000,
                parts_cents=1632,
                fees_cents=169,
                tax_cents=0,
                total_cents=32801,
                maintenance_codes="7",
            ),
            ServiceLineItemRow(
                description="Shop supplies and sales tax",
                labor_cents=0,
                parts_cents=0,
                fees_cents=1630,
                tax_cents=5850,
                total_cents=7480,
                maintenance_codes="",
            ),
        ]
        session.add(event)
        session.add(
            ReadingRow(
                vehicle_id=DEFAULT_VEHICLE_ID,
                captured_at=datetime(2026, 8, 15, 9, 0),
                odometer_miles=8462,
                minder_code="A67",
                oil_life_percent=None,
                origin=Origin.VEHICLE_DISPLAYED.value,
            )
        )
        return {"event_id": event.id, "created": True, "total_cents": event.total_cents}


def service_history(database: str | Path | None = None) -> list[dict[str, object]]:
    with session_scope(database) as session:
        events = session.scalars(select(ServiceEventRow).order_by(desc(ServiceEventRow.service_date))).all()
        return [
            {
                "id": event.id,
                "service_date": event.service_date.isoformat(),
                "odometer_miles": event.odometer_miles,
                "displayed_code": event.displayed_code,
                "total_cents": event.total_cents,
                "provider_name": event.provider_name,
                "line_items": [
                    {
                        "description": item.description,
                        "labor_cents": item.labor_cents,
                        "parts_cents": item.parts_cents,
                        "fees_cents": item.fees_cents,
                        "tax_cents": item.tax_cents,
                        "total_cents": item.total_cents,
                        "maintenance_codes": item.maintenance_codes.split(",") if item.maintenance_codes else [],
                    }
                    for item in event.line_items
                ],
            }
            for event in events
        ]
