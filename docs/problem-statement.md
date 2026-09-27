# Problem Statement

## Background

Digital financial fraud in India — spanning UPI payment fraud, SIM-swap scams, vishing attacks, and organized money-mule networks — has grown into a large-scale, coordinated criminal industry. Cases routinely involve dozens of actors, hundreds of transactions, and thousands of telecom records spread across banking systems, telecom operators, and police complaint registries. When a victim files a complaint, investigators at cyber-crime cells must manually reconcile Call Detail Records (CDRs) from telecom providers, UPI/IMEI transaction logs from banks, device records, and victim complaint narratives — all stored in separate, incompatible data silos with no common identifier scheme.

## The Problem

Cyber-crime investigators managing multi-victim financial fraud cases are overwhelmed by fragmented, multi-source evidence. A single case can generate hundreds of CDR entries, dozens of UPI transfers across layered mule accounts, multiple device IMEI records, and victim complaint reports — each arriving in a different CSV or PDF format with no shared entity namespace. Manually cross-referencing a caller's phone number against a bank account, linking it to an IMEI, and then tracing that device to a tower location and a second set of phone numbers can take an experienced analyst several days per case. During this window, fraudulently transferred funds are withdrawn or laundered further, and the critical 24–72 hour interception window is missed. There is no automated tool purpose-built for this cross-source, graph-centric reconstruction workflow — investigators rely on spreadsheets, manual annotation, and institutional memory.

## Who is Affected

**Cyber-crime investigators and analysts** working at state and central police cyber-crime cells in India, handling digital financial fraud cases with ten or more victims and multiple suspected operators. These investigators are technically literate but not data scientists; they need actionable intelligence outputs (who called whom, which accounts received funds, which devices were shared) rather than raw data dumps. Secondary stakeholders include **bank fraud teams** that must issue account-freeze notices within tight legal windows, and **prosecutors** who need court-ready evidence briefs that clearly separate observed records from derived inferences.

## Why It Matters

- **Fund recovery window**: RBI guidelines and court precedents recognize a 24–72 hour window during which fraudulently transferred funds can be frozen before they are layered through multiple mule accounts and become unrecoverable. Manual cross-referencing routinely exceeds this window.
- **Volume**: India's National Cyber Crime Reporting Portal (Cyber Dost / i4C) receives tens of thousands of fraud complaints monthly. Each unresolved case represents direct financial loss to a victim — average reported fraud amounts in organized vishing cases range from ₹50,000 to ₹5,00,000 per victim.
- **Coordination complexity**: Modern fraud syndicates use rotating SIM cards, shared IMEI devices, layered UPI mule accounts, and scripted call flows to defeat simple pattern matching. Identifying a coordination or consolidation node — the central actor distributing stolen funds — requires multi-hop graph traversal across at least three evidence types simultaneously.
- **Legal risk**: An investigator presenting evidence that conflates a derived inference with a directly observed record risks case dismissal. There is no existing workflow that explicitly labels each finding as `OBSERVED`, `DERIVED`, or `ANALYTICAL INFERENCE`.

## Why Existing Solutions Fall Short

General-purpose analytics tools (Excel, Maltego, generic graph databases) require investigators to manually define entity schemas, write import scripts, and learn graph query languages — skills most cyber-crime cell analysts do not have. Commercial intelligence platforms (i2 Analyst's Notebook, Palantir) are prohibitively expensive for state police budgets and require weeks of training. There is no open, purpose-built tool that:

1. Accepts the exact evidence file formats (CSV CDR, UPI transaction exports, complaint records) that Indian cyber-crime investigators actually receive.
2. Automatically resolves entities across source types (e.g., recognizes that `9876543210`, `+919876543210`, and `91-9876543210` are the same phone number).
3. Constructs a multi-hop investigation graph, scores entities against known fraud-pattern signatures, and generates an evidence-linked case brief — all in a single, reproducible pipeline that a non-data-scientist investigator can operate from a browser.
