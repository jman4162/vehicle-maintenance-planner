#!/usr/bin/env bash
set -euo pipefail

uv sync --extra dev --locked
uv run ruff check .
uv run ruff format --check src tests
uv run pytest
uv run pip-audit --local --progress-spinner off
uv build
uv run vehicle-maint privacy audit . --json
uv run cyclonedx-py environment --pyproject pyproject.toml --output-reproducible \
  --output-format JSON --output-file dist/python-sbom.json .venv

(
  cd pwa
  npm ci
  npm run lint
  npm test
  npm audit --audit-level=high
  npm run build
  npm run test:offline
  tar -C dist -czf ../dist/vehicle-maintenance-planner-pwa.tar.gz .
  npm sbom --package-lock-only --sbom-format cyclonedx --sbom-type application > ../dist/pwa-sbom.json
)

./scripts/prose-lint.sh
shasum -a 256 dist/*.whl dist/*.tar.gz dist/*-sbom.json > dist/SHA256SUMS

echo "Automated gates passed. Complete the manual gates in RELEASE.md before publishing."
