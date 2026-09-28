# Setup Guide

> **This file is read by the automated evaluation pipeline. Be precise and complete.**

## Chanakya-Graph — AI-Assisted Cyber-Fraud Investigation Platform

## Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.10+
- pip
- Git
- Streamlit
- A modern web browser (Chrome or Edge)
- Windows, Linux, or macOS

**Optional:**
- IBM watsonx.ai account/API access (if the optional AI/LLM integration is enabled)
- Ollama (if using a local LLM instead of a cloud model)

> Chanakya-Graph's core investigation pipeline runs using local Python modules and synthetic evidence data.

## Environment Variables

The core synthetic-data investigation pipeline does not require any environment variables.

If the optional IBM watsonx.ai integration is enabled, create a `.env` file in the project root:


## Installation

### 1. Clone the repository

```bash
git clone https://github.com/[your-org]/[your-repo].git
cd [your-repo]
```

### 2. Create a virtual environment

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**Linux/macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

If required packages are not yet listed in `requirements.txt`, install them manually:

```bash
pip install streamlit pandas networkx scikit-learn pyvis
```

Additional packages used by individual modules can be installed as required.

## Project Structure

```
bob-ai-hackathon-team-Hypercats/
│
├── src/
│   ├── dashboard/
│   │   ├── demo_app.py
│   │   └── pages/
│   │       └── command_center.py
│   │
│   ├── data/
│   │   ├── cdr_records.csv
│   │   ├── upi_transactions.csv
│   │   ├── complaints.csv
│   │   └── device_records.csv
│   │
│   ├── ingestion/
│   ├── entity/
│   ├── graph/
│   ├── model/
│   ├── investigation/
│   ├── integration/
│   └── output/
│
└── requirements.txt
```

## Input Evidence

Chanakya-Graph accepts four evidence categories:

| File | Description |
|---|---|
| `cdr_records.csv` | Call Detail Records |
| `upi_transactions.csv` | UPI transaction records |
| `complaints.csv` | Cyber-fraud complaints |
| `device_records.csv` | Device, IMEI and tower observations |

The Case Intake interface validates these files before processing. The project also includes synthetic demonstration data so the system can be demonstrated without real law-enforcement records.

## Running the Application

From the project root, run:

```bash
python -m streamlit run src\dashboard\demo_app.py
```

Streamlit will display a local URL similar to `http://localhost:8501`. Open that address in your browser.

## Running the Investigation Pipeline

The complete pipeline can be executed independently of Streamlit:

```bash
python -m src.integration.demo_pipeline
```

The pipeline processes the active case through the following investigation stages:

```
Case Intake → Evidence Processing → Entity Extraction → Entity Resolution
    → Graph Construction → Graph Analysis → Fraud Pattern Analysis
    → Command Center → Evidence Explorer → Timeline
    → Edge Case Intelligence → Final Case Brief → Evidence-Linked Case Brief
```

## Quick Demo

1. **Start the application:**
   ```bash
   python -m streamlit run src\dashboard\demo_app.py
   ```

2. **Open the Case Intake page** and upload:
   - `cdr_records.csv`
   - `upi_transactions.csv`
   - `complaints.csv`
   - `device_records.csv`

3. **Start investigation processing.** The system creates a case and processes the uploaded evidence.

4. **Explore the results.** The dashboard provides:
   - Investigation Command Center
   - Investigation Graph
   - Connection Explanation
   - Evidence Explorer
   - Timeline
   - Edge Case Intelligence
   - Investigation Copilot
   - Final Case Brief
   - Evidence-Linked Case Brief

## Running Individual Phases

For debugging or development, individual phases can be executed independently:

```bash
# Entity extraction
python -m src.entity.run_phase2

# Graph construction
python -m src.graph.run_phase3

# Fraud pattern model
python -m src.model.run_phase4

# Evidence-linked investigation
python -m src.investigation.phase16_evidence_linked_brief
```

The recommended approach for the complete application remains:

```bash
python -m src.integration.demo_pipeline
```

## Output Files

Investigation outputs are generated under `src/output/`:

```
src/output/entities/
├── entity_occurrences.json
├── canonical_entities.json
└── multi_source_entities.json

src/output/graph/
├── investigation_graph.json
├── graph_analysis.json
└── investigation_graph.html

src/output/model/
├── fraud_pattern_model.pkl
├── feature_names.json
└── predictions.json

src/output/investigation/
├── command_center.json
├── evidence_ledger.json
├── investigation_timeline.json
├── edge_case_intelligence.json
├── final_case_brief.json
├── final_case_brief.txt
├── phase16_evidence_linked_case_brief.json
└── phase16_evidence_linked_case_brief.txt
```

## Running Tests / Validation

For pipeline validation, run:

```bash
python -m src.integration.demo_pipeline
```

A successful execution finishes with:

```
CHANAKYA-GRAPH
COMPLETE INVESTIGATION PIPELINE SUCCESSFUL
```

You can also verify that the expected JSON files exist under `src/output/graph/` and `src/output/investigation/`.

## Troubleshooting

| Issue | Solution |
|---|---|
| `ModuleNotFoundError: No module named 'src'` | Run commands from the project root using `python -m ...` |
| `ModuleNotFoundError` for a dependency | Activate `.venv` and run `pip install -r requirements.txt` |
| Streamlit does not start | Run `python -m streamlit run src\dashboard\demo_app.py` |
| No active investigation case found | Use the Case Intake page to create/process a case |
| No columns to parse from file | Check that all four uploaded CSV files contain headers and data rows |
| Graph output is missing | Run `python -m src.integration.demo_pipeline` |
| Phase 16 report is missing | Run `python -m src.investigation.phase16_evidence_linked_brief` |
| `NameError: clean_finding_text` | Ensure the helper function is defined near the top of `src/dashboard/pages/command_center.py` |
| Old investigation results appear | Run the complete pipeline again so previous outputs are replaced |
| Import/circular-import error involving `demo_pipeline` | Ensure `demo_pipeline.py` does not import `run_complete_investigation` from itself |

## Evidence and Data Disclaimer

Chanakya-Graph's demonstration dataset is **synthetic/mock data** created for development and demonstration purposes only.

The system separates findings by confidence tier: **OBSERVED → DERIVED → ANALYTICAL INFERENCE**.

Analytical findings are investigative leads and must be validated against the underlying evidence. The system does not automatically determine guilt, legal responsibility, or criminal attribution.
