from __future__ import annotations

import json
from io import BytesIO

import requests
from PIL import Image

class EarthEngineService:
    def __init__(self, settings):
        self.settings = settings
        self.available = False
        self.ee = None
        self._init()

    def _init(self):
        try:
            import ee
            if self.settings.gee_credentials_json:
                from google.oauth2 import service_account
                info = json.loads(self.settings.gee_credentials_json)
                creds = service_account.Credentials.from_service_account_info(
                    info, scopes=["https://www.googleapis.com/auth/earthengine"]
                )
                ee.Initialize(credentials=creds, project=self.settings.gee_project_id)
            elif self.settings.gee_project_id:
                ee.Initialize(project=self.settings.gee_project_id)
            else:
                return
            self.ee = ee
            # Lightweight connectivity check.
            _ = ee.Number(1).getInfo()
            self.available = True
        except Exception:
            self.available = False

    def satellite_thumbnail(self, lat: float, lon: float):
        if not self.available:
            return None
        try:
            ee = self.ee
            point = ee.Geometry.Point([lon, lat])
            region = point.buffer(22_000).bounds()
            image = (
                ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
                .filterBounds(region)
                .filterDate(ee.Date.now().advance(-45, "day"), ee.Date.now())
                .filter(ee.Filter.lte("CLOUDY_PIXEL_PERCENTAGE", 45))
                .sort("CLOUDY_PIXEL_PERCENTAGE")
                .first()
            )
            if image is None:
                return None
            url = image.getThumbURL({
                "region": region,
                "dimensions": 1100,
                "format": "png",
                "bands": ["B4", "B3", "B2"],
                "min": 200,
                "max": 3200,
                "gamma": 1.25,
            })
            r = requests.get(url, timeout=20)
            r.raise_for_status()
            return Image.open(BytesIO(r.content)).convert("RGB")
        except Exception:
            return None
