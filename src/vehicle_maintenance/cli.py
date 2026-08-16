"""Stable, non-interactive CLI with JSON output for automation."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import typer

from .api import mount_pwa
from .db import initialize_database
from .decision import calculate_break_even
from .invoice import audit_invoice
from .maintenance import assess_displayed_code
from .migration import migrate_records
from .nhtsa import decode_vin, recalls_by_vehicle
from .ocr import AppleVisionOCRProvider, ManualOCRProvider
from .packet import export_decision_packet, import_decision_packet
from .paths import data_paths
from .privacy import audit_tree
from .quotes import quote_packet
from .reminders import export_reminders
from .repository import (
    add_benchmark,
    add_quote,
    add_shop,
    create_plan,
    quote_comparison,
    seed_august_2026_event,
    status,
)

app = typer.Typer(no_args_is_help=True, help="Local-first vehicle maintenance planner.")
plan_app = typer.Typer(no_args_is_help=True)
invoice_app = typer.Typer(no_args_is_help=True)
quote_app = typer.Typer(no_args_is_help=True)
decision_app = typer.Typer(no_args_is_help=True)
privacy_app = typer.Typer(no_args_is_help=True)
private_app = typer.Typer(no_args_is_help=True)
shop_app = typer.Typer(no_args_is_help=True)
nhtsa_app = typer.Typer(no_args_is_help=True)
packet_app = typer.Typer(no_args_is_help=True)
benchmark_app = typer.Typer(no_args_is_help=True)
reminder_app = typer.Typer(no_args_is_help=True)
ocr_app = typer.Typer(no_args_is_help=True)
app.add_typer(plan_app, name="plan")
app.add_typer(invoice_app, name="invoice")
app.add_typer(quote_app, name="quote")
app.add_typer(decision_app, name="decision")
app.add_typer(privacy_app, name="privacy")
app.add_typer(private_app, name="private")
app.add_typer(shop_app, name="shop")
app.add_typer(nhtsa_app, name="nhtsa")
app.add_typer(packet_app, name="packet")
app.add_typer(benchmark_app, name="benchmark")
app.add_typer(reminder_app, name="reminder")
app.add_typer(ocr_app, name="ocr")


def emit(payload: Any, json_output: bool) -> None:
    serializable = payload.model_dump(mode="json") if hasattr(payload, "model_dump") else payload
    if json_output:
        typer.echo(json.dumps(serializable, indent=2, default=str))
    else:
        typer.echo(json.dumps(serializable, indent=2, default=str))


@app.command("status")
def status_command(json_output: bool = typer.Option(False, "--json")) -> None:
    emit(status(), json_output)


@app.command("explain-code")
def explain_code(displayed_code: str, json_output: bool = typer.Option(False, "--json")) -> None:
    emit(
        {
            "displayed_code": displayed_code.upper(),
            "origin": "vehicle_displayed",
            "assessments": [item.model_dump(mode="json") for item in assess_displayed_code(displayed_code)],
        },
        json_output,
    )


@plan_app.command("create")
def plan_create(
    codes: str = typer.Option(..., "--codes"),
    odometer: int = typer.Option(..., "--odometer", min=0),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    emit(create_plan(codes, odometer), json_output)


@invoice_app.command("audit")
def invoice_audit(path: Path, json_output: bool = typer.Option(False, "--json")) -> None:
    emit(audit_invoice(path), json_output)


@quote_app.command("packet")
def quote_packet_command(
    plan: str = typer.Option("ACTIVE", "--plan"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    emit(quote_packet(plan), json_output)


@quote_app.command("compare")
def quote_compare(
    plan: str = typer.Option("ACTIVE", "--plan"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    emit(quote_comparison(plan), json_output)


@quote_app.command("add")
def quote_add(payload: Path, json_output: bool = typer.Option(False, "--json")) -> None:
    emit(add_quote(json.loads(payload.read_text(encoding="utf-8"))), json_output)


@decision_app.command("break-even")
def decision_break_even(
    dealer_cents: int = typer.Option(..., "--dealer-cents", min=0),
    alternative_cents: int = typer.Option(..., "--alternative-cents", min=0),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    emit(calculate_break_even(dealer_cents, alternative_cents), json_output)


@privacy_app.command("audit")
def privacy_audit(root: Path = typer.Argument(Path(".")), json_output: bool = typer.Option(False, "--json")) -> None:
    report = audit_tree(root)
    emit(report, json_output)
    if not report.passed:
        raise typer.Exit(code=1)


@private_app.command("init")
def private_init(
    seed_august_event: bool = typer.Option(False, "--seed-august-event"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    paths = data_paths().ensure()
    initialize_database(paths.database)
    result: dict[str, object] = {"data_root": str(paths.root), "database": str(paths.database)}
    if seed_august_event:
        result["event"] = seed_august_2026_event(paths.database)
    emit(result, json_output)


@private_app.command("migrate-records")
def private_migrate_records(
    source: Path,
    data_dir: Path | None = typer.Option(None, "--data-dir"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    emit(migrate_records(source, destination=data_dir), json_output)


@shop_app.command("add")
def shop_add(payload: Path, json_output: bool = typer.Option(False, "--json")) -> None:
    emit(add_shop(json.loads(payload.read_text(encoding="utf-8"))), json_output)


@benchmark_app.command("add")
def benchmark_add(payload: Path, json_output: bool = typer.Option(False, "--json")) -> None:
    emit(add_benchmark(json.loads(payload.read_text(encoding="utf-8"))), json_output)


@nhtsa_app.command("decode-vin")
def nhtsa_decode_vin(
    vin: str,
    consent: bool = typer.Option(False, "--consent"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    emit(decode_vin(vin, consent=consent), json_output)


@nhtsa_app.command("recalls")
def nhtsa_recalls(
    make: str = typer.Option("Honda", "--make"),
    model: str = typer.Option("CR-V", "--model"),
    model_year: int = typer.Option(2024, "--model-year"),
    consent: bool = typer.Option(False, "--consent"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    emit(recalls_by_vehicle(make, model, model_year, consent=consent), json_output)


def _read_passphrase(path: Path) -> str:
    return path.read_text(encoding="utf-8").rstrip("\r\n")


@packet_app.command("export")
def packet_export(
    passphrase_file: Path = typer.Option(..., "--passphrase-file"),
    plan: str = typer.Option("ACTIVE", "--plan"),
    output: Path | None = typer.Option(None, "--output"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    target = export_decision_packet(_read_passphrase(passphrase_file), plan_id=plan, output=output)
    emit({"encrypted_packet": str(target), "plan_id": plan}, json_output)


@packet_app.command("import")
def packet_import(
    path: Path,
    passphrase_file: Path = typer.Option(..., "--passphrase-file"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    emit(import_decision_packet(path, _read_passphrase(passphrase_file)), json_output)


@reminder_app.command("export")
def reminder_export(
    appointment: datetime = typer.Option(..., "--appointment"),
    plan: str = typer.Option("ACTIVE", "--plan"),
    output: Path | None = typer.Option(None, "--output"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    target = export_reminders(plan, appointment, output=output)
    emit({"calendar_file": str(target), "external_action_taken": False}, json_output)


@ocr_app.command("extract")
def ocr_extract(
    path: Path,
    provider: str = typer.Option("auto", "--provider"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    selected = AppleVisionOCRProvider() if provider in {"auto", "apple-vision"} else ManualOCRProvider()
    if provider == "auto" and not selected.available():
        selected = ManualOCRProvider()
    if not selected.available():
        raise typer.BadParameter(f"OCR provider is unavailable: {provider}")
    text = selected.extract(path)
    paths = data_paths().ensure()
    target = paths.ocr / f"{path.stem}.txt"
    target.write_text(text, encoding="utf-8")
    emit({"provider": selected.name, "ocr_path": str(target), "characters": len(text)}, json_output)


@app.command("mcp")
def mcp_command() -> None:
    """Run the local stdio MCP server."""
    from .mcp_server import run as run_mcp

    run_mcp()


@app.command("serve")
def serve(host: str = typer.Option("127.0.0.1"), port: int = typer.Option(8765, min=1, max=65535)) -> None:
    """Serve the local API and built PWA. Keep host loopback unless you understand the exposure."""
    import uvicorn

    mount_pwa()
    uvicorn.run("vehicle_maintenance.api:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    app()
