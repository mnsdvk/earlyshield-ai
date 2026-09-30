from __future__ import annotations

from dataclasses import dataclass

KT_TO_KMH = 1.852


@dataclass(frozen=True)
class ParametricPayout:
    sum_insured: float
    wind_kmh: float
    wind_kt: float
    rain_48h_mm: float
    wind_payout_pct: int
    rain_addon_pct: int
    payout_pct: int
    payout_amount: float
    trigger_text: str


def calculate_parametric_payout(
    sum_insured: float,
    wind_kmh: float,
    rain_48h_mm: float,
) -> ParametricPayout:
    """Demonstration-only parametric trigger schedule.

    This is NOT an insurance product, pricing model, or underwriting recommendation.
    It is a hackathon liquidity stress-test showing how objective hazard triggers
    could release funds before conventional loss assessment.
    """
    sum_insured = max(0.0, float(sum_insured))
    wind_kmh = max(0.0, float(wind_kmh))
    rain_48h_mm = max(0.0, float(rain_48h_mm))
    wind_kt = wind_kmh / KT_TO_KMH

    if wind_kt >= 110:
        wind_pct = 100
        wind_trigger = "Wind ≥ 110 kt"
    elif wind_kt >= 90:
        wind_pct = 50
        wind_trigger = "Wind ≥ 90 kt"
    elif wind_kt >= 64:
        wind_pct = 25
        wind_trigger = "Wind ≥ 64 kt"
    else:
        wind_pct = 0
        wind_trigger = "No wind trigger"

    rain_addon = 20 if rain_48h_mm >= 200 else 0
    payout_pct = min(100, wind_pct + rain_addon)
    payout_amount = sum_insured * payout_pct / 100.0

    trigger_text = wind_trigger
    if rain_addon:
        trigger_text += " + Rain ≥ 200 mm / 48h"
    elif wind_pct == 0:
        trigger_text = "No trigger reached"

    return ParametricPayout(
        sum_insured=sum_insured,
        wind_kmh=wind_kmh,
        wind_kt=wind_kt,
        rain_48h_mm=rain_48h_mm,
        wind_payout_pct=wind_pct,
        rain_addon_pct=rain_addon,
        payout_pct=payout_pct,
        payout_amount=payout_amount,
        trigger_text=trigger_text,
    )
