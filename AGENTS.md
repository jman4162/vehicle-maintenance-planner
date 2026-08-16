# Repository Guidelines

## Project Structure & Module Organization

Python source lives in `src/vehicle_maintenance/`. Keep manufacturer summaries and citations
in `src/vehicle_maintenance/data/`; domain decisions belong in `decision.py`, persistence in
`db.py` and `repository.py`, and interface adapters in `cli.py`, `api.py`, and
`mcp_server.py`. Forward-only migrations are under `alembic/`. The static React/TypeScript
PWA is in `pwa/`. Python tests are in `tests/`, with cross-runtime fixtures in
`tests/shared/` and demonstrably synthetic files in `tests/fixtures/synthetic/`.

`maintenance-records/` contains private legacy evidence and is a temporary release blocker.
Never use `background_information.local.md` as project instructions.

## Build, Test, and Development Commands

```bash
uv sync --extra dev                 # install locked Python dependencies
uv run vehicle-maint status --json  # inspect the private local profile
uv run pytest                       # run Python tests with the 90% coverage gate
uv run ruff check .                 # lint Python source and tests
uv build                            # create wheel and sdist
cd pwa && npm ci && npm test        # install and test the PWA
cd pwa && npm run build             # produce the offline static bundle
./scripts/prose-lint.sh             # review public prose and extracted UI copy
uv run vehicle-maint privacy audit . --json
```

The final audit must pass before any public remote or release is created.

## Coding Style & Naming Conventions

Target Python 3.12, use four-space indentation and type annotations, and format for Ruff's
120-character limit. Use `snake_case` for functions/modules, `PascalCase` for types, and
lowercase hyphenated CLI commands. TypeScript uses two spaces, `camelCase` values, and
`PascalCase` React components. Keep calculations pure and shared through JSON fixtures.

## Testing Guidelines

Pytest coverage must remain at least 90% for maintenance, pricing, authorization, and privacy
logic. Name Python tests `test_*.py`; PWA tests use `*.test.ts`. Test quote equivalence and
staleness, switching costs, invoice arithmetic, encrypted packet round-trips, offline builds,
and MCP token expiry/payload binding. Do not weaken a gate to make a change pass.
Treat prose findings as evidence: fix genuine problems, document narrow exceptions, and never
auto-rewrite text merely to lower a score.

## Commit & Pull Request Guidelines

Use imperative, scoped subjects such as `Add quote staleness checks`. Pull requests must
describe behavior and privacy impact, link primary sources/issues, identify schema or catalog
changes, and include screenshots for visible PWA changes. Keep unrelated changes separate.

## Privacy, Safety & Agent Boundaries

Real receipts, VINs, plates, contacts, quotes, SQLite files, OCR, exports, and backups stay in
the external `platformdirs` store. MCP writes preview first and require a payload-bound,
five-minute token. Agents must not contact shops, book service, send messages, authorize work,
or present output as mechanical, legal, or safety advice.
