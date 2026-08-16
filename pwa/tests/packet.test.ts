import { describe, expect, it } from "vitest";
import { parseDecisionPacket } from "../src/packet";

const packet = {
  schema_version: 1,
  exported_at: "2026-08-15T12:00:00Z",
  vehicle_label: "Synthetic 2024 vehicle",
  plan: { id: "plan-synthetic", service_codes: ["A", "6", "7"], odometer_miles: 8462 },
  catalog: [{ code: "7", title: "Brake fluid", summary: "Synthetic summary", market: "US", model_applicability: "Synthetic vehicle", source_url: "https://example.com/source", retrieved_date: "2026-08-15" }],
  quotes: [],
  benchmarks: [],
};

describe("decision packet schema", () => {
  it("accepts the public v1 schema", () => expect(parseDecisionPacket(packet).plan.odometer_miles).toBe(8462));
  it("rejects malformed packets", () => expect(() => parseDecisionPacket({ ...packet, schema_version: 2 })).toThrow());
});
