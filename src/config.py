from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

APP_TITLE = "EarlyShield AI"
DEMO_DISTRICT = "Visakhapatnam"
GOOGLE_AI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.7-flash")

@dataclass(frozen=True)
class Settings:
    gemini_api_key: str | None
    google_cloud_project: str | None
    google_cloud_location: str
    gee_project_id: str | None
    gee_credentials_json: str | None
    alert_webhook_url: str | None
    demo_mode: bool


def _bridge_streamlit_secrets() -> None:
    """Copy common Streamlit secrets into environment variables once."""
    try:
        import streamlit as st
        mapping = {
            "GEMINI_API_KEY": "GEMINI_API_KEY",
            "GOOGLE_CLOUD_PROJECT": "GOOGLE_CLOUD_PROJECT",
            "GOOGLE_CLOUD_LOCATION": "GOOGLE_CLOUD_LOCATION",
            "GEE_PROJECT_ID": "GEE_PROJECT_ID",
            "GEE_CREDENTIALS_JSON": "GEE_CREDENTIALS_JSON",
            "ALERT_WEBHOOK_URL": "ALERT_WEBHOOK_URL",
            "GEMINI_MODEL": "GEMINI_MODEL",
        }
        for secret_key, env_key in mapping.items():
            if env_key not in os.environ:
                try:
                    value = st.secrets.get(secret_key)
                except Exception:
                    value = None
                if value:
                    os.environ[env_key] = str(value)
    except Exception:
        pass


def load_settings() -> Settings:
    _bridge_streamlit_secrets()
    return Settings(
        gemini_api_key=os.getenv("GEMINI_API_KEY") or None,
        google_cloud_project=os.getenv("GOOGLE_CLOUD_PROJECT") or None,
        google_cloud_location=os.getenv("GOOGLE_CLOUD_LOCATION", "global"),
        gee_project_id=os.getenv("GEE_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT") or None,
        gee_credentials_json=os.getenv("GEE_CREDENTIALS_JSON") or None,
        alert_webhook_url=os.getenv("ALERT_WEBHOOK_URL") or None,
        demo_mode=os.getenv("EARLYSHIELD_DEMO_MODE", "true").lower() == "true",
    )
