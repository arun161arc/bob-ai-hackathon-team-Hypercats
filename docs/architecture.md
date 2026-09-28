
flowchart TD
    A[Investigator / User] --> B[Streamlit Frontend]

    B --> C[Case Intake]
    C --> D[Evidence Ingestion]
    D --> E[CSV Evidence Files]

    E --> F[CDR Records]
    E --> G[UPI Transactions]
    E --> H[Complaint Records]
    E --> I[Device Records]

    I --> J[Data Processing & Normalization]
    J --> K[Entity Extraction]
    K --> L[Entity Resolution / Canonicalization]
    L --> M[Evidence Ledger]

    M --> N[Investigation Graph]
    M --> O[Evidence Explorer]
    M --> P[Investigation Timeline]

    N --> Q[Phones]
    N --> R[Bank Accounts]
    N --> S[IMEIs / Devices]
    N --> T[Towers]
    N --> U[Persons]
    N --> V[Transactions]
    N --> W[Investigation Analysis]
    N --> X[Investigation Copilot]

    W --> Y[Fraud Pattern Detection]
    W --> Z[Shared Device Analysis]
    W --> AA[Fund Flow Analysis]
    W --> AB[Multi-hop Analysis]
    W --> AC[Edge Case Intelligence]

    X --> AD[Investigation Findings]
    Y --> AD
    Z --> AD
    AA --> AD
    AB --> AD
    AC --> AD

    B --> AD
    AD --> AE[Evidence-Linked Case Brief]
