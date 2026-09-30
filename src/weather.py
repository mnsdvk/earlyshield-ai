from __future__ import annotations

from datetime import datetime, timezone
import requests

class OpenMeteoService:
    """Live weather adapter with a deterministic fallback."""
    URL = "https://api.open-meteo.com/v1/forecast"

    def fetch(self, lat: float, lon: float) -> dict:
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,wind_gusts_10m,precipitation,rain",
            "hourly": "precipitation",
            "forecast_days": 2,
            "timezone": "auto",
        }
        try:
            r = requests.get(self.URL, params=params, timeout=8)
            r.raise_for_status()
            data = r.json()
            current = data.get("current", {})
            hourly_rain = data.get("hourly", {}).get("precipitation", [])[:48]
            rain_48h_mm = float(sum(float(value or 0) for value in hourly_rain))
            return {
                "ok": True,
                "time": current.get("time", datetime.now(timezone.utc).isoformat()),
                "wind_kmh": float(current.get("wind_speed_10m") or 0),
                "gust_kmh": float(current.get("wind_gusts_10m") or 0),
                "rain_mm": float(current.get("rain") or current.get("precipitation") or 0),
                "rain_48h_mm": rain_48h_mm,
                "temperature_c": float(current.get("temperature_2m") or 0),
                "humidity": float(current.get("relative_humidity_2m") or 0),
                "source": "Open-Meteo",
            }
        except Exception as exc:
            return {
                "ok": False,
                "time": datetime.now(timezone.utc).isoformat(),
                "wind_kmh": 0.0,
                "gust_kmh": 0.0,
                "rain_mm": 0.0,
                "rain_48h_mm": 0.0,
                "temperature_c": 0.0,
                "humidity": 0.0,
                "source": f"fallback ({type(exc).__name__})",
            }
