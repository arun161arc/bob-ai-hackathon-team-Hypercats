## Overall Architecture

Chanakya-Graph is a **Python + Streamlit AI-assisted cyber-fraud investigation platform**. It ingests structured cyber-fraud evidence such as CDR records, UPI transactions, complaints, and device records, normalizes the data, extracts entities and relationships, builds an investigation graph, performs analytical detection, and presents evidence-linked findings through the dashboard.

### Components

| Component | Technology | Responsibility |
|---|---|---|
| **Frontend** | Streamlit | Investigation dashboard, case intake, graph visualization, timeline, evidence explorer, findings, and case brief |
| **Application / Orchestration** | Python | Coordinates the investigation pipeline and connects the different analysis phases |
| **Data Processing** | Python, Pandas, Regex | CSV ingestion, validation, normalization, preprocessing, and structured evidence processing |
| **Entity & Relationship Extraction** | Python, Regex, deterministic rules | Extracts phones, bank accounts, IMEIs, towers, persons, transactions, and relationships |
| **Entity Resolution** | Python | Normalizes identifiers and creates canonical entities across multiple evidence sources |
| **Evidence Ledger** | JSON | Maintains evidence records, provenance, source type, timestamps, and evidence IDs |
| **Investigation Graph** | NetworkX + JSON | Represents entities as nodes and investigative relationships as edges |
| **AI / ML Analysis** | Scikit-learn | Fraud-pattern classification and analytical scoring such as mule-chain, funnel-account, shared-device, and multi-hop patterns |
| **Investigation Copilot** | Python rule-based analysis | Answers investigation-oriented questions using the structured graph and evidence |
| **Reporting** | Python + JSON/TXT | Generates final case briefs and evidence-linked investigation reports |
| **Storage** | CSV + JSON files | Stores normalized evidence and generated investigation artifacts |

## Data Flow

1. **Case creation**  
   The investigator creates or loads an investigation case through the Streamlit interface.

2. **Evidence ingestion**  
   The system accepts structured mock investigation data including:
   - CDR/call records
   - UPI transaction records
   - Complaint records
   - Device/IMEI records

3. **Normalization**  
   Python/Pandas processes the input files and converts the records into a consistent internal structure.

4. **Entity extraction**  
   The system identifies entities such as:
   - Phone numbers
   - Bank accounts
   - IMEIs
   - Towers
   - Persons
   - Transactions
   - References

5. **Entity resolution**  
   Identifiers appearing across different sources are normalized and mapped to canonical entities.

6. **Evidence ledger creation**  
   Every processed record receives an evidence reference so that findings can be traced back to the underlying source record.

7. **Graph construction**  
   NetworkX creates an investigation graph where entities become nodes and relationships such as `CALLED`, `TRANSFERRED_FUNDS`, `USED_HARDWARE`, and `CONNECTED_TO_TOWER` become edges.

8. **Investigation analysis**  
   The analysis layer evaluates the graph and evidence for patterns such as shared devices, funnel accounts, mule chains, and multi-hop fund movement.

9. **Investigation interface**  
   The Streamlit dashboard exposes the results through the Investigation Command Center, graph, timeline, Evidence Explorer, Copilot, and other investigation views.

10. **Evidence-linked reporting**  
    Findings are connected back to evidence IDs and compiled into a final case brief for human review.

### Core flow

```text
Raw Evidence
     ↓
Ingestion
     ↓
Normalization
     ↓
Entity Extraction
     ↓
Entity Resolution
     ↓
Evidence Ledger
     ↓
Investigation Graph
     ↓
AI/ML + Rule-Based Analysis
     ↓
Investigation Findings
     ↓
Timeline / Copilot / Evidence Explorer
     ↓
Evidence-Linked Case Brief
