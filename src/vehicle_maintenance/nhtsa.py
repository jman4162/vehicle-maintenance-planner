"""Explicit, opt-in NHTSA lookup; never called during normal local operation."""

from __future__ import annotations

import httpx

NHTSA_BASE = "https://vpic.nhtsa.dot.gov/api"
NHTSA_RECALLS = "https://api.nhtsa.gov/recalls/recallsByVehicle"


def decode_vin(vin: str, *, consent: bool, timeout: float = 10) -> dict[str, object]:
    if not consent:
        raise ValueError("NHTSA lookup requires explicit consent because the VIN is transmitted")
    normalized = vin.strip().upper()
    if len(normalized) != 17:
        raise ValueError("VIN must contain 17 characters")
    response = httpx.get(
        f"{NHTSA_BASE}/vehicles/DecodeVinValues/{normalized}",
        params={"format": "json"},
        timeout=timeout,
    )
    response.raise_for_status()
    results = response.json().get("Results", [])
    return {"source": "NHTSA vPIC", "result": results[0] if results else {}}


def recalls_by_vehicle(
    make: str,
    model: str,
    model_year: int,
    *,
    consent: bool,
    timeout: float = 10,
) -> dict[str, object]:
    if not consent:
        raise ValueError("NHTSA recall lookup requires explicit consent for a network request")
    response = httpx.get(
        NHTSA_RECALLS,
        params={"make": make, "model": model, "modelYear": model_year},
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()
    return {
        "source": "NHTSA Recalls API",
        "count": int(payload.get("Count", len(payload.get("results", [])))),
        "results": payload.get("results", []),
    }
