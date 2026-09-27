# Solution Overview

## What We Built

Chanakya-Graph is an automated intelligence platform for cyber-syndicate deconvolution. It takes raw, heterogeneous evidence files — Call Detail Records (CDR), UPI transaction logs, victim complaint reports, and device/IMEI records — and automatically fuses them into a single directed investigation graph. From that graph it extracts fraud-pattern features, classifies entities against known mule and coordination-node signatures using a trained RandomForest model, and generates a court-ready, evidence-linked case brief. Everything is accessible through a multi-module Streamlit investigation workstation that a non-data-scientist investigator can operate from a browser with no command-line interaction required.

## How It Works

1. **Case Intake** — The investigator uploads four CSV evidence files (or activates the built-in synthetic demo dataset) through the Streamlit Case Intake page. The system assigns a case ID and validates file schemas, phone number formats, and timestamp consistency before accepting the evidence.
2. **Entity Extraction & Resolution** — Raw identifiers (phone numbers, bank accounts, IMEI numbers, cell tower IDs) are extracted from every evidence record, normalized (e.g., `9876543210` → `+919876543210`), and resolved into a deduplicated set of canonical entities shared across all source types.
3. **Investigation Graph Construction** — A directed `networkx.MultiDiGraph` is built where nodes are canonical entities and edges represent observed relationships: `CALLED`, `TRANSFERRED_FUNDS`, `REPORTED_FRAUD_CALL`, and `USED_HARDWARE`. Every edge carries the originating evidence ID, creating a fully traceable graph. The graph is also rendered as an interactive PyVis HTML network visualization.
4. **Fraud Pattern Evaluation** — Per-entity graph features (degree centrality, betweenness centrality, transaction count, multi-source presence, connected-component membership) are extracted and passed to a trained `RandomForestClassifier`. The model classifies each entity into a fraud-pattern category with a confidence score.
5. **Investigation Intelligence Generation** — The investigation modules generate a chronological timeline, focused sub-graphs for specific pivots, edge-case signals, and human-readable explanations for each connection. All findings are explicitly labelled as `OBSERVED` (from source records), `DERIVED` (calculated from evidence), or `ANALYTICAL INFERENCE` (model output requiring investigator validation).
6. **Case Brief Output** — A structured JSON + plain-text case brief is generated, ranked by prediction confidence, listing the top analytical findings with their supporting evidence IDs and connection counts. This brief is designed to be submitted directly to a bank fraud desk or court.
7. **Investigation Copilot** — At any point, the investigator can ask natural-language questions against the live graph through the Copilot module: *"What is the total loss?"*, *"Who received money?"*, *"Show shared devices"*, *"Find +919876543210"*. The copilot resolves the query against the NetworkX graph and returns structured results instantly.

## Architecture Diagram

> See [`architecture.md`](architecture.md) for the full annotated diagram.

```
[Evidence CSVs]
      │  Phase 1: Ingest & Validate
      ▼
[Evidence Ledger]
      │  Phase 2: Extract & Resolve
      ▼
[Canonical Entities]
      │  Phase 3: Build Graph
      ▼
[NetworkX MultiDiGraph] ──► [PyVis HTML Visualization]
      │  Phase 4: Feature Extraction + RandomForest
      ▼
[Pattern Predictions JSON]
      │  Phase 5–6: Intelligence + Case Brief
      ▼
[Evidence-Linked Case Brief (JSON + TXT)]
      │
[Streamlit Investigation Workstation]
      └──► Command Center | Graph Explorer | Mule Evaluation
           Timeline | Evidence Explorer | Copilot | Final Brief
```

## Key Design Decisions

| Decision | Rationale |
|---|---|
| Flat evidence ledger as Phase 1 → Phase 2 bridge | Decouples ingestion format from graph schema; new evidence types can be added without rewriting the graph builder. |
| `networkx.MultiDiGraph` for the investigation graph | Supports multiple parallel edges between the same entity pair (e.g., multiple calls or transfers), which is essential for detecting repeated-contact fraud patterns. |
| Explicit evidence classification (`OBSERVED` / `DERIVED` / `ANALYTICAL INFERENCE`) | Ensures court-admissibility by preventing investigators from presenting a model inference as a directly recorded fact. Every finding is labelled at its source tier. |
| RandomForest over deep learning for pattern classification | Interpretable feature importance, fast training on small labelled datasets, and no GPU dependency — suitable for a hackathon prototype that must run on an investigator's laptop. |
| Streamlit as the investigation workstation | Single-file deployment, browser-based UI, no frontend build step. Investigators with no developer tooling can run `streamlit run src/dashboard/app.py` after a `pip install`. |
| Subprocess-based backend pipeline execution | Keeps each phase independently testable and allows the existing Phase 1–7 scripts to remain unmodified while the dashboard triggers them on demand. |
| Built-in synthetic demo dataset | Allows demonstrations without exposing real case data. A hard `data_source == "SYNTHETIC_DEMO"` validation guard prevents accidental mixing of demo and operational evidence. |
| Indian phone number normalization to `+91XXXXXXXXXX` | CDR exports from different telecom operators use inconsistent formats; a single canonical form is required before entity resolution can match the same phone across sources. |

## IBM Technologies Used

- **IBM watsonx.ai** *(integration-ready)*: The platform is architected to route the fraud-pattern classification step to a watsonx.ai hosted model endpoint. The `WATSONX_API_KEY`, `WATSONX_PROJECT_ID`, and `WATSONX_URL` environment variables are pre-defined in `src/.env.example`. The current prototype uses a locally trained scikit-learn model; swapping in a watsonx.ai `ibm/granite` inference call requires only replacing the predict step in `src/model/predict_patterns.py`.
- **IBM Cloud** *(deployment target)*: The stateless Streamlit dashboard and the file-based pipeline backend are designed to be containerised and deployed on IBM Cloud Code Engine or IBM Kubernetes Service, with evidence files stored in IBM Cloud Object Storage buckets rather than the local filesystem.
