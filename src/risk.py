from __future__ import annotations

from math import exp, sqrt
import pandas as pd


def haversine_km(lat1, lon1, lat2, lon2):
    from math import radians, sin, cos, asin
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return 2 * R * asin(sqrt(a))


def _risk_level(score: float) -> str:
    if score >= 80: return "EXTREME"
    if score >= 65: return "SEVERE"
    if score >= 45: return "HIGH"
    if score >= 25: return "MODERATE"
    return "LOW"


def build_forecast(*, district, wind_kmh, rainfall_mm, central_pressure_hpa, live_weather, infrastructure):
    lat, lon = float(district["lat"]), float(district["lon"])
    coastal_km = float(district["coast_km"])
    elevation = float(district["elevation_m"])

    # Transparent screening equations. They are intentionally not presented as an official NWP/cyclone model.
    local_wind = wind_kmh * exp(-coastal_km / 190.0)
    local_rain = rainfall_mm * exp(-coastal_km / 330.0)
    pressure_term = max(0.0, 1005.0 - central_pressure_hpa) / 55.0
    surge = max(0.2, 0.45 + 0.014 * max(local_wind - 75.0, 0.0) + 0.35 * pressure_term) * max(0.55, 1.15 - elevation / 40.0)

    hazard_wind = min(1.0, max(0.0, local_wind - 60.0) / 120.0)
    hazard_rain = min(1.0, max(0.0, local_rain - 70.0) / 330.0)
    hazard_surge = min(1.0, surge / 3.5)
    hazard = 0.46 * hazard_wind + 0.30 * hazard_rain + 0.24 * hazard_surge

    assets = infrastructure.copy()
    assets["distance_km"] = assets.apply(lambda r: haversine_km(lat, lon, r["lat"], r["lon"]), axis=1)
    # Focus the operational view on the selected district and immediate response catchment.
    local_assets = assets[assets["distance_km"] <= 90].copy()
    if len(local_assets) < 6:
        local_assets = assets.sort_values("distance_km").head(12).copy()
    assets = local_assets
    assets["wind_h"] = local_wind * (0.35 + 0.65 * assets["distance_km"].map(lambda d: exp(-d / 55.0)))
    assets["rain_h"] = local_rain * (0.30 + 0.70 * assets["distance_km"].map(lambda d: exp(-d / 70.0)))
    assets["surge_h"] = surge * (0.25 + 0.75 * assets["distance_km"].map(lambda d: exp(-d / 45.0)))
    assets["wind_component"] = (assets["wind_h"].clip(lower=0) / 180.0).clip(upper=1)
    assets["rain_component"] = ((assets["rain_h"] - 50) / 350.0).clip(lower=0, upper=1)
    assets["surge_component"] = (assets["surge_h"] / 3.5).clip(upper=1)
    assets["hazard"] = 0.46*assets["wind_component"] + 0.30*assets["rain_component"] + 0.24*assets["surge_component"]
    assets["risk"] = (100 * assets["hazard"] * assets["criticality"] * assets["fragility"]).clip(0, 100)

    pathway = []
    for kind, series, threshold, name, description in [
        ("wind", assets["wind_h"], 110, "Wind / grid pathway", "High winds can interrupt feeders, substations, roofs and road clearance operations."),
        ("rain", assets["rain_h"], 140, "Rainfall / access pathway", "Short-duration intense rain can isolate arterial roads and delay access to shelters and hospitals."),
        ("surge", assets["surge_h"], 1.5, "Surge / coastal pathway", "Low-lying assets face coastal inundation and difficult last-mile access during peak tide and surge."),
    ]:
        severity = "Severe" if float(series.max()) >= threshold*1.25 else ("High" if float(series.max()) >= threshold else "Moderate")
        pathway.append({"name": name, "severity": severity, "description": description})

    priority_types = {
        "power_substation": "Pre-position restoration crews and isolate flood-prone equipment.",
        "hospital": "Secure backup power, oxygen/cold-chain capacity and access routes.",
        "shelter": "Stage water, lighting, communications and accessible transport before road degradation.",
        "arterial_road": "Inspect culverts, clear drainage hotspots and stage debris-removal crews.",
    }
    ranked = assets.sort_values("risk", ascending=False).head(6)
    actions = []
    for typ in ranked["type"].tolist():
        if typ in priority_types and priority_types[typ] not in actions:
            actions.append(priority_types[typ])
        if len(actions) >= 4:
            break
    if not actions:
        actions = ["Validate exposed assets against municipal GIS and official advisory bulletins before operational action."]

    score = float(min(100, 100 * hazard * (0.78 + 0.18 * float(assets["criticality"].mean()))))
    affected = int((assets["risk"] >= 45).sum())
    critical = int((assets["type"].isin(["hospital", "power_substation", "shelter"]) & (assets["risk"] >= 45)).sum())
    exposed_people = int(sum(assets.loc[assets["risk"] >= 45, "population_exposed"]))

    color_map = []
    for x in assets["risk"]:
        if x >= 80: color_map.append([220, 62, 66, 220])
        elif x >= 65: color_map.append([240, 132, 62, 220])
        elif x >= 45: color_map.append([245, 201, 83, 220])
        else: color_map.append([99, 196, 139, 220])
    assets["risk_color"] = color_map

    drivers = [
        {"title": "Wind loading", "detail": f"Scenario wind attenuates to ~{local_wind:.0f} km/h at this district boundary."},
        {"title": "Rainfall loading", "detail": f"The 24-hour rainfall scenario contributes ~{local_rain:.0f} mm after a simple coastal-distance attenuation."},
        {"title": "Surge sensitivity", "detail": f"Estimated screening surge is ~{surge:.1f} m and is amplified for lower-elevation locations."},
        {"title": "Exposure", "detail": f"{affected} catalogued assets cross the high-risk threshold, affecting roughly {exposed_people:,} people in the demo exposure model."},
    ]

    return {
        "district": district["district"],
        "state": district["state"],
        "lat": lat,
        "lon": lon,
        "risk_score": score,
        "risk_level": _risk_level(score),
        "local_wind_kmh": local_wind,
        "local_rain_mm": local_rain,
        "surge_m": surge,
        "central_pressure_hpa": central_pressure_hpa,
        "coastal_km": coastal_km,
        "elevation_m": elevation,
        "critical_assets": critical,
        "affected_assets": affected,
        "exposed_people": exposed_people,
        "drivers": drivers,
        "actions": actions,
        "pathways": pathway,
        "infrastructure": assets,
        "live_weather_time": live_weather.get("time", "unknown"),
        "live_weather": live_weather,
    }


def infrastructure_impacts(forecast):
    return forecast["infrastructure"].sort_values("risk", ascending=False)
