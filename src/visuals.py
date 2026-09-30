from __future__ import annotations

from io import BytesIO
import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go
from PIL import Image


def build_pathway_chart(forecast):
    distances = np.linspace(0, 180, 60)
    wind = forecast["local_wind_kmh"] * np.exp(-distances / 55)
    rain = forecast["local_rain_mm"] * np.exp(-distances / 75)
    surge = forecast["surge_m"] * np.exp(-distances / 48)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=distances, y=wind, name="Wind (km/h)", mode="lines"))
    fig.add_trace(go.Scatter(x=distances, y=rain, name="Rain (mm)", mode="lines"))
    fig.add_trace(go.Scatter(x=distances, y=surge, name="Surge (m)", mode="lines"))
    fig.update_layout(height=420, margin=dict(l=10,r=10,t=25,b=10), template="plotly_dark", xaxis_title="Distance from highest-impact corridor (km)", yaxis_title="Relative intensity")
    return fig


def build_risk_map_image(forecast):
    assets = forecast["infrastructure"].copy()
    fig, ax = plt.subplots(figsize=(11, 6.6), dpi=150)
    # Shift to local coordinates for a legible operational snapshot.
    x = (assets["lon"] - forecast["lon"]) * 92 * np.cos(np.radians(forecast["lat"]))
    y = (assets["lat"] - forecast["lat"]) * 111
    sizes = 40 + assets["risk"] * 3.5
    ax.scatter(x, y, s=sizes, c=assets["risk"], cmap="turbo", vmin=0, vmax=100, alpha=0.88, edgecolor="white", linewidth=0.6)
    ax.scatter([0], [0], marker="*", s=300, c="black", edgecolor="white", linewidth=1.0, label="Target district")
    for _, r in assets.sort_values("risk", ascending=False).head(6).iterrows():
        xx = (r["lon"] - forecast["lon"]) * 92 * np.cos(np.radians(forecast["lat"]))
        yy = (r["lat"] - forecast["lat"]) * 111
        ax.annotate(r["name"], (xx, yy), xytext=(5,5), textcoords="offset points", fontsize=7)
    ax.set_title(f"EarlyShield AI — {forecast['district']} operational risk snapshot", loc="left", fontsize=15, weight="bold")
    ax.text(0, 0.98, f"Risk {forecast['risk_score']:.0f}/100 · {forecast['risk_level']} · wind {forecast['local_wind_kmh']:.0f} km/h · rain {forecast['local_rain_mm']:.0f} mm · surge {forecast['surge_m']:.1f} m", transform=ax.transAxes, va="top", fontsize=9)
    ax.set_xlabel("Approx. east-west offset (km)")
    ax.set_ylabel("Approx. north-south offset (km)")
    ax.grid(alpha=0.18)
    ax.legend(loc="lower right")
    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert("RGB")


def build_multimodal_snapshot(risk_image, satellite_image):
    """Create one legible evidence board so Gemini receives both model output and satellite context."""
    left = risk_image.convert("RGB")
    right = satellite_image.convert("RGB")
    target_h = max(left.height, right.height)
    left = left.resize((int(left.width * target_h / left.height), target_h))
    right = right.resize((int(right.width * target_h / right.height), target_h))
    board = Image.new("RGB", (left.width + right.width, target_h), "white")
    board.paste(left, (0, 0))
    board.paste(right, (left.width, 0))
    return board
