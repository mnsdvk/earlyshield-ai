from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pydeck as pdk
import streamlit as st

from src.config import APP_TITLE, DEMO_DISTRICT, GOOGLE_AI_MODEL, load_settings
from src.data import district_catalog, infrastructure_catalog
from src.gemini_service import GeminiService
from src.gee_service import EarthEngineService
from src.risk import build_forecast, infrastructure_impacts
from src.visuals import build_risk_map_image, build_pathway_chart, build_multimodal_snapshot
from src.weather import OpenMeteoService
from src.advisory import build_fallback_advisory, dispatch_advisory
from src.insurance import calculate_parametric_payout
from src.cap import build_cap_style_alert, cap_filename

ROOT = Path(__file__).resolve().parent

st.set_page_config(page_title=APP_TITLE, page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")

settings = load_settings()

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=JetBrains+Mono:wght@600;800&display=swap');
    /* EarlyShield mission-control theme: presentation-only styling. */
    html, body, .stApp, [data-testid="stSidebar"] { font-family:'Inter',system-ui,'Segoe UI',sans-serif; }
    .stApp { color:#e6f1f8;
      background:radial-gradient(1100px 520px at 88% -8%,rgba(34,211,238,.16),transparent 60%),
                 radial-gradient(800px 480px at -8% 6%,rgba(251,191,36,.07),transparent 60%),#060d18; }
    div[data-testid="stMarkdownContainer"] { color:#dbe9f4; }
    .stApp h2,.stApp h3,.stApp h4 { color:#f1f8fd !important; font-weight:800; letter-spacing:-.02em; }
    [data-testid="stWidgetLabel"] *, label { color:#cfe0ee !important; }
    [data-testid="stCaptionContainer"], .stCaption { color:#8fa6ba !important; }
    .block-container { max-width:1480px; padding-top:2.4rem; padding-bottom:2.5rem; }
    /* header + sidebar toggle: always visible */
    [data-testid="stHeader"] { background:rgba(6,13,24,.72); backdrop-filter:blur(10px); border-bottom:1px solid rgba(255,255,255,.06); }
    [data-testid="stHeader"] *, [data-testid="stToolbar"] *, [data-testid="stExpandSidebarButton"] *,
    [data-testid="stSidebarCollapseButton"] *, [data-testid="collapsedControl"] * { color:#e6f1f8 !important; fill:#e6f1f8 !important; }
    [data-testid="stExpandSidebarButton"], [data-testid="collapsedControl"], [data-testid="stSidebarCollapseButton"] button {
      background:rgba(34,211,238,.16) !important; border:1px solid rgba(34,211,238,.55) !important; border-radius:10px !important; }
    /* hero */
    .hero { position:relative; overflow:hidden; padding:1.7rem 1.9rem 1.5rem; border-radius:24px; margin-bottom:1.1rem;
      border:1px solid rgba(34,211,238,.22);
      background:linear-gradient(135deg,rgba(9,30,52,.95),rgba(8,58,82,.92) 55%,rgba(10,96,110,.9));
      box-shadow:0 0 0 1px rgba(255,255,255,.03) inset,0 24px 60px rgba(0,0,0,.45),0 0 60px rgba(34,211,238,.10); }
    .hero:before { content:""; position:absolute; inset:0; opacity:.5; pointer-events:none;
      background-image:linear-gradient(rgba(255,255,255,.04) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.04) 1px,transparent 1px);
      background-size:34px 34px; mask-image:linear-gradient(90deg,transparent,#000 70%); }
    .hero:after { content:""; position:absolute; width:340px; height:340px; right:-90px; top:-140px; border-radius:50%;
      background:radial-gradient(circle,rgba(34,211,238,.35),transparent 65%); }
    .hero-content { position:relative; z-index:2; max-width:1000px; }
    .hero-kicker { font-size:.74rem; font-weight:800; letter-spacing:.16em; text-transform:uppercase; color:#67e8f9; margin-bottom:.6rem; }
    .hero h1 { margin:0; font-size:clamp(2.1rem,3.8vw,3.3rem); line-height:1.04; letter-spacing:-.045em; font-weight:800; }
    .hero h1 .grad { background:linear-gradient(90deg,#fff 10%,#7ee7f0 55%,#fcd34d); -webkit-background-clip:text; background-clip:text; color:transparent; -webkit-text-fill-color:transparent; }
    .hero p { margin:.7rem 0 0; max-width:880px; color:#c4d9e8; font-size:1.02rem; line-height:1.55; }
    .hero-status { margin-top:1rem; display:flex; gap:.45rem; flex-wrap:wrap; }
    .badge { display:inline-flex; align-items:center; padding:.34rem .7rem; border-radius:999px; font-size:.7rem; font-weight:800; letter-spacing:.04em;
      border:1px solid rgba(255,255,255,.16); background:rgba(255,255,255,.07); color:#e6f4ff; }
    .badge-live { border-color:rgba(52,211,153,.5); background:rgba(52,211,153,.14); color:#6ee7b7; }
    .pulse { width:8px; height:8px; border-radius:50%; background:#34d399; display:inline-block; margin-right:.5rem; animation:es-pulse 1.6s infinite; }
    @keyframes es-pulse { 0%{box-shadow:0 0 0 0 rgba(52,211,153,.7)} 70%{box-shadow:0 0 0 9px rgba(52,211,153,0)} 100%{box-shadow:0 0 0 0 rgba(52,211,153,0)} }
    .hero-flow { margin-top:1.1rem; display:flex; gap:.5rem; flex-wrap:wrap; align-items:center; font-size:.78rem; font-weight:700; }
    .hero-flow .step { padding:.35rem .75rem; border-radius:10px; background:rgba(3,12,22,.55); border:1px solid rgba(103,232,249,.25); color:#cdf4fa; }
    .hero-flow .arrow { color:#fbbf24; font-weight:800; }
    /* risk banner */
    .alert-banner { display:flex; align-items:center; flex-wrap:wrap; gap:.4rem; padding:.9rem 1.2rem; border-radius:16px; margin:.1rem 0 1rem;
      background:linear-gradient(90deg,color-mix(in srgb,var(--c) 22%,#0a1424),#0a1424 75%);
      border:1px solid color-mix(in srgb,var(--c) 45%,transparent); border-left:7px solid var(--c);
      color:#eaf4fb; font-size:.96rem; box-shadow:0 10px 30px rgba(0,0,0,.35),0 0 28px color-mix(in srgb,var(--c) 18%,transparent); }
    .alert-banner .pulse { background:var(--c); animation:none; box-shadow:0 0 0 4px color-mix(in srgb,var(--c) 30%,transparent); }
    .alert-banner b.lvl { color:var(--c); letter-spacing:.08em; }
    /* KPI cards */
    .metric-card { position:relative; min-height:108px; padding:1rem 1.05rem; border-radius:18px; overflow:hidden;
      background:linear-gradient(160deg,rgba(255,255,255,.075),rgba(255,255,255,.025)); border:1px solid rgba(255,255,255,.10);
      border-top:3px solid #22d3ee; box-shadow:0 12px 30px rgba(0,0,0,.35); backdrop-filter:blur(8px); transition:transform .18s, box-shadow .18s; }
    .metric-card:hover { transform:translateY(-4px); box-shadow:0 18px 40px rgba(0,0,0,.5),0 0 28px rgba(34,211,238,.14); }
    .metric-label { color:#8fb0c6; font-size:.7rem; font-weight:800; text-transform:uppercase; letter-spacing:.09em; }
    .metric-value { color:#fff; font-family:'JetBrains Mono','Inter',monospace; font-size:1.6rem; font-weight:800; margin-top:.3rem; line-height:1.1; }
    .metric-sub { color:#8fa6ba; font-size:.76rem; margin-top:.35rem; }
    .section { margin-top:1.1rem; } .tiny { color:#7f96aa; font-size:.76rem; }
    /* tabs */
    .stTabs [data-baseweb="tab-list"] { gap:.4rem; border-bottom:1px solid rgba(255,255,255,.09); padding:.2rem .1rem 0; }
    .stTabs [data-baseweb="tab"] { height:2.7rem; padding:0 1rem; border-radius:12px 12px 0 0; font-weight:700; }
    .stTabs [data-baseweb="tab"] p { color:#8fa6ba !important; }
    .stTabs [aria-selected="true"] { background:rgba(34,211,238,.13) !important; }
    .stTabs [aria-selected="true"] p { color:#67e8f9 !important; }
    .stTabs [data-baseweb="tab-highlight"] { background:#22d3ee !important; }
    /* buttons */
    [data-testid="stBaseButton-primary"], .stButton > button[kind="primary"] { border:0 !important; color:#04121d !important; font-weight:800;
      background:linear-gradient(90deg,#22d3ee,#34d399) !important; box-shadow:0 8px 22px rgba(34,211,238,.28); transition:transform .15s, filter .15s; }
    [data-testid="stBaseButton-primary"] p { color:#04121d !important; }
    [data-testid="stBaseButton-primary"]:hover { transform:translateY(-1px); filter:brightness(1.08); }
    [data-testid="stBaseButton-secondary"] { background:rgba(255,255,255,.06) !important; border:1px solid rgba(255,255,255,.2) !important; color:#e6f1f8 !important; }
    [data-testid="stBaseButton-secondary"] p { color:#e6f1f8 !important; }
    /* inputs */
    input, textarea, [data-baseweb="select"] > div, [data-baseweb="input"], [data-baseweb="textarea"] {
      background:rgba(255,255,255,.055) !important; color:#fff !important; border-color:rgba(255,255,255,.16) !important; }
    [data-baseweb="popover"] ul, [data-baseweb="menu"] { background:#0b1626 !important; }
    [data-baseweb="popover"] li { color:#e6f1f8 !important; }
    [data-baseweb="slider"] [role="slider"] { background:#22d3ee !important; box-shadow:0 0 0 4px rgba(34,211,238,.25); }
    /* sidebar */
    [data-testid="stSidebar"] { background:linear-gradient(180deg,#040a13,#071426); border-right:1px solid rgba(34,211,238,.14); }
    [data-testid="stSidebar"] * { color:#dbe9f4; }
    [data-testid="stSidebar"] svg { fill:#cfe6f3; }
    /* misc surfaces */
    .stAlert, [data-testid="stAlertContainer"] { background:rgba(34,211,238,.08) !important; border:1px solid rgba(34,211,238,.25); border-radius:14px; }
    .stAlert *, [data-testid="stAlertContainer"] * { color:#e6f1f8 !important; }
    [data-testid="stExpander"] { border:1px solid rgba(255,255,255,.1) !important; border-radius:16px; background:rgba(255,255,255,.035); }
    [data-testid="stExpander"] summary * { color:#e6f1f8 !important; }
    [data-testid="stJson"] { background:rgba(255,255,255,.04); border-radius:12px; padding:.6rem; } [data-testid="stJson"] * { color:#cfe6f3 !important; }
    table { color:#e6f1f8 !important; } th, td { border-color:rgba(255,255,255,.1) !important; } thead th { background:rgba(255,255,255,.07) !important; }
    div[data-testid="stMetric"] { background:rgba(255,255,255,.05); border:1px solid rgba(255,255,255,.1); padding:.6rem .8rem; border-radius:14px; }
    hr { border-color:rgba(255,255,255,.1) !important; }
    [data-testid="stDeckGlJsonChart"], .stPlotlyChart, [data-testid="stImage"] img {
      border-radius:18px; overflow:hidden; border:1px solid rgba(34,211,238,.18); box-shadow:0 14px 36px rgba(0,0,0,.45); }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- header ----------
st.markdown(
    f"""
    <div class='hero'>
      <div class='hero-content'>
        <div class='hero-kicker'>INDIA CLIMATE INTELLIGENCE · TRACK 5</div>
        <h1><span class='logo'>🛡️</span> <span class='grad'>{APP_TITLE}</span></h1>
        <p>Anticipate cyclone impact before landfall — translate weather and geospatial signals into infrastructure risk, explainable actions, and multilingual early-warning dispatch.</p>
        <div class='hero-status'>
          <span class='badge badge-live'><span class='pulse'></span>LIVE WEATHER</span>
          <span class='badge'>GOOGLE GEMINI</span>
          <span class='badge'>EARTH ENGINE READY</span>
          <span class='badge'>INDIA-SCALE DESIGN</span>
        </div>
        <div class='hero-flow'><span class='step'>🛰️ Signal</span><span class='arrow'>→</span><span class='step'>📊 Risk model</span><span class='arrow'>→</span><span class='step'>🧠 Gemini reasoning</span><span class='arrow'>→</span><span class='step'>📣 Multilingual dispatch</span></div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------- services ----------
gemini = GeminiService(settings)
weather = OpenMeteoService()
gee = EarthEngineService(settings)

# ---------- sidebar controls ----------
with st.sidebar:
    st.markdown("## 🛡️ Mission controls")
    st.caption("Scenario lab · decision-support prototype")
    districts = district_catalog()
    district_names = list(districts["district"])
    default_index = district_names.index(DEMO_DISTRICT) if DEMO_DISTRICT in district_names else 0
    selected_district = st.selectbox("Target district", district_names, index=default_index)
    district = districts.loc[districts["district"] == selected_district].iloc[0].to_dict()

    severity = st.select_slider("Cyclone scenario", options=["Watch", "Warning", "Severe", "Extreme"], value="Severe")
    default_wind = {"Watch": 90, "Warning": 115, "Severe": 145, "Extreme": 180}[severity]
    wind = st.slider("Max sustained wind (km/h)", 70, 220, default_wind, step=5)
    rain = st.slider("24-hour rainfall near landfall (mm)", 50, 500, {"Watch": 120, "Warning": 180, "Severe": 260, "Extreme": 380}[severity], step=10)
    pressure = st.slider("Central pressure (hPa)", 900, 1005, {"Watch": 995, "Warning": 985, "Severe": 970, "Extreme": 950}[severity], step=1)
    st.caption("Scenario inputs are screening parameters, not an official meteorological forecast.")

    st.divider()
    st.markdown("### 🔌 Data connectors")
    ai_status = "🟢 Connected" if gemini.available else "🟡 Ready — add key"
    gee_status = "🟢 Connected" if gee.available else "🔵 Demo mode"
    st.write(f"**Gemini:** {ai_status}")
    st.write(f"**Earth Engine:** {gee_status}")
    st.write("**Weather:** 🟢 Open-Meteo live")

    run = st.button("Run EarlyShield forecast", type="primary", use_container_width=True)

# ---------- state ----------
if "forecast" not in st.session_state or run:
    live = weather.fetch(district["lat"], district["lon"])
    forecast = build_forecast(
        district=district,
        wind_kmh=wind,
        rainfall_mm=rain,
        central_pressure_hpa=pressure,
        live_weather=live,
        infrastructure=infrastructure_catalog(),
    )
    st.session_state.forecast = forecast
    st.session_state.gemini_assessment = None
    st.session_state.advisory = None
    st.session_state.advisory_editor = ""
    # Prevent a previous district's satellite evidence from being reused.
    st.session_state.satellite_image = None

forecast = st.session_state.forecast

# ---------- risk banner (presentation only; reads existing forecast values) ----------
from html import escape
_score = float(forecast["risk_score"])
_lvl, _col = (("LOW", "#34d399") if _score < 25 else ("MODERATE", "#fbbf24") if _score < 50
              else ("HIGH", "#fb923c") if _score < 75 else ("CRITICAL", "#f43f5e"))
st.markdown(
    f"<div class='alert-banner' style='--c:{_col}'><span class='pulse'></span><b>{escape(str(selected_district))}</b>&nbsp;·&nbsp;"
    f"<b class='lvl'>{_lvl}</b>&nbsp;impact expected · risk {_score:.0f}/100 · "
    f"{forecast['critical_assets']} critical assets need pre-landfall action</div>",
    unsafe_allow_html=True,
)

# ---------- KPIs ----------
col1, col2, col3, col4, col5 = st.columns(5)
def metric(col, label, value, sub="", accent=None):
    _st = f" style='border-top-color:{accent}'" if accent else ""
    col.markdown(
        f"<div class='metric-card'{_st}><div class='metric-label'>{label}</div><div class='metric-value'>{value}</div><div class='metric-sub'>{sub}</div></div>",
        unsafe_allow_html=True,
    )

metric(col1, "District risk", f"{forecast['risk_score']:.0f}/100", forecast["risk_level"], accent=_col)
metric(col2, "Local wind", f"{forecast['local_wind_kmh']:.0f} km/h", "screening estimate")
metric(col3, "Rainfall", f"{forecast['local_rain_mm']:.0f} mm", "24-hour scenario")
metric(col4, "Storm surge", f"{forecast['surge_m']:.1f} m", "coastal screening estimate")
metric(col5, "Critical assets", f"{forecast['critical_assets']}", f"{forecast['affected_assets']} exposed assets")

st.markdown("<div class='section'></div>", unsafe_allow_html=True)

# ---------- tabs ----------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    ["Command center", "Impact pathways", "Satellite evidence", "Gemini copilot", "Advisory dispatch", "Method & sources"]
)

with tab1:
    left, right = st.columns([1.55, 1])
    with left:
        st.subheader("Infrastructure exposure map")
        assets = forecast["infrastructure"].copy()
        layer = pdk.Layer(
            "ScatterplotLayer",
            data=assets,
            get_position="[lon, lat]",
            get_radius=2600,
            get_fill_color="risk_color",
            get_line_color=[255, 255, 255],
            get_line_width=40,
            pickable=True,
            stroked=True,
            opacity=0.88,
        )
        district_layer = pdk.Layer(
            "ScatterplotLayer",
            data=pd.DataFrame([district]),
            get_position="[lon, lat]",
            get_radius=9000,
            get_fill_color=[255, 255, 255, 15],
            get_line_color=[255, 210, 90, 180],
            get_line_width=80,
            stroked=True,
        )
        view = pdk.ViewState(latitude=district["lat"], longitude=district["lon"], zoom=8.2)
        tooltip = {
            "html": "<b>{name}</b><br/>Type: {type}<br/>Risk: {risk:.0f}/100<br/>Pathway: {pathway}<br/>Elevation: {elevation_m} m",
            "style": {"backgroundColor": "#08131f", "color": "white"},
        }
        st.pydeck_chart(pdk.Deck(layers=[district_layer, layer], initial_view_state=view, tooltip=tooltip, map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"), use_container_width=True)
        st.caption("Infrastructure points are a realistic demo catalog with explicit provenance labels; swap in municipal asset GIS for a pilot.")

    with right:
        st.subheader("Why the district is at risk")
        for item in forecast["drivers"]:
            st.markdown(f"**{item['title']}** — {item['detail']}")
        st.markdown("### Priority actions")
        for action in forecast["actions"]:
            st.markdown(f"→ {action}")
        st.markdown("### Data freshness")
        st.markdown(f"<span class='tiny'>Weather pull: {forecast['live_weather_time']}</span>", unsafe_allow_html=True)

with tab2:
    st.subheader("Damage pathways: wind × rainfall × surge")
    c1, c2 = st.columns([1.2, 1])
    with c1:
        fig = build_pathway_chart(forecast)
        try:  # dark-theme the chart (UI only)
            fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              font=dict(color="#dbe9f4"))
        except Exception:
            pass
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown("#### Pathway logic")
        pathways = forecast["pathways"]
        for p in pathways:
            st.markdown(f"**{p['name']}** · {p['severity']}\n\n{p['description']}")
            st.divider()
        st.info("The screening engine intentionally separates hazard, exposure, and asset fragility so operators can see why a site is prioritized.")

with tab3:
    st.subheader("Google Earth Engine satellite context")
    if gee.available:
        with st.spinner("Querying a recent cloud-screened Sentinel-2 composite..."):
            try:
                satellite = gee.satellite_thumbnail(district["lat"], district["lon"])
                if satellite:
                    st.session_state.satellite_image = satellite
                    st.image(satellite, caption="Recent Sentinel-2 context from Google Earth Engine", use_container_width=True)
                    st.caption("Satellite context is an observational layer. It is not interpreted as a direct cyclone forecast.")
                else:
                    st.warning("Earth Engine returned no image for the selected date window.")
            except Exception as exc:
                st.session_state.satellite_image = None
                st.error(f"Earth Engine query failed: {type(exc).__name__}. The forecast and risk map remain available.")
    else:
        st.info("Earth Engine connector is in demo mode. Add GEE_PROJECT_ID plus authenticated Earth Engine credentials to activate live satellite imagery.")
        st.image(build_risk_map_image(forecast), caption="EarlyShield risk surface used for multimodal reasoning", use_container_width=True)

with tab4:
    st.subheader("Gemini multimodal incident copilot")
    risk_image = build_risk_map_image(forecast)
    satellite_image = st.session_state.get("satellite_image")
    st.image(risk_image, caption="Operational risk snapshot supplied to Gemini", use_container_width=True)
    if satellite_image is not None:
        st.image(satellite_image, caption="Earth Engine evidence available to the multimodal workflow", use_container_width=True)

    if st.button("Analyze this scenario with Gemini", type="primary"):
        with st.spinner(f"Gemini is reasoning over the risk snapshot + structured forecast ({GOOGLE_AI_MODEL})..."):
            try:
                multimodal_image = risk_image
                if satellite_image is not None:
                    multimodal_image = build_multimodal_snapshot(risk_image, satellite_image)
                st.session_state.gemini_assessment = gemini.analyze_forecast(forecast, multimodal_image)
            except Exception as exc:
                st.session_state.gemini_assessment = None
                st.error(f"Gemini analysis failed: {type(exc).__name__}. The deterministic forecast remains available.")
    if st.session_state.gemini_assessment:
        st.markdown(st.session_state.gemini_assessment)
    else:
        st.caption("The multimodal call will review the generated risk map and structured forecast together. This is where Google AI performs meaningful reasoning, not just copy generation.")

    st.markdown("#### Ask the copilot")
    question = st.text_input("Operator question", placeholder="Which infrastructure should be pre-positioned first, and why?")
    if question and st.button("Ask Gemini", key="ask_gemini"):
        with st.spinner("Gemini is preparing an evidence-linked answer..."):
            try:
                answer = gemini.ask(question, forecast, risk_image)
                if answer:
                    st.markdown(answer)
                else:
                    st.warning("Gemini is unavailable. Use the deterministic impact pathways and infrastructure priorities above.")
            except Exception as exc:
                st.error(f"Gemini request failed: {type(exc).__name__}. The deterministic forecast remains available.")

with tab5:
    st.subheader("Multilingual early-warning advisory")
    language = st.selectbox("Dispatch language", ["English", "Telugu", "Hindi"], index=1)
    if st.button("Generate advisory", type="primary"):
        with st.spinner("Generating advisory with Gemini..."):
            try:
                advisory = gemini.generate_advisory(forecast, language)
            except Exception as exc:
                st.warning(f"Gemini advisory generation failed ({type(exc).__name__}); using the deterministic advisory template.")
                advisory = None
        if not advisory:
            advisory = build_fallback_advisory(forecast, language)
        st.session_state.advisory = advisory
        st.session_state.advisory_editor = advisory

    if st.session_state.advisory:
        edited_advisory = st.text_area("Advisory preview — operator editable", key="advisory_editor", height=320)
        b1, b2 = st.columns(2)
        with b1:
            st.download_button(
                "Download advisory",
                edited_advisory,
                file_name=f"earlyshield_{selected_district.lower().replace(' ', '_')}_{language.lower()}.txt",
                mime="text/plain",
                use_container_width=True,
            )
        with b2:
            if st.button("Dispatch advisory", use_container_width=True):
                result = dispatch_advisory(edited_advisory, forecast, settings)
                if result["sent"]:
                    st.success(result["message"])
                else:
                    st.warning(result["message"])
        st.caption("Dispatch is designed for municipal integration: configure ALERT_WEBHOOK_URL for an actual outbound POST; otherwise the prototype writes a timestamped local dispatch record.")

        with st.expander("CAP-style alert export", expanded=False):
            cap_alert = build_cap_style_alert(forecast, edited_advisory, language)
            st.caption("Machine-readable alert envelope using core OASIS CAP 1.2 fields. Strict CAP 1.2 exchange is XML; this JSON form is intended for prototype/API integration.")
            st.download_button(
                "Download CAP-style alert JSON",
                data=json.dumps(cap_alert, ensure_ascii=False, indent=2),
                file_name=cap_filename(cap_alert),
                mime="application/json",
                use_container_width=True,
            )
            st.json(cap_alert)

        with st.expander("Parametric insurance liquidity stress-test", expanded=False):
            st.caption("Demonstration trigger schedule only — not an insurance product, pricing model, or underwriting recommendation.")
            insurance_sum = st.number_input(
                "Illustrative sum insured (₹)",
                min_value=10_000,
                max_value=100_000_000,
                value=5_000_000,
                step=50_000,
                key="insurance_sum_insured",
            )
            rain_48h = float(forecast.get("live_weather", {}).get("rain_48h_mm") or 0.0)
            rain_48h = st.number_input(
                "48-hour rainfall used for trigger (mm)",
                min_value=0.0,
                max_value=1000.0,
                value=round(rain_48h, 1),
                step=10.0,
                key="insurance_rain_48h",
                help="Prefilled from the live Open-Meteo 48-hour precipitation window when available; adjust for scenario stress-testing.",
            )
            payout = calculate_parametric_payout(
                insurance_sum,
                forecast["local_wind_kmh"],
                rain_48h,
            )
            i1, i2, i3 = st.columns(3)
            metric(i1, "Trigger wind", f"{payout.wind_kt:.0f} kt", f"{payout.wind_kmh:.0f} km/h")
            metric(i2, "Trigger payout", f"{payout.payout_pct}%", payout.trigger_text)
            metric(i3, "Indicated liquidity", f"₹{payout.payout_amount:,.0f}", "demonstration only")
            st.table(
                pd.DataFrame(
                    {
                        "Trigger": ["Wind ≥ 64 kt", "Wind ≥ 90 kt", "Wind ≥ 110 kt", "Rain ≥ 200 mm / 48h"],
                        "Effect": ["25%", "50%", "100%", "+20% add-on"],
                    }
                )
            )
    else:
        st.caption("Generate an operator-ready message for the selected district and language.")

with tab6:
    st.subheader("Architecture and guardrails")
    st.markdown(
        """
        **Signal → Model → Evidence → Action**

        1. **Live weather signal:** Open-Meteo current + short-range weather feed anchors the scenario to current local conditions.
        2. **Parametric risk engine:** a transparent screening model converts wind, rainfall, pressure, coastal distance, elevation, criticality and fragility into a 0–100 risk score.
        3. **Earth Engine evidence:** optional authenticated Google Earth Engine access fetches recent Sentinel-2 context for the target area.
        4. **Gemini multimodal reasoning:** Gemini sees the operational risk snapshot together with the structured forecast, identifies damage pathways, and drafts multilingual actions.
        5. **Dispatch:** advisories can be logged for a tabletop exercise or posted to a configured municipal webhook.

        **Safety boundary:** EarlyShield AI is a decision-support prototype, not an official cyclone warning system. Final evacuation, closure, relief and insurance decisions must use authoritative government forecasts and operational protocols.
        """
    )
    st.markdown("### Connector sources")
    st.write("• Google Gemini / Google AI: multimodal reasoning and advisory generation")
    st.write("• Google Earth Engine: satellite context")
    st.write("• Open-Meteo: live meteorological input adapter")
    st.write("• Demo infrastructure catalog: realistic synthetic asset records for reproducible evaluation")

# ---------- footer ----------
now = datetime.now(timezone.utc).astimezone()
st.markdown(f"<div class='tiny' style='text-align:center;margin-top:24px'>EarlyShield AI · Track 5 · prototype build · {now.strftime('%d %b %Y %H:%M %Z')}</div>", unsafe_allow_html=True)