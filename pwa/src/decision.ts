export interface Quote {
  id: string;
  shop_id: string;
  plan_id: string;
  received_at: string;
  out_the_door_cents: number;
  warranty_score: number;
  travel_minutes: number;
  completeness_score: number;
  honda_hybrid_experience: number;
  comparable_scope: boolean;
  written: boolean;
}

export interface RankedQuote {
  quote: Quote;
  score: number;
  stale: boolean;
  eligible: boolean;
  reasons: string[];
}

export function breakEven(dealerCents: number, alternativeCents: number) {
  if (dealerCents < 0 || alternativeCents < 0) throw new Error("prices must be non-negative");
  const savingsCents = dealerCents - alternativeCents;
  const breakEvenHours = Object.fromEntries(
    [50, 100, 150].map((rate) => [
      `$${rate}/hour`,
      Math.round((Math.max(savingsCents, 0) / 100 / rate) * 100) / 100,
    ]),
  );
  return { dealerCents, alternativeCents, savingsCents, breakEvenHours };
}

export function compareQuotes(quotes: Quote[], asOf = new Date()) {
  const day = 86_400_000;
  const current = quotes.filter((quote) => {
    const age = Math.floor((asOf.getTime() - new Date(`${quote.received_at}T00:00:00`).getTime()) / day);
    return age <= 30 && quote.comparable_scope && quote.written;
  });
  const lowest = current.length ? Math.min(...current.map((quote) => quote.out_the_door_cents)) : 0;
  const ranked: RankedQuote[] = quotes.map((quote) => {
    const age = Math.floor((asOf.getTime() - new Date(`${quote.received_at}T00:00:00`).getTime()) / day);
    const stale = age > 30;
    const reasons: string[] = [];
    if (stale) reasons.push(`quote is ${age} days old (limit 30)`);
    if (!quote.comparable_scope) reasons.push("service scope is not comparable");
    if (!quote.written) reasons.push("quote is not written");
    const eligible = reasons.length === 0;
    const price = lowest && eligible ? lowest / quote.out_the_door_cents : 0;
    const travel = Math.max(0, 1 - quote.travel_minutes / 60);
    const score = 100 * (
      0.5 * price + 0.2 * quote.honda_hybrid_experience + 0.15 * quote.warranty_score +
      0.1 * travel + 0.05 * quote.completeness_score
    );
    return { quote, score: Math.round(score * 100) / 100, stale, eligible, reasons };
  }).sort((a, b) => Number(b.eligible) - Number(a.eligible) || b.score - a.score);
  return {
    ranked,
    comparableCurrentCount: current.length,
    bestValueDeclared: current.length >= 3,
    bestQuoteId: current.length >= 3 ? ranked.find((item) => item.eligible)?.quote.id ?? null : null,
  };
}

export type Decision = "authorize_now" | "clarify_before_authorizing" | "defer_and_quote" | "seek_professional_safety_advice";

export function recommendDecision(input: {
  safetyUncertainty: boolean;
  missingScopeOrFees: boolean;
  dueNow: boolean;
  alternativeSaves: boolean;
  extraTripHours: number;
  breakEvenHours: number;
}): Decision {
  if (input.safetyUncertainty) return "seek_professional_safety_advice";
  if (input.missingScopeOrFees) return "clarify_before_authorizing";
  if (input.alternativeSaves && input.extraTripHours < input.breakEvenHours && !input.dueNow) {
    return "defer_and_quote";
  }
  return "authorize_now";
}
