"""Provider-neutral, identical quote-request packet generation."""

from __future__ import annotations

from pathlib import Path

from .catalog import explain_minder_code
from .paths import data_paths
from .repository import list_shops, resolve_plan

REQUEST_TEMPLATE = """Please provide a written, itemized quote for {vehicle} at {odometer:,} miles.

Requested Maintenance Minder scope: {codes}
{scope}

Please state:
- exact fluid and parts specifications and quantities;
- labor, parts, shop/environmental fees, tax, and out-the-door total;
- whether any listed service is bundled with other work;
- parts and labor warranty;
- estimated appointment duration; and
- relevant Honda and hybrid experience.

Do not add work beyond this scope without listing it separately and explaining why it is due.
"""


def quote_packet(plan_id: str, database: str | Path | None = None) -> dict[str, object]:
    plan = resolve_plan(plan_id, database)
    codes = plan.service_codes.split(",")
    scope = "\n".join(f"- {rule.code}: {rule.title}" for code in codes for rule in explain_minder_code(code))
    text = REQUEST_TEMPLATE.format(
        vehicle="U.S. 2024 Honda CR-V Sport-L Hybrid AWD",
        odometer=plan.odometer_miles,
        codes="".join(codes),
        scope=scope,
    )
    shops = list_shops(database)
    selected = [shop for shop in shops if shop["category"] == "dealer"][:2]
    selected += [shop for shop in shops if shop["category"] == "specialist"][:3]
    return {
        "plan_id": plan.id,
        "required_provider_mix": {"dealer": 2, "specialist": 3, "within_miles": 30},
        "provider_count": len(selected),
        "complete": len(selected) == 5,
        "requests": [{"shop": shop, "text": text} for shop in selected],
        "template_for_unfilled_slots": text,
    }


def export_quote_packet(plan_id: str, database: str | Path | None = None) -> Path:
    import json

    paths = data_paths().ensure()
    packet = quote_packet(plan_id, database)
    target = paths.exports / f"quote-packet-{packet['plan_id']}.json"
    target.write_text(json.dumps(packet, indent=2), encoding="utf-8")
    return target
