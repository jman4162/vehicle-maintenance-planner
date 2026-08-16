"""Auditable pricing and authorization calculations with no provider side effects."""

from __future__ import annotations

from datetime import date

from .models import BreakEvenResult, Decision, Quote, QuoteComparison, RankedQuote

QUOTE_MAX_AGE_DAYS = 30


def compare_quotes(quotes: list[Quote], *, as_of: date | None = None) -> QuoteComparison:
    today = as_of or date.today()
    current_comparable = [
        quote
        for quote in quotes
        if (today - quote.received_at).days <= QUOTE_MAX_AGE_DAYS and quote.comparable_scope and quote.written
    ]
    lowest = min((quote.out_the_door_cents for quote in current_comparable), default=0)
    ranked: list[RankedQuote] = []
    for quote in quotes:
        age_days = (today - quote.received_at).days
        stale = age_days > QUOTE_MAX_AGE_DAYS
        reasons: list[str] = []
        if stale:
            reasons.append(f"quote is {age_days} days old (limit {QUOTE_MAX_AGE_DAYS})")
        if not quote.comparable_scope:
            reasons.append("service scope is not comparable")
        if not quote.written:
            reasons.append("quote is not written")
        eligible = not reasons
        price_score = lowest / quote.out_the_door_cents if lowest and eligible else 0
        travel_score = max(0.0, 1 - quote.travel_minutes / 60)
        score = 100 * (
            0.50 * price_score
            + 0.20 * quote.honda_hybrid_experience
            + 0.15 * quote.warranty_score
            + 0.10 * travel_score
            + 0.05 * quote.completeness_score
        )
        ranked.append(
            RankedQuote(
                quote=quote,
                score=round(score, 2),
                stale=stale,
                eligible=eligible,
                reasons=reasons,
            )
        )
    ranked.sort(key=lambda item: (item.eligible, item.score), reverse=True)
    enough = len(current_comparable) >= 3
    best_id = next((item.quote.id for item in ranked if item.eligible), None) if enough else None
    notice = (
        "Best value may be declared from at least three current, written, comparable quotes."
        if enough
        else f"Need {3 - len(current_comparable)} more current comparable quote(s) before declaring best value."
    )
    return QuoteComparison(
        ranked=ranked,
        comparable_current_count=len(current_comparable),
        best_value_declared=enough,
        best_quote_id=best_id,
        notice=notice,
    )


def calculate_break_even(dealer_cents: int, alternative_cents: int) -> BreakEvenResult:
    if dealer_cents < 0 or alternative_cents < 0:
        raise ValueError("prices must be non-negative")
    savings = dealer_cents - alternative_cents
    hours = {f"${hourly}/hour": round(max(savings, 0) / 100 / hourly, 2) for hourly in (50, 100, 150)}
    explanation = (
        "The alternative saves money before valuing another appointment; the hours are the maximum "
        "additional trip time that preserves those savings."
        if savings > 0
        else "The alternative does not save money, even before valuing another appointment."
    )
    return BreakEvenResult(
        dealer_cents=dealer_cents,
        alternative_cents=alternative_cents,
        savings_cents=savings,
        break_even_hours=hours,
        explanation=explanation,
    )


def recommend_decision(
    *,
    safety_uncertainty: bool,
    missing_scope_or_fees: bool,
    due_now: bool,
    alternative_saves: bool,
    extra_trip_hours: float,
    break_even_hours: float,
) -> Decision:
    if safety_uncertainty:
        return Decision.SAFETY_ADVICE
    if missing_scope_or_fees:
        return Decision.CLARIFY
    if alternative_saves and extra_trip_hours < break_even_hours and not due_now:
        return Decision.DEFER_AND_QUOTE
    return Decision.AUTHORIZE_NOW
