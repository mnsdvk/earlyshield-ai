# EarlyShield AI
### Anticipatory Cyclone & Infrastructure Forecaster — Google Cloud Build with AI, Track 5

**One operational question:** *Where should a district act first, before a cyclone becomes a crisis?*

EarlyShield AI turns a cyclone scenario into an explainable district risk surface. It combines live meteorological context, a transparent parametric screening model, infrastructure exposure, optional Google Earth Engine satellite evidence, and Gemini multimodal reasoning to produce a prioritized action brief and multilingual advisory.

> **Important:** this is a hackathon decision-support prototype, not an official weather or evacuation warning system. Real-world actions must follow authoritative IMD/NDMA and local disaster-management protocols.

## What the prototype demonstrates

- **End-to-end workflow:** scenario → live weather pull → hazard/exposure model → infrastructure prioritization → risk visualization → Gemini multimodal analysis → advisory → dispatch.
- **Google AI is meaningful:** Gemini receives the generated operational risk snapshot as an image *plus* structured forecast data and reasons over both.
- **Geospatial intelligence:** district coordinates, infrastructure points, local distance attenuation, pathway modeling and an Earth Engine Sentinel-2 connector.
- **Infrastructure vulnerability:** separate wind, rainfall/access and surge pathways, plus criticality/fragility weighting.
- **India-first scale:** the demo catalog covers coastal districts across Andhra Pradesh, Odisha, West Bengal and Tamil Nadu; the data layer can be swapped for municipal GIS.
- **Multilingual operations:** English, Telugu and Hindi advisory generation.
- **Operational handoff:** CAP-style machine-readable JSON export for prototype alert integrations, plus an operator-editable advisory before dispatch.
- **Parametric liquidity stress-test:** illustrative wind/rain trigger calculator showing how objective triggers could release funds before loss adjustment. It is explicitly not an insurance product.
- **Deployability:** Streamlit app suitable for a hackathon live link; optional webhook integration provides a realistic dispatch boundary.

## Architecture

```text
                ┌──────────────────────────────┐
                │ Cyclone scenario controls    │
                │ wind / rain / pressure       │
                └──────────────┬───────────────┘
                               │
               ┌───────────────▼────────────────┐
               │ Live weather adapter            │
               │ Open-Meteo current conditions   │
               └───────────────┬────────────────┘
                               │
       ┌───────────────────────▼────────────────────────┐
       │ Transparent risk engine                         │
       │ hazard × exposure × criticality × fragility     │
       └───────────────┬───────────────┬────────────────┘
                       │               │
           ┌───────────▼───┐   ┌───────▼──────────────┐
           │ Infrastructure│   │ Google Earth Engine  │
           │ exposure layer │   │ Sentinel-2 context  │
           └───────────┬───┘   └───────┬──────────────┘
                       │               │
                       └───────┬───────┘
                               ▼
                    ┌─────────────────────┐
                    │ Gemini multimodal    │
                    │ operations copilot  │
                    └──────────┬──────────┘
                               ▼
                 ┌───────────────────────────┐
                 │ Multilingual advisory     │
                 │ + webhook / demo dispatch │
                 └───────────────────────────┘
```

## Local setup

### 1. Create a virtual environment

Windows PowerShell:

```powershell
cd earlyshield-ai
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Linux/macOS:

```bash
cd earlyshield-ai
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Activate Gemini

The easiest hackathon path is a Gemini API key. Create a `.env` file from `.env.example` and set:

```text
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-3.7-flash
```

The app also supports Vertex / Google Cloud mode:

```text
GOOGLE_CLOUD_PROJECT=your_project_id
GOOGLE_CLOUD_LOCATION=global
```

### 3. Activate Earth Engine

For local development, authenticate Earth Engine once and set the project:

```bash
earthengine authenticate
```

Then run the app with `GEE_PROJECT_ID` set. If you are using an authenticated local environment, the Earth Engine Python client can reuse your credentials.

