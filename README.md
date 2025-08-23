
# BookYourCampus — Unified Career Assessment (v2)

A next‑gen, student‑friendly assessment for Classes 8–12 (and early UG). It blends:
- **Personality (Big Five/IPIP-style)** — original items
- **Interests (RIASEC)** — O*NET‑compatible original items
- **Learning Preferences** — original multimodal items (V/A/R-W/K‑inspired)
- **Academics** — self‑ratings by subject
- **Skills** — 21st‑century + domain skills
- **Work Values** — motivation anchors
- **AI & Automation Readiness** — NEW
- **Digital Creativity** — NEW
- **Entrepreneurship Mindset** — NEW
- **Resilience & Adaptability** — NEW
- **Ethics & Global Mindset** — NEW
- **Extracurriculars** — enrichment profile

It computes **career cluster fit** + a **FutureFit score**, and exports a graphical HTML report (printable to PDF).

## Quickstart
```
pip install -r requirements.txt
streamlit run app.py
```

## Hosting
- Streamlit Community Cloud (recommended)
- Hugging Face Spaces (Streamlit template)
- Render.com (start: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`)

## Customize
- Add/edit questions in `assessment/items.json`
- Tune career weights in `assessment/mapping.json`
- Replace branding `assets/logo.png`
- Style/theme in `app.py` (THEME section)
