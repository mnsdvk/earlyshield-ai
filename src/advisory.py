from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1]
OUTBOX = ROOT / "outbox"
OUTBOX.mkdir(exist_ok=True)


def build_fallback_advisory(forecast, language):
    district = forecast["district"]
    score = forecast["risk_score"]
    wind = forecast["local_wind_kmh"]
    rain = forecast["local_rain_mm"]
    surge = forecast["surge_m"]

    if language == "Telugu":
        return (f"{district} కోసం EarlyShield AI స్క్రీనింగ్: ప్రమాద స్కోరు {score:.0f}/100. "
                f"స్థానిక గాలి సుమారు {wind:.0f} km/h, 24 గంటల వర్షపాతం సన్నివేశం {rain:.0f} mm, తుఫాను అలల అంచనా {surge:.1f} m. "
                "విద్యుత్, ఆసుపత్రులు, షెల్టర్లు మరియు ప్రధాన రహదారులపై ముందస్తు తనిఖీలు చేయండి. "
                "బ్యాకప్ పవర్, కమ్యూనికేషన్, నీరు మరియు అత్యవసర సామగ్రిని సిద్ధంగా ఉంచండి. "
                "తీర ప్రాంతాల్లో ప్రభావిత మార్గాలను పర్యవేక్షించండి. ఇది నిర్ణయ సహాయక ప్రోటోటైప్ మాత్రమే; అధికారిక IMD/NDMA మరియు జిల్లా అధికారుల హెచ్చరికలే తుది మార్గదర్శకం.")
    if language == "Hindi":
        return (f"{district} के लिए EarlyShield AI स्क्रीनिंग: जोखिम स्कोर {score:.0f}/100। "
                f"स्थानीय पवन लगभग {wind:.0f} km/h, 24 घंटे की वर्षा परिदृश्य {rain:.0f} mm और स्क्रीनिंग तूफानी ज्वार {surge:.1f} m है। "
                "बिजली, अस्पताल, आश्रय केंद्र और मुख्य सड़कों की अग्रिम जांच करें। बैकअप पावर, संचार, पानी और आपात सामग्री तैयार रखें। "
                "तटीय मार्गों और निचले इलाकों की निगरानी बढ़ाएं। यह केवल निर्णय-सहायक प्रोटोटाइप है; आधिकारिक IMD/NDMA और जिला प्रशासन के निर्देश सर्वोपरि हैं।")
    return (f"EARLYSHIELD ADVISORY — {district}\n"
            f"Screening risk: {score:.0f}/100 | Local wind: ~{wind:.0f} km/h | 24h rain scenario: ~{rain:.0f} mm | Screening surge: ~{surge:.1f} m.\n\n"
            "Priorities: inspect power and critical facilities; stage backup power, communications and water; protect shelter access; monitor low-lying roads and drainage hotspots.\n\n"
            "This is a decision-support prototype, not an official warning. Follow official IMD/NDMA and district administration instructions for operational decisions.")


def dispatch_advisory(advisory: str, forecast: dict, settings):
    payload = {
        "system": "EarlyShield AI",
        "district": forecast["district"],
        "state": forecast["state"],
        "risk_score": round(forecast["risk_score"], 1),
        "risk_level": forecast["risk_level"],
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "advisory": advisory,
    }
    if settings.alert_webhook_url:
        try:
            r = requests.post(settings.alert_webhook_url, json=payload, timeout=10)
            r.raise_for_status()
            return {"sent": True, "message": "Advisory posted to the configured municipal webhook."}
        except Exception as exc:
            return {"sent": False, "message": f"Webhook delivery failed ({type(exc).__name__}); the advisory was not treated as dispatched."}

    path = OUTBOX / f"dispatch_{forecast['district'].lower().replace(' ', '_')}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"sent": True, "message": f"Demo dispatch recorded locally at {path.name}. Configure ALERT_WEBHOOK_URL for live delivery."}
