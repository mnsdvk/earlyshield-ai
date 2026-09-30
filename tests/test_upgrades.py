from src.cap import build_cap_style_alert, cap_filename
from src.insurance import calculate_parametric_payout


def _forecast():
    return {
        "district": "Visakhapatnam",
        "state": "Andhra Pradesh",
        "lat": 17.6868,
        "lon": 83.2185,
        "risk_score": 78.5,
        "risk_level": "SEVERE",
        "local_wind_kmh": 180,
        "local_rain_mm": 260,
        "surge_m": 2.1,
    }


def test_parametric_payout_caps_at_100_percent():
    result = calculate_parametric_payout(5_000_000, 210, 250)
    assert result.payout_pct == 100
    assert result.payout_amount == 5_000_000


def test_parametric_payout_uses_rain_addon():
    result = calculate_parametric_payout(1_000_000, 130, 220)
    assert result.wind_payout_pct == 25
    assert result.rain_addon_pct == 20
    assert result.payout_pct == 45
    assert result.payout_amount == 450_000


def test_cap_style_alert_has_stable_identifier_and_unicode_safe_fields():
    alert = build_cap_style_alert(_forecast(), "తీర ప్రాంతాలు పర్యవేక్షించండి.", "Telugu")
    assert alert["identifier"].startswith("EARLYSHIELD-")
    assert alert["info"][0]["language"] == "te-IN"
    assert "తీర ప్రాంతాలు" in alert["info"][0]["instruction"]
    assert cap_filename(alert).endswith(".json")
