"""Local API for automation and optional desktop serving; the public PWA needs no backend."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .catalog import explain_minder_code
from .decision import calculate_break_even
from .repository import quote_comparison, service_history, status

app = FastAPI(
    title="Vehicle Maintenance Planner",
    version="0.1.0-dev",
    description="Local-only support; not mechanical, legal, or safety advice.",
)


class BreakEvenInput(BaseModel):
    dealer_cents: int
    alternative_cents: int


@app.get("/api/status")
def get_status():
    return status()


@app.get("/api/codes/{displayed_code}")
def get_code(displayed_code: str):
    try:
        return [rule.model_dump(mode="json") for rule in explain_minder_code(displayed_code)]
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/history")
def get_history():
    return service_history()


@app.get("/api/plans/{plan_id}/quotes")
def get_quotes(plan_id: str):
    try:
        return quote_comparison(plan_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/decision/break-even")
def post_break_even(payload: BreakEvenInput):
    return calculate_break_even(payload.dealer_cents, payload.alternative_cents)


def mount_pwa(directory: Path | None = None) -> None:
    build = directory or Path(__file__).parents[2] / "pwa" / "dist"
    if not build.is_dir():
        return
    assets = build / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def pwa_fallback(path: str):
        candidate = (build / path).resolve()
        if candidate.is_file() and build.resolve() in candidate.parents:
            return FileResponse(candidate)
        return FileResponse(build / "index.html")
