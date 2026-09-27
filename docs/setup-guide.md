# Setup Guide — Chanakya-Graph

> **This file is read by the automated evaluation pipeline. Be precise and complete.**

## Prerequisites

Before you begin, ensure you have the following installed:

- [x] Python 3.9+
- [x] `pip` (bundled with Python)
- [x] Git

> **Optional:** An IBM Cloud account with watsonx.ai access is required only if you intend to enable the live watsonx.ai integration (see [Environment Variables](#environment-variables)). The pipeline runs fully offline without it.

---

## Environment Variables

Copy `.env.example` to `.env` inside the `src/` directory and fill in the values:

```bash
cp src/.env.example src/.env
```

| Variable | Description | Required |
|---|---|---|
| `WATSONX_API_KEY` | IBM watsonx.ai API key | No (integration-ready; not called at runtime in the submitted build) |
| `WATSONX_PROJECT_ID` | watsonx.ai project ID | No |
| `WATSONX_URL` | watsonx.ai service URL (default: `https://us-south.ml.cloud.ibm.com`) | No |
| `APP_PORT` | Port the application listens on (default: `8000`) | No |
| `APP_ENV` | Runtime environment — `development` or `production` | No |
| `SLACK_WEBHOOK_URL` | Slack webhook URL for alerts | No |

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-org/bob-ai-hackathon-team-Hypercats.git
cd bob-ai-hackathon-team-Hypercats

# 2. (Recommended) Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows

# 3. Install all dependencies
pip install -r requirements.txt

# 4. (Optional) Download the spaCy English model used by the copilot
python -m spacy download en_core_web_sm
```

---

## Running the Application

```bash
# Launch the Streamlit investigation dashboard
streamlit run src/dashboard/app.py
```

The dashboard will open automatically in your browser, or navigate to:

```
http://localhost:8501
```

### Demo mode (pre-loaded synthetic data)

```bash
streamlit run src/dashboard/demo_app.py
```

---

## Running Tests

```bash
# Run the full test suite from the repo root
pytest tests/ -v
```

---

## Quick Demo

The `demo_app.py` entry point boots the dashboard with the bundled synthetic CDR / UPI / device / complaint CSV fixtures already loaded, so you can walk through every feature without providing your own evidence files:

```bash
streamlit run src/dashboard/demo_app.py
# Then open http://localhost:8501 in your browser
```

Key things to try:

1. **Evidence upload panel** — swap in your own CSV files at any time.
2. **Investigation graph** — zoom, pan, and click nodes to inspect entity details.
3. **Fraud classification** — view the RandomForest confidence scores for each actor.
4. **Case brief export** — download the court-ready brief with evidence-tier labels.
5. **Investigation Copilot** — type a free-text query such as *"Who received money?"* or *"Show shared devices?"*.

---

## Project Structure

```
bob-ai-hackathon-team-Hypercats/
├── requirements.txt          ← Python dependency manifest
├── src/
│   ├── .env.example          ← Environment variable template
│   ├── dashboard/
│   │   ├── app.py            ← Main Streamlit entry point
│   │   └── demo_app.py       ← Demo entry point (synthetic data pre-loaded)
│   ├── ingestion/            ← Phase 1 — multi-source CSV ingestion
│   ├── entity/               ← Phase 2 — entity resolution & canonical namespace
│   ├── graph/                ← Phase 3 — directed graph construction & centrality
│   ├── model/                ← Phase 4 — RandomForestClassifier fraud detection
│   ├── investigation/        ← Phase 5 — timeline & evidence-tier labelling
│   ├── output/               ← Phase 6 — case brief generation
│   ├── copilot/              ← Phase 7 — free-text Investigation Copilot
│   └── integration/          ← IBM watsonx.ai integration hooks
├── docs/                     ← Architecture and setup documentation
├── demo/                     ← Screenshots, video link, live demo URL
└── presentation/             ← Slide deck
```

---

## Troubleshooting

| Issue | Solution |
|---|---|
| `ModuleNotFoundError` after install | Re-run `pip install -r requirements.txt` inside your virtual environment. Make sure the venv is activated. |
| `streamlit: command not found` | Streamlit is installed inside the venv — activate it first: `source .venv/bin/activate` |
| spaCy model not found | Run `python -m spacy download en_core_web_sm` |
| Graph visualisation blank | Ensure `pyvis` installed correctly: `pip install pyvis` |
| watsonx.ai 401 error | Verify `WATSONX_API_KEY` and `WATSONX_PROJECT_ID` in `src/.env`; the submitted build does not call watsonx.ai at runtime, so this only affects optional integration testing |
| Port 8501 already in use | Run `streamlit run src/dashboard/app.py --server.port 8502` |
