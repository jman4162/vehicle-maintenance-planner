# Public Release Gate

An untagged public development snapshot is allowed only after the working directory and exact
commit pass privacy and secret scanning. It does not authorize a package upload, hosted PWA,
GitHub Release, or version tag. Before `v0.1.0`, all boxes require fresh evidence:

- [ ] CLI, domain, FastAPI, PWA, and MCP acceptance tests pass.
- [ ] `vehicle-maint privacy audit .` and secret scanning pass.
- [ ] `maintenance-records/` and every real document are outside the source tree.
- [ ] Every fixture has a recorded synthetic-data review.
- [ ] Catalog citations and summarized text pass source, applicability, and copyright review.
- [ ] `./scripts/prose-lint.sh` passes and its retained findings receive human review.
- [ ] MCP preview/commit safeguards pass adversarial token and prohibited-action tests.
- [ ] `vehicle-maintenance-planner` distribution availability is confirmed immediately before release.
- [ ] The production PWA passes browser airplane-mode and blocked-network testing.
- [ ] Wheel, sdist, static PWA, Python SBOM, JavaScript SBOM, hashes, and changelog are attached.
- [ ] Apache-2.0 notices and dependency licenses are reviewed.

Migrations are forward-only. Tag the approved commit as `v0.1.0`; do not publish a development
version or a build from a dirty tree.

## Development snapshot

On 2026-08-16, private records and reference manuals were checksum-verified and relocated outside
the repository. The working-directory privacy audit passes. Python and PWA suites, linters,
package builds, offline static-asset checks, SBOM generation, dependency audits, and prose checks
also pass. PyPI previously returned `404` for the exact distribution name; this is not a
reservation, so recheck immediately before a package release. Fixture construction and checksums
are recorded in `tests/FIXTURE_REVIEW.md`.
