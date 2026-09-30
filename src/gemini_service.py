from __future__ import annotations

import json
from io import BytesIO

from PIL import Image

from src.config import GOOGLE_AI_MODEL
import os

class GeminiService:
    def __init__(self, settings):
        self.settings = settings
        self.model = os.getenv("GEMINI_MODEL", GOOGLE_AI_MODEL)
        self.available = False
        self.client = None
        self.last_error = None
        try:
            from google import genai
            if settings.gemini_api_key:
                self.client = genai.Client(api_key=settings.gemini_api_key)
            elif settings.google_cloud_project:
                self.client = genai.Client(
                    vertexai=True,
                    project=settings.google_cloud_project,
                    location=settings.google_cloud_location,
                )
            self.available = self.client is not None
        except Exception as exc:
            self.available = False
            self.last_error = f"{type(exc).__name__}: {exc}"

    def _prompt_context(self, forecast: dict) -> str:
        assets = forecast["infrastructure"].sort_values("risk", ascending=False).head(8)
        asset_rows = assets[["name", "type", "risk", "distance_km", "elevation_m", "pathway"]].to_dict("records") if "pathway" in assets.columns else assets[["name", "type", "risk", "distance_km", "elevation_m"]].to_dict("records")
        return json.dumps({
            "district": forecast["district"],
            "state": forecast["state"],
            "risk_score": round(forecast["risk_score"], 1),
            "risk_level": forecast["risk_level"],
            "local_wind_kmh": round(forecast["local_wind_kmh"], 1),
            "local_rain_mm": round(forecast["local_rain_mm"], 1),
            "surge_m": round(forecast["surge_m"], 2),
            "pressure_hpa": forecast["central_pressure_hpa"],
            "exposed_people": forecast["exposed_people"],
            "top_assets": asset_rows,
            "live_weather": forecast["live_weather"],
        }, ensure_ascii=False)

    def _call(self, prompt, image=None):
        if not self.available:
            return None
        try:
            contents = [prompt]
            if image is not None:
                buf = BytesIO()
                image.save(buf, format="PNG")
                from google.genai import types
                contents = [types.Part.from_bytes(data=buf.getvalue(), mime_type="image/png"), prompt]
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config={"max_output_tokens": 900},
            )
            return response.text
        except Exception as exc:
            self.last_error = f"{type(exc).__name__}: {exc}"
            return None

    def analyze_forecast(self, forecast, image):
        prompt = f"""
You are EarlyShield AI's emergency operations copilot. Review the supplied risk snapshot together with the structured scenario below.
Return a concise operator brief with exactly these sections:
## Situation
## Highest-risk infrastructure
## Damage pathways
## Next 3 anticipatory actions
## Evidence and uncertainty

Do not invent official warnings or casualty figures. Explicitly say this is a screening prototype and that official IMD/NDMA guidance governs real-world decisions.
Structured scenario JSON:
{self._prompt_context(forecast)}
"""
        return self._call(prompt, image=image)

    def ask(self, question, forecast, image):
        prompt = f"""
Answer the operator question using only the supplied scenario and the visible risk snapshot. Distinguish computed screening estimates from assumptions. Do not present the prototype as an official forecast.
Question: {question}
Scenario JSON:
{self._prompt_context(forecast)}
"""
        return self._call(prompt, image=image)

    def generate_advisory(self, forecast, language: str):
        prompt = f"""
Draft a municipal pre-landfall advisory for {forecast['district']}, {forecast['state']} in {language}.
Use plain public-facing language, 120-180 words, with:
- what may happen,
- critical preparation actions,
- infrastructure priorities,
- a clear statement that official government bulletins override this prototype.
Never fabricate an evacuation order, closure, shelter address, wind warning or casualty count.
Scenario: {self._prompt_context(forecast)}
"""
        return self._call(prompt)
