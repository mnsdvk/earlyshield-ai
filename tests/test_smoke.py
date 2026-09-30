from src.data import district_catalog, infrastructure_catalog
from src.risk import build_forecast


def test_forecast_shape():
    districts = district_catalog()
    district = districts.iloc[0].to_dict()
    forecast = build_forecast(
        district=district,
        wind_kmh=145,
        rainfall_mm=260,
        central_pressure_hpa=970,
        live_weather={"time": "test"},
        infrastructure=infrastructure_catalog(),
    )
    assert 0 <= forecast["risk_score"] <= 100
    assert forecast["risk_level"] in {"LOW", "MODERATE", "HIGH", "SEVERE", "EXTREME"}
    assert len(forecast["infrastructure"]) > 10


def test_catalogs():
    assert "Visakhapatnam" in set(district_catalog()["district"])
    assert {"hospital", "shelter", "power_substation", "arterial_road"}.issubset(set(infrastructure_catalog()["type"]))
