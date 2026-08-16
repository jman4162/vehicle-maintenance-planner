# Synthetic Fixture Review

Reviewed on 2026-08-15. These files are deliberately constructed test data, contain no
VIN, plate, address, contact information, receipt image, provider quote, or copied invoice
text, and are approved for a future public release.

| Fixture | SHA-256 | Construction |
| --- | --- | --- |
| `fixtures/synthetic/invoice-a67.json` | `4c5545a97cf4555f287a4b102006a5c4ee5b63b4ab8b5092b5c8feb1e3f39654` | Arithmetic-only A67 acceptance scenario using the plan's expressly supplied totals. |
| `shared/decision-parity.json` | `77331a5a74ec0b377b982b73258d73c501fb279c4c12a21939623a1020ce5061` | Hand-authored branch cases for cross-runtime decision parity. |
| `shared/python-encrypted-packet.json` | `9e4a57bbaaafbdf2c03653aeea4ed7393b5575d57fe72e69d3ee2999724df1cc` | Deterministic interop envelope generated from synthetic packet fields and a test-only passphrase. |

Any fixture edit invalidates this review until its content and checksum are reviewed again.
