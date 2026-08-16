"""Local stdio MCP server with side-effect-free research and guarded recording tools."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from .decision import calculate_break_even
from .invoice import audit_invoice
from .maintenance import assess_displayed_code
from .mutations import preview_or_commit
from .quotes import quote_packet
from .repository import quote_comparison, service_history, status

INSTRUCTIONS = (
    "Vehicle Maintenance Planner is local-only. Read tools may explain and compare existing data. "
    "Write tools always preview first and require a payload-bound, five-minute confirmation token to commit. "
    "Never use these tools to contact a shop, send a message, book service, authorize work, or imply mechanical, "
    "legal, or safety advice. Personal address, phone, email, plate, and full VIN are redacted by default."
)

mcp = FastMCP("vehicle-maint", instructions=INSTRUCTIONS)
READ_ONLY = ToolAnnotations(readOnlyHint=True, openWorldHint=False)
LOCAL_WRITE = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=False,
    idempotentHint=False,
    openWorldHint=False,
)


@mcp.tool(annotations=READ_ONLY)
def vehicle_status() -> dict[str, Any]:
    """Read the current local vehicle status."""
    return status()


@mcp.tool(annotations=READ_ONLY)
def explain_code(displayed_code: str) -> list[dict[str, Any]]:
    """Explain manufacturer-defined Maintenance Minder scope from the cited catalog."""
    return [item.model_dump(mode="json") for item in assess_displayed_code(displayed_code)]


@mcp.tool(annotations=READ_ONLY)
def local_service_history() -> list[dict[str, Any]]:
    """Read redacted service history from the local database."""
    return service_history()


@mcp.tool(annotations=READ_ONLY)
def invoice_audit(path: str) -> dict[str, Any]:
    """Audit arithmetic for a reviewed local invoice; does not judge mechanical necessity."""
    return audit_invoice(path)


@mcp.tool(annotations=READ_ONLY)
def inspect_plan(plan_id: str = "ACTIVE") -> dict[str, Any]:
    """Inspect a service plan and its provider-neutral quote requests."""
    return quote_packet(plan_id)


@mcp.tool(annotations=READ_ONLY)
def compare_plan_quotes(plan_id: str = "ACTIVE") -> dict[str, Any]:
    """Rank current comparable written quotes; three are required to declare best value."""
    return quote_comparison(plan_id)


@mcp.tool(annotations=READ_ONLY)
def break_even(dealer_cents: int, alternative_cents: int) -> dict[str, Any]:
    """Calculate the maximum extra-trip time at $50, $100, and $150 per hour."""
    return calculate_break_even(dealer_cents, alternative_cents).model_dump(mode="json")


@mcp.tool(annotations=LOCAL_WRITE)
def add_reading(payload: dict[str, Any], commit: bool = False, confirmation_token: str | None = None) -> dict[str, Any]:
    """Preview or record a local odometer/Maintenance Minder reading."""
    return preview_or_commit("add_reading", payload, commit=commit, confirmation_token=confirmation_token).model_dump(
        mode="json"
    )


@mcp.tool(annotations=LOCAL_WRITE)
def import_reviewed_document(
    payload: dict[str, Any], commit: bool = False, confirmation_token: str | None = None
) -> dict[str, Any]:
    """Preview or copy a user-reviewed document into private local storage."""
    return preview_or_commit(
        "import_reviewed_document", payload, commit=commit, confirmation_token=confirmation_token
    ).model_dump(mode="json")


@mcp.tool(annotations=LOCAL_WRITE)
def record_quote(
    payload: dict[str, Any], commit: bool = False, confirmation_token: str | None = None
) -> dict[str, Any]:
    """Preview or record a written quote already obtained by the user."""
    return preview_or_commit("record_quote", payload, commit=commit, confirmation_token=confirmation_token).model_dump(
        mode="json"
    )


@mcp.tool(annotations=LOCAL_WRITE)
def record_authorization(
    payload: dict[str, Any], commit: bool = False, confirmation_token: str | None = None
) -> dict[str, Any]:
    """Preview or record a past user decision; this never authorizes or contacts anyone."""
    return preview_or_commit(
        "record_authorization", payload, commit=commit, confirmation_token=confirmation_token
    ).model_dump(mode="json")


@mcp.tool(annotations=LOCAL_WRITE)
def complete_service_event(
    payload: dict[str, Any], commit: bool = False, confirmation_token: str | None = None
) -> dict[str, Any]:
    """Preview or record a completed service event in the local database."""
    return preview_or_commit(
        "complete_service_event", payload, commit=commit, confirmation_token=confirmation_token
    ).model_dump(mode="json")


def run() -> None:
    mcp.run(transport="stdio")