For an unattended deployment, place the service-account JSON in the `GEE_CREDENTIALS_JSON` secret and set `GEE_PROJECT_ID`. Do **not** commit a private key to GitHub.

### 4. Start

```bash
streamlit run app.py
```

## Streamlit Cloud deployment

1. Push the repository to a public GitHub repository.
2. In Streamlit Community Cloud, create the app and set the main file to `app.py`.
3. Add secrets equivalent to:

```toml
GEMINI_API_KEY = "your_key"
GEMINI_MODEL = "gemini-3.7-flash"
GEE_PROJECT_ID = "your_project_id"
GEE_CREDENTIALS_JSON = "{...single-line service-account JSON...}"
ALERT_WEBHOOK_URL = "https://..." # optional
```

The app copies supported Streamlit secrets into the process environment at startup.

## Demo script (3–5 minutes)

**0:00–0:30 — Problem.** Select Visakhapatnam and show the operational question: where should responders act before landfall?

**0:30–1:10 — Forecast.** Choose the Severe scenario. Point out the district risk score, local wind, rainfall, surge screening estimate and critical assets.

**1:10–1:50 — Explainability.** Open Impact pathways. Show how the same event can stress power, access and low-lying coastal assets through different mechanisms.

**1:50–2:30 — Satellite + AI.** Open Satellite evidence to show the Earth Engine connector. Then open Gemini copilot and run the multimodal analysis; show that Gemini receives both the image and structured data.

**2:30–3:20 — Action.** Generate a Telugu advisory. Highlight the pre-landfall actions and the official-guidance guardrail. Dispatch it in demo mode or through the configured webhook.

**3:20–4:00 — Scale.** Switch to Odisha or Tamil Nadu and show that the same engine works across another coastal district without rewriting the application logic.

## Design choices that matter to judges

### Problem-solution fit
The product does not stop at "predict cyclone." It answers an operational allocation question: **which critical assets need anticipatory attention first, and which damage pathway explains the priority?**

### AI / technical execution
Gemini is used where multimodality adds value: it sees the same risk surface an operator sees and turns structured estimates into a concise decision brief. The model is not used to manufacture the core numbers.

### Depth across India
The data catalog spans multiple Bay of Bengal states and uses a clean adapter boundary for municipal GIS. Adding a state becomes a data/configuration change rather than an architectural rewrite.

### Deployability
The app is a single Streamlit service with optional connectors. A pilot can start with a curated infrastructure CSV, then replace that layer with official GIS and authenticated Google services.

## Model caveats

The hazard engine is a **transparent screening model**, designed for prototype demonstration and prioritization. It intentionally avoids claiming physical forecast accuracy. Storm surge, rainfall and wind attenuation are simplified relationships; an operational deployment should replace these with authoritative forecast ensembles, high-resolution DEM/bathymetry, flood models, official cyclone tracks and validated infrastructure fragility curves.

## Sources used by the prototype

- Google Gemini / Google Gen AI SDK
- Google Earth Engine Python API
- Open-Meteo current weather adapter
- Demo infrastructure records included in `data/infrastructure.csv`

## Repository map

```text
.
├── app.py
├── requirements.txt
├── README.md
├── .env.example
├── data/
│   ├── districts.csv
│   └── infrastructure.csv
├── outbox/
├── src/
│   ├── advisory.py
│   ├── cap.py
│   ├── config.py
│   ├── data.py
│   ├── gee_service.py
│   ├── gemini_service.py
│   ├── insurance.py
│   ├── risk.py
│   ├── visuals.py
│   └── weather.py
├── tests/
│   ├── test_smoke.py
│   └── test_upgrades.py
└── .streamlit/
    └── config.toml
```

## Gemini model alignment
The default Gemini model is `gemini-3.7-flash`, matching the Track 5 requirement. Override `GEMINI_MODEL` only with a currently supported model.
