# Vehicle Maintenance Planner Agent Guide

Use `uv run vehicle-maint ... --json` or the project MCP server for vehicle-maintenance
work. Treat the manufacturer code and the user's authorization decision as separate facts.
Never convert a dealer recommendation into `vehicle_displayed`, invent a mileage schedule,
or infer that quoted work is mechanically necessary.

Start with `status`, `explain-code`, and plan inspection. For price comparisons, require
three written quotes with equivalent scope that are no more than 30 days old. Calculate the
extra-trip break-even before recommending that the user leave an appointment.

MCP write tools record local data only. Always call them in preview mode first, show the exact
payload and result to the user, and use the returned token only after explicit confirmation.
Never send a message, contact a provider, book service, or authorize work. Keep address,
phone, email, plate, full VIN, receipts, estimates, quotes, OCR output, databases, exports,
backups, and authorization packets out of the repository.

The software provides organizational and arithmetic support. It does not provide mechanical, legal, or safety
advice. Escalate uncertain safety-critical conditions to a qualified professional.
