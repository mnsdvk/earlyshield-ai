from __future__ import annotations

from datetime import datetime, timezone


def _cap_language(language: str) -> str:
    return {
        "English": "en-IN",
        "Telugu": "te-IN",
        "Hindi": "hi-IN",
    }.get(language, "en-IN")


def build_cap_style_alert(forecast: dict, advisory: str, language: str) -> dict:
    """Build a CAP-style JSON mapping for hackathon/demo integrations.

    OASIS CAP 1.2 is an XML standard. This JSON object mirrors the core CAP
    alert/info fields for an easy machine-readable export; strict CAP 1.2
    interoperability would require XML serialization/validation.
    """
    now = datetime.now(timezone.utc)
    severity = forecast.get("risk_level", "HIGH")
    if severity == "EXTREME":
        cap_severity = "Extreme"
    elif severity == "SEVERE":
        cap_severity = "Severe"
    elif severity == "HIGH":
        cap_severity = "Moderate"
    else:
        cap_severity = "Minor"

    risk_score = float(forecast.get("risk_score", 0))
    urgency = "Immediate" if risk_score >= 80 else "Expected"
    certainty = "Likely"
    district = forecast.get("district", "Unknown district")
    state = forecast.get("state", "Unknown state")
    lat = float(forecast.get("lat", 0))
    lon = float(forecast.get("lon", 0))

    identifier = f"EARLYSHIELD-{now.astimezone().strftime('%Y%m%d%H%M')}"
    return {
        "identifier": identifier,
        "sender": "earlyshield.ai",
        "sent": now.isoformat(),
        "status": "Actual",
        "msgType": "Alert",
        "scope": "Restricted",
        "format": "CAP-style JSON",
        "format_note": "Core OASIS CAP 1.2 fields represented in JSON for prototype integration; strict CAP 1.2 exchange uses XML.",
        "info": [
            {
                "language": _cap_language(language),
                "category": ["Met"],
                "event": "Tropical Cyclone",
                "urgency": urgency,
                "severity": cap_severity,
                "certainty": certainty,
                "senderName": "EarlyShield AI",
                "headline": f"EarlyShield alert — {district}, {state}",
                "description": (
                    f"Screening risk {risk_score:.0f}/100; local wind ~{forecast.get('local_wind_kmh', 0):.0f} km/h; "
                    f"24h rainfall scenario ~{forecast.get('local_rain_mm', 0):.0f} mm; "
                    f"screening surge ~{forecast.get('surge_m', 0):.1f} m."
                ),
                "instruction": advisory,
                "area": [
                    {
                        "areaDesc": f"{district}, {state}",
                        "circle": f"{lat:.5f},{lon:.5f} 60",
                    }
                ],
            }
        ],
    }


def cap_filename(alert: dict) -> str:
    identifier = str(alert.get("identifier", "EARLYSHIELD-ALERT"))
    return f"{identifier}.json"
