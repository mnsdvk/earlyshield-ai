# EarlyShield AI — Submission Notes

## 2–3 line brief description
EarlyShield AI is an anticipatory cyclone intelligence platform that combines live weather context, transparent hazard/exposure modeling, Google Earth Engine satellite evidence and Gemini multimodal reasoning to identify vulnerable infrastructure before landfall. It turns the forecast into prioritized actions and multilingual advisories for district disaster-management teams.

## Suggested 10–12 slide pitch deck
1. **Title — EarlyShield AI:** Anticipatory Cyclone & Infrastructure Forecaster.
2. **The operational gap:** warnings exist, but response teams still need to answer where to act first.
3. **Our answer:** Signal → risk surface → infrastructure priority → action.
4. **End-to-end demo flow:** district selection, scenario, map, pathways, AI brief, advisory.
5. **Architecture:** Open-Meteo + risk engine + infrastructure GIS + GEE + Gemini + dispatch.
6. **AI / technical execution:** Gemini receives structured forecast + visual evidence and produces an operator brief.
7. **Why multimodal matters:** map evidence is interpreted alongside numeric hazard and exposure context.
8. **India scale:** same engine across coastal districts; municipal GIS can replace the demo catalog.
9. **Impact:** pre-positioning, access continuity, backup power, shelter readiness, response prioritization.
10. **Deployability:** Streamlit / Cloud Run, secrets-based Google integration, webhook boundary.
11. **Responsible AI:** transparent screening equations, provenance labels, official-warning override, no invented evacuation orders.
12. **Next step:** pilot with district GIS + official cyclone forecasts + validated flood/surge models.

## 3–5 minute demo script
**0:00–0:25** — “A cyclone warning tells us danger exists. The harder question is where a district should act first.”

**0:25–1:05** — Select Visakhapatnam, choose Severe, run the forecast. Show the risk score, local wind, rainfall, surge estimate and critical assets.

**1:05–1:40** — Open the infrastructure map. Click or point out the power, hospital, shelter and road records. Explain that the engine separates hazard from exposure and fragility.

**1:40–2:10** — Open Impact pathways. Show how wind, rainfall/access and coastal surge create different operational failure modes.

**2:10–2:50** — Open Satellite evidence and show the Earth Engine view. Open Gemini Copilot and run the multimodal brief. Emphasize that Gemini is reasoning over the same visual evidence and structured forecast rather than inventing the numbers.

**2:50–3:30** — Generate a Telugu advisory. Show the preparation actions and the official-guidance guardrail. Dispatch in demo mode or to the configured webhook.

**3:30–4:00** — Switch to Puri / Chennai / Kakinada. “The workflow is reusable; the district changes, the architecture does not.”

## Final submission checklist
- Public GitHub repository URL
- Live prototype URL
- Public YouTube or Google Drive demo video
- Pitch deck exported to PDF ≤ 5 MB
- Brief description copied into the portal
- Gemini API key or Vertex credentials working in the deployed environment
- Earth Engine project and credentials working for live satellite tab
- Optional municipal webhook tested


## Final hardening included
- Forecast reruns clear the prior Earth Engine image so Gemini cannot analyze stale district imagery.
- Advisory text is bound to an operator-editable widget before download/dispatch.
- CAP-style JSON export uses core CAP 1.2 field semantics while clearly identifying the export as JSON for prototype integration; strict CAP 1.2 exchange uses XML.
- The live weather adapter also exposes a 48-hour precipitation total for the illustrative parametric liquidity stress-test.
- External Earth Engine/Gemini failures are caught at the UI boundary without raw tracebacks.
- `pytest` is included in requirements; transient Python/test caches are excluded from Git.
