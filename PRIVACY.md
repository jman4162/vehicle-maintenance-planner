# Privacy

## Data boundary

Real vehicle records belong in the platform-specific directory returned by `platformdirs`,
not in this repository. On macOS that is normally
`~/Library/Application Support/Vehicle Maintenance Planner/`. The store contains SQLite,
documents, OCR output, encrypted exports, backups, and settings.

The static PWA has no backend, analytics, telemetry, remote fonts, or runtime CDN dependency.
Records and decision packets are encrypted with Web Crypto before browser persistence or
export. Estimate photos should be deleted after the user confirms extraction.

## Publication gate

Run:

```bash
uv run vehicle-maint privacy audit . --json
```

The audit rejects private databases, OCR/backup/export artifacts, media outside synthetic
fixtures, local-only files, environment files, common personal identifiers and credentials,
and images with EXIF GPS. A passing `.gitignore` is not evidence of privacy.

Do not include real receipts, VINs, plates, addresses, phone numbers, email addresses, or
personal quotes in commits, issues, discussions, screenshots, or test fixtures. Report a
suspected disclosure privately using [SECURITY.md](SECURITY.md).

## External requests

No network request is needed for local planning. NHTSA VIN decoding is opt-in and transmits
the supplied VIN to the NHTSA vPIC API. Provider research and quote contact remain manual;
agent tools cannot contact a provider.
