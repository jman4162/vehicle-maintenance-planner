import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { breakEven, compareQuotes, recommendDecision, type Quote } from "../src/decision";

const fixture = JSON.parse(readFileSync(resolve("..", "tests", "shared", "decision-parity.json"), "utf8"));

describe("decision parity", () => {
  it("matches the Python break-even fixture", () => {
    const result = breakEven(fixture.break_even.dealer_cents, fixture.break_even.alternative_cents);
    expect(result.savingsCents).toBe(fixture.break_even.expected_savings_cents);
    expect(result.breakEvenHours).toEqual(fixture.break_even.expected_hours);
  });

  it("requires three current comparable written quotes", () => {
    const result = compareQuotes(fixture.quotes as Quote[], new Date("2026-08-15T12:00:00"));
    expect(result.bestValueDeclared).toBe(true);
    expect(result.bestQuoteId).toBe("quote-specialist-a");
    const stale = { ...fixture.quotes[0], received_at: "2026-07-01" };
    expect(compareQuotes([stale, ...fixture.quotes.slice(1)], new Date("2026-08-15T12:00:00")).bestValueDeclared).toBe(false);
  });

  it("covers support-state precedence", () => {
    const base = { safetyUncertainty: false, missingScopeOrFees: false, dueNow: false, alternativeSaves: true, extraTripHours: 1, breakEvenHours: 2 };
    expect(recommendDecision({ ...base, safetyUncertainty: true })).toBe("seek_professional_safety_advice");
    expect(recommendDecision({ ...base, missingScopeOrFees: true })).toBe("clarify_before_authorizing");
    expect(recommendDecision(base)).toBe("defer_and_quote");
    expect(recommendDecision({ ...base, dueNow: true })).toBe("authorize_now");
  });

  it("rejects negative prices", () => expect(() => breakEven(-1, 0)).toThrow("non-negative"));
});
