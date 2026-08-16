# Security Policy

This project is pre-release; no version currently receives public security support. Do not
file public issues containing private vehicle or identity data. Report suspected privacy,
encryption, confirmation-token, dependency, or MCP boundary flaws privately to the repository
maintainer once a public security contact exists.

MCP tools must never send messages, contact providers, book appointments, authorize work, or
transmit a VIN. Local mutations must default to preview and require an unexpired token bound
to the exact operation and payload. Releases require dependency locking, secret scanning,
SBOM generation, synthetic-fixture review, and an offline network-block test.
