# Vehicle Maintenance Planner

`vehicle-maintenance-planner` is a local-first toolkit for explaining manufacturer
maintenance codes, planning service, gathering comparable written quotes, auditing
invoices, and deciding whether another trip is worth the likely savings.

> **Important:** This software is not mechanical, legal, or safety advice. Confirm
> safety-critical questions with a qualified professional and current primary sources.

## Privacy model

The repository contains code, cited summaries, and synthetic fixtures only. Real VINs,
receipts, estimates, quotes, authorizations, and contact details live outside the source
tree. On macOS the default private store is:

```text
~/Library/Application Support/Vehicle Maintenance Planner/
```

A public source snapshot is allowed only when `uv run vehicle-maint privacy audit .` passes
against both the working directory and an exact checkout of the commit, and secret scanning
finds nothing. A source snapshot does not authorize a package upload, hosted PWA, tag, or
GitHub Release; those remain subject to every gate in `RELEASE.md`.

## Quick start

```bash
uv sync --extra dev
uv run vehicle-maint private init --json
uv run vehicle-maint explain-code A67 --json
uv run vehicle-maint plan create --codes A67 --odometer 8462 --json
uv run vehicle-maint decision break-even \
  --dealer-cents 32801 --alternative-cents 16000 --json
uv run vehicle-maint packet export --plan ACTIVE \
  --passphrase-file /path/to/private-passphrase-file --json
uv run pytest
```

Build and test the offline PWA separately:

```bash
cd pwa
npm ci
npm run lint
npm test
npm run build
npm run test:offline
```

Check public documentation, Python docstrings, and extracted PWA copy locally:

```bash
./scripts/prose-lint.sh
```

The check reports writing patterns, not authorship. It combines a narrow vocabulary guard,
`slopscore-lint`, and selected `slopless` rules; findings require human review.

## Supported workflow

1. Record the displayed Maintenance Minder code and odometer.
2. Review cited manufacturer-defined scope; no invented mileage interval is added.
3. Generate identical requests for two dealers and three independent specialists.
4. Compare at least three current, written, equivalent-scope quotes.
5. Import an encrypted decision packet into the offline PWA before the appointment.
6. Check estimate scope, fees, Washington authorization thresholds, and extra-trip
   break-even time before deciding.
7. Record the user's decision and audit the final invoice locally.

MCP write tools only record local facts. They preview by default and require a
payload-bound, expiring confirmation token; they cannot contact shops, book service,
send messages, or authorize work.

Encrypted desktop-to-phone packets use PBKDF2-SHA-256 and AES-256-GCM with compatible Python
and Web Crypto implementations. Passphrases are read from a file to avoid shell-history
exposure. Importing a reviewed on-site packet records its support state locally but performs
no external action.

## Sources and scope

Catalog entries are short summaries with source URL, market, applicability, and retrieval
date. See `src/vehicle_maintenance/data/`. Optional NHTSA lookup requires explicit consent
because it sends a VIN to the federal API. See [PRIVACY.md](PRIVACY.md),
[DISCLAIMER.md](DISCLAIMER.md), and [CONTRIBUTING.md](CONTRIBUTING.md) before contributing.
