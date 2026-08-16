# Contributing

Use Python 3.12 and Node 22 or newer. Keep domain decisions in
`src/vehicle_maintenance/decision.py` and mirror them against shared JSON fixtures in both
Python and TypeScript. Run `uv run ruff check .`, `uv run pytest`, and `npm test` in `pwa/`
before opening a pull request. Run `./scripts/prose-lint.sh` after changing documentation or
user-visible PWA text. It combines a high-precision vocabulary guard, `slopscore-lint`, and
filtered `slopless` rules. Review evidence manually; do not auto-rewrite text to satisfy a score.

Use imperative, scoped commits such as `Add quote staleness tests`. Pull requests should
explain behavior and privacy impact, link relevant issues and primary sources, list migration
or catalog changes, and include PWA screenshots when the interface changes.

Only summarize manufacturer material; do not copy manuals or restricted ratings data. Every
maintenance rule needs market, model applicability, retrieval date, and a direct source URL.
Never contribute a real receipt, full VIN, plate, personal quote, address, phone number, or
email, even in an issue or fixture. Synthetic fixtures must be clearly labeled and must not be
derived by light redaction of a real person's record.

Database migrations are forward-only. Public behavior follows semantic versioning. A change
that weakens token binding, redaction, encryption, offline behavior, or the privacy audit
requires an explicit security review.
