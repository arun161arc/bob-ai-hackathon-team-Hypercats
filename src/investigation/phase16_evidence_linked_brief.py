"""
CHANAKYA-GRAPH — PHASE 16
FINAL EVIDENCE-LINKED CASE BRIEF

Purpose:
    Generate a final investigation case brief by combining:

    - Active case information
    - Command-center findings
    - Evidence ledger
    - Investigation timeline
    - Financial analysis
    - Investigative findings
    - Recommended actions

This version is deliberately defensive against different JSON structures.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


# ============================================================
# PATHS
# ============================================================

SRC_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = SRC_DIR / "data"
CASES_DIR = DATA_DIR / "cases"
OUTPUT_DIR = SRC_DIR / "output" / "investigation"

ACTIVE_CASE_FILE = CASES_DIR / "active_case.json"
COMMAND_CENTER_FILE = OUTPUT_DIR / "command_center.json"
EVIDENCE_LEDGER_FILE = OUTPUT_DIR / "evidence_ledger.json"
TIMELINE_FILE = OUTPUT_DIR / "investigation_timeline.json"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# JSON HELPERS
# ============================================================

def load_json(path: Path, default: Any = None) -> Any:
    """
    Safely load a JSON file.
    """

    if default is None:
        default = {}

    try:
        if not path.exists():
            return default

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    except (OSError, json.JSONDecodeError):
        return default


def save_json(path: Path, data: Any) -> None:
    """
    Save JSON with readable formatting.
    """

    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False,
            default=str,
        )


def safe_list(value: Any) -> list:
    """
    Convert common JSON structures into a list.
    """

    if value is None:
        return []

    if isinstance(value, list):
        return value

    if isinstance(value, dict):

        for key in (
            "items",
            "records",
            "events",
            "timeline",
            "evidence",
            "data",
            "results",
            "findings",
        ):
            if isinstance(value.get(key), list):
                return value[key]

    return []


def safe_dict(value: Any) -> dict:
    """
    Return a dictionary or empty dictionary.
    """

    return value if isinstance(value, dict) else {}


# ============================================================
# DATA LOADERS
# ============================================================

def load_active_case() -> dict:
    return safe_dict(
        load_json(
            ACTIVE_CASE_FILE,
            {}
        )
    )


def load_command_center() -> dict:
    return safe_dict(
        load_json(
            COMMAND_CENTER_FILE,
            {}
        )
    )


def load_evidence_ledger() -> Any:
    return load_json(
        EVIDENCE_LEDGER_FILE,
        []
    )


def load_investigation_timeline() -> Any:
    """
    Load investigation timeline.

    Handles both:
        [...]
    and:
        {"events": [...]}
        {"timeline": [...]}
        {"data": [...]}
    """

    return load_json(
        TIMELINE_FILE,
        []
    )


# ============================================================
# CASE INFORMATION
# ============================================================

def get_case_information() -> dict:
    case = load_active_case()

    if not case:
        return {
            "case_id": "UNKNOWN",
            "title": "Unknown Investigation Case",
            "status": "UNKNOWN",
            "created_at": "",
            "updated_at": "",
            "description": "",
        }

    return {
        "case_id": (
            case.get("case_id")
            or case.get("id")
            or "UNKNOWN"
        ),

        "title": (
            case.get("title")
            or case.get("case_title")
            or case.get("name")
            or "Investigation Case"
        ),

        "status": (
            case.get("status")
            or case.get("case_status")
            or "UNKNOWN"
        ),

        "created_at": (
            case.get("created_at")
            or case.get("created")
            or ""
        ),

        "updated_at": (
            case.get("updated_at")
            or case.get("updated")
            or ""
        ),

        "description": (
            case.get("description")
            or case.get("summary")
            or ""
        ),
    }


# ============================================================
# EVIDENCE SUMMARY
# ============================================================

def build_evidence_summary(evidence: Any) -> dict:
    """
    Build a safe evidence summary.

    Handles malformed/nested evidence structures.
    """

    evidence_items = safe_list(evidence)

    normalized = []

    for item in evidence_items:

        if isinstance(item, dict):
            normalized.append(item)

        elif isinstance(item, list):

            for nested in item:
                if isinstance(nested, dict):
                    normalized.append(nested)

    categories = {}
    evidence_ids = []

    for item in normalized:

        category = (
            item.get("category")
            or item.get("type")
            or item.get("evidence_type")
            or "UNKNOWN"
        )

        category = str(category)

        categories[category] = (
            categories.get(category, 0) + 1
        )

        evidence_id = (
            item.get("evidence_id")
            or item.get("id")
            or item.get("artifact_id")
        )

        if evidence_id:
            evidence_ids.append(str(evidence_id))

    return {
        "total_evidence": len(normalized),
        "categories": categories,
        "evidence_ids": evidence_ids,
    }


# ============================================================
# TIMELINE SUMMARY
# ============================================================

def build_timeline_summary(timeline=None):
    """
    Build a robust investigation timeline summary.

    IMPORTANT:
    This function intentionally does NOT call load_timeline().
    """

    calls = 0
    transactions = 0
    complaints = 0
    devices = 0
    total_amount = 0.0

    timestamps = []

    # --------------------------------------------------------
    # Load timeline
    # --------------------------------------------------------

    if timeline is None:
        timeline = load_investigation_timeline()

    # --------------------------------------------------------
    # Handle dictionary wrapper
    # --------------------------------------------------------

    if isinstance(timeline, dict):

        extracted = None

        for key in (
            "timeline",
            "events",
            "records",
            "items",
            "data",
        ):

            value = timeline.get(key)

            if isinstance(value, list):
                extracted = value
                break

        timeline = (
            extracted
            if extracted is not None
            else []
        )

    # --------------------------------------------------------
    # Ensure list
    # --------------------------------------------------------

    if not isinstance(timeline, list):
        timeline = []

    # --------------------------------------------------------
    # Normalize nested lists
    # --------------------------------------------------------

    normalized_events = []

    for item in timeline:

        if isinstance(item, dict):

            normalized_events.append(item)

        elif isinstance(item, list):

            for nested_item in item:

                if isinstance(nested_item, dict):
                    normalized_events.append(
                        nested_item
                    )

    # --------------------------------------------------------
    # Analyze events
    # --------------------------------------------------------

    for event in normalized_events:

        event_type = str(
            event.get("event_type", "")
        ).strip().upper()

        if not event_type:
            event_type = str(
                event.get("type", "")
            ).strip().upper()

        # ----------------------------------------------------
        # CALL
        # ----------------------------------------------------

        if event_type in (
            "CALL",
            "PHONE_CALL",
            "CALL_EVENT",
        ):
            calls += 1

        # ----------------------------------------------------
        # TRANSACTION
        # ----------------------------------------------------

        elif event_type in (
            "TRANSACTION",
            "PAYMENT",
            "TRANSFER",
            "TRANSACTION_EVENT",
        ):

            transactions += 1

            amount = event.get(
                "amount_inr",
                event.get("amount", 0)
            )

            try:
                total_amount += float(
                    amount or 0
                )

            except (
                TypeError,
                ValueError,
            ):
                pass

        # ----------------------------------------------------
        # COMPLAINT
        # ----------------------------------------------------

        elif event_type in (
            "COMPLAINT",
            "COMPLAINT_EVENT",
        ):
            complaints += 1

        # ----------------------------------------------------
        # DEVICE
        # ----------------------------------------------------

        elif event_type in (
            "DEVICE",
            "DEVICE_EVENT",
            "DEVICE_OBSERVATION",
            "DEVICE_OBSERVATION_EVENT",
        ):
            devices += 1

        # ----------------------------------------------------
        # TIMESTAMP
        # ----------------------------------------------------

        timestamp = (
            event.get("timestamp")
            or event.get("time")
            or event.get("datetime")
            or event.get("date")
        )

        if timestamp:
            timestamps.append(
                str(timestamp)
            )

    # --------------------------------------------------------
    # Sort timestamps
    # --------------------------------------------------------

    timestamps.sort()

    # --------------------------------------------------------
    # Return
    # --------------------------------------------------------

    return {
        "total_events": len(
            normalized_events
        ),

        "calls": calls,

        "transactions": transactions,

        "complaints": complaints,

        "device_observations": devices,

        "total_transaction_amount": (
            total_amount
        ),

        "first_event": (
            timestamps[0]
            if timestamps
            else ""
        ),

        "last_event": (
            timestamps[-1]
            if timestamps
            else ""
        ),
    }


# ============================================================
# FINANCIAL ANALYSIS
# ============================================================

def build_financial_analysis(timeline=None) -> dict:
    """
    Extract financial information from timeline.
    """

    if timeline is None:
        timeline = load_investigation_timeline()

    if isinstance(timeline, dict):

        for key in (
            "timeline",
            "events",
            "records",
            "items",
            "data",
        ):

            if isinstance(
                timeline.get(key),
                list
            ):
                timeline = timeline[key]
                break

        else:
            timeline = []

    if not isinstance(timeline, list):
        timeline = []

    transactions = []

    for item in timeline:

        if not isinstance(item, dict):
            continue

        event_type = str(
            item.get("event_type")
            or item.get("type")
            or ""
        ).upper()

        if event_type in (
            "TRANSACTION",
            "PAYMENT",
            "TRANSFER",
            "TRANSACTION_EVENT",
        ):

            amount = item.get(
                "amount_inr",
                item.get("amount", 0)
            )

            try:
                amount = float(
                    amount or 0
                )

            except (
                TypeError,
                ValueError,
            ):
                amount = 0.0

            transactions.append(
                {
                    "timestamp": (
                        item.get("timestamp")
                        or ""
                    ),
                    "amount_inr": amount,
                    "description": (
                        item.get("description")
                        or item.get("remarks")
                        or ""
                    ),
                    "transaction_id": (
                        item.get("transaction_id")
                        or item.get("id")
                        or ""
                    ),
                }
            )

    total = sum(
        x["amount_inr"]
        for x in transactions
    )

    return {
        "transaction_count": len(
            transactions
        ),

        "total_amount_inr": total,

        "average_amount_inr": (
            total / len(transactions)
            if transactions
            else 0.0
        ),

        "maximum_amount_inr": (
            max(
                x["amount_inr"]
                for x in transactions
            )
            if transactions
            else 0.0
        ),

        "transactions": transactions,
    }


# ============================================================
# COMMAND CENTER FINDINGS
# ============================================================

def extract_findings(command_center: dict) -> list:
    """
    Extract findings from command center JSON.
    """

    if not isinstance(
        command_center,
        dict
    ):
        return []

    findings = []

    for key in (
        "findings",
        "alerts",
        "observations",
        "results",
        "risk_findings",
        "investigative_findings",
    ):

        value = command_center.get(key)

        if isinstance(value, list):

            for item in value:

                if isinstance(item, dict):
                    findings.append(item)

                elif isinstance(item, str):

                    findings.append(
                        {
                            "finding": item
                        }
                    )

    return findings


# ============================================================
# INVESTIGATIVE FINDINGS
# ============================================================

def build_investigative_findings(
    case_info: dict,
    evidence_summary: dict,
    timeline_summary: dict,
    financial_analysis: dict,
    command_findings: list,
) -> list:

    findings = []

    # --------------------------------------------------------
    # Case status
    # --------------------------------------------------------

    if case_info.get("status"):
        findings.append(
            {
                "finding": "Case status identified",
                "detail": (
                    f"Case status: "
                    f"{case_info['status']}"
                ),
                "source": "active_case.json",
            }
        )

    # --------------------------------------------------------
    # Evidence
    # --------------------------------------------------------

    if evidence_summary[
        "total_evidence"
    ]:

        findings.append(
            {
                "finding": "Evidence collected",
                "detail": (
                    f"{evidence_summary['total_evidence']} "
                    f"evidence item(s) are associated "
                    f"with the investigation."
                ),
                "source": "evidence_ledger.json",
            }
        )

    # --------------------------------------------------------
    # Timeline
    # --------------------------------------------------------

    if timeline_summary[
        "total_events"
    ]:

        findings.append(
            {
                "finding": "Investigation timeline established",
                "detail": (
                    f"{timeline_summary['total_events']} "
                    f"timeline event(s) were processed."
                ),
                "source": "investigation_timeline.json",
            }
        )

    # --------------------------------------------------------
    # Calls
    # --------------------------------------------------------

    if timeline_summary["calls"]:

        findings.append(
            {
                "finding": "Communication activity detected",
                "detail": (
                    f"{timeline_summary['calls']} "
                    f"call event(s) were identified."
                ),
                "source": "investigation_timeline.json",
            }
        )

    # --------------------------------------------------------
    # Transactions
    # --------------------------------------------------------

    if timeline_summary[
        "transactions"
    ]:

        findings.append(
            {
                "finding": "Financial activity detected",
                "detail": (
                    f"{timeline_summary['transactions']} "
                    f"transaction event(s) totaling "
                    f"INR {timeline_summary['total_transaction_amount']:,.2f}."
                ),
                "source": "investigation_timeline.json",
            }
        )

    # --------------------------------------------------------
    # Complaints
    # --------------------------------------------------------

    if timeline_summary[
        "complaints"
    ]:

        findings.append(
            {
                "finding": "Complaint activity recorded",
                "detail": (
                    f"{timeline_summary['complaints']} "
                    f"complaint event(s) were identified."
                ),
                "source": "investigation_timeline.json",
            }
        )

    # --------------------------------------------------------
    # Devices
    # --------------------------------------------------------

    if timeline_summary[
        "device_observations"
    ]:

        findings.append(
            {
                "finding": "Device observations available",
                "detail": (
                    f"{timeline_summary['device_observations']} "
                    f"device observation(s) were recorded."
                ),
                "source": "investigation_timeline.json",
            }
        )

    # --------------------------------------------------------
    # Financial analysis
    # --------------------------------------------------------

    if financial_analysis[
        "transaction_count"
    ]:

        findings.append(
            {
                "finding": "Financial pattern summarized",
                "detail": (
                    f"Average transaction value: "
                    f"INR {financial_analysis['average_amount_inr']:,.2f}; "
                    f"maximum transaction value: "
                    f"INR {financial_analysis['maximum_amount_inr']:,.2f}."
                ),
                "source": "financial timeline analysis",
            }
        )

    # --------------------------------------------------------
    # Command center findings
    # --------------------------------------------------------

    for item in command_findings:

        if not isinstance(item, dict):
            continue

        finding = (
            item.get("finding")
            or item.get("title")
            or item.get("name")
            or item.get("alert")
        )

        detail = (
            item.get("detail")
            or item.get("description")
            or item.get("message")
            or ""
        )

        if finding:

            findings.append(
                {
                    "finding": str(finding),
                    "detail": str(detail),
                    "source": "command_center.json",
                }
            )

    return findings


# ============================================================
# RECOMMENDED ACTIONS
# ============================================================

def build_recommended_actions(
    case_info: dict,
    evidence_summary: dict,
    timeline_summary: dict,
    financial_analysis: dict,
) -> list:

    actions = []

    # --------------------------------------------------------
    # Evidence preservation
    # --------------------------------------------------------

    actions.append(
        {
            "priority": "HIGH",
            "action": (
                "Preserve all collected evidence "
                "and maintain evidence integrity."
            ),
            "basis": (
                "Evidence-linked investigation workflow"
            ),
        }
    )

    # --------------------------------------------------------
    # Timeline preservation
    # --------------------------------------------------------

    if timeline_summary[
        "total_events"
    ]:

        actions.append(
            {
                "priority": "HIGH",
                "action": (
                    "Preserve the investigation timeline "
                    "and associated timestamps."
                ),
                "basis": (
                    f"{timeline_summary['total_events']} "
                    f"timeline events identified."
                ),
            }
        )

    # --------------------------------------------------------
    # Financial records
    # --------------------------------------------------------

    if financial_analysis[
        "transaction_count"
    ]:

        actions.append(
            {
                "priority": "HIGH",
                "action": (
                    "Review and preserve relevant "
                    "transaction records."
                ),
                "basis": (
                    f"{financial_analysis['transaction_count']} "
                    f"financial transaction(s) identified."
                ),
            }
        )

    # --------------------------------------------------------
    # Communication records
    # --------------------------------------------------------

    if timeline_summary[
        "calls"
    ]:

        actions.append(
            {
                "priority": "MEDIUM",
                "action": (
                    "Review relevant communication "
                    "records associated with the case."
                ),
                "basis": (
                    f"{timeline_summary['calls']} "
                    f"call event(s) identified."
                ),
            }
        )

    # --------------------------------------------------------
    # Device records
    # --------------------------------------------------------

    if timeline_summary[
        "device_observations"
    ]:

        actions.append(
            {
                "priority": "MEDIUM",
                "action": (
                    "Preserve relevant device "
                    "observation records."
                ),
                "basis": (
                    f"{timeline_summary['device_observations']} "
                    f"device observation(s) identified."
                ),
            }
        )

    # --------------------------------------------------------
    # Case review
    # --------------------------------------------------------

    actions.append(
        {
            "priority": "MEDIUM",
            "action": (
                "Perform investigator review of the "
                "evidence-linked case brief."
            ),
            "basis": (
                "Final Phase 16 case brief generated."
            ),
        }
    )

    return actions


# ============================================================
# EVIDENCE LINKS
# ============================================================

def build_evidence_links(
    evidence: Any,
    timeline: Any,
) -> list:

    links = []

    evidence_items = safe_list(
        evidence
    )

    timeline_items = safe_list(
        timeline
    )

    # --------------------------------------------------------
    # Evidence links
    # --------------------------------------------------------

    for item in evidence_items:

        if not isinstance(item, dict):
            continue

        evidence_id = (
            item.get("evidence_id")
            or item.get("id")
            or item.get("artifact_id")
        )

        if not evidence_id:
            continue

        links.append(
            {
                "type": "EVIDENCE",
                "id": str(evidence_id),
                "description": (
                    item.get("description")
                    or item.get("name")
                    or item.get("title")
                    or ""
                ),
                "source": (
                    item.get("source")
                    or item.get("file")
                    or "evidence_ledger.json"
                ),
            }
        )

    # --------------------------------------------------------
    # Timeline links
    # --------------------------------------------------------

    for index, item in enumerate(
        timeline_items,
        start=1,
    ):

        if not isinstance(item, dict):
            continue

        links.append(
            {
                "type": "TIMELINE_EVENT",
                "id": str(
                    item.get("event_id")
                    or item.get("id")
                    or f"EVENT-{index:04d}"
                ),
                "event_type": (
                    item.get("event_type")
                    or item.get("type")
                    or "UNKNOWN"
                ),
                "timestamp": (
                    item.get("timestamp")
                    or ""
                ),
                "source": (
                    item.get("source")
                    or "investigation_timeline.json"
                ),
            }
        )

    return links


# ============================================================
# BUILD REPORT
# ============================================================

def build_report() -> dict:
    """
    Build complete Phase 16 report.
    """

    # --------------------------------------------------------
    # Load source data
    # --------------------------------------------------------

    case_info = get_case_information()

    command_center = (
        load_command_center()
    )

    evidence = (
        load_evidence_ledger()
    )

    timeline = (
        load_investigation_timeline()
    )

    # --------------------------------------------------------
    # Build summaries
    # --------------------------------------------------------

    evidence_summary = (
        build_evidence_summary(
            evidence
        )
    )

    timeline_summary = (
        build_timeline_summary(
            timeline
        )
    )

    financial_analysis = (
        build_financial_analysis(
            timeline
        )
    )

    command_findings = (
        extract_findings(
            command_center
        )
    )

    investigative_findings = (
        build_investigative_findings(
            case_info,
            evidence_summary,
            timeline_summary,
            financial_analysis,
            command_findings,
        )
    )

    recommended_actions = (
        build_recommended_actions(
            case_info,
            evidence_summary,
            timeline_summary,
            financial_analysis,
        )
    )

    evidence_links = (
        build_evidence_links(
            evidence,
            timeline,
        )
    )

    # --------------------------------------------------------
    # Build final report
    # --------------------------------------------------------

    report = {

        "phase": 16,

        "phase_name": (
            "FINAL EVIDENCE-LINKED CASE BRIEF"
        ),

        "generated_at": (
            datetime.now().isoformat()
        ),

        "case": case_info,

        "evidence_summary": (
            evidence_summary
        ),

        "timeline_summary": (
            timeline_summary
        ),

        "financial_analysis": (
            financial_analysis
        ),

        "command_center_findings": (
            command_findings
        ),

        "investigative_findings": (
            investigative_findings
        ),

        "recommended_actions": (
            recommended_actions
        ),

        "evidence_links": (
            evidence_links
        ),

        "source_files": {
            "active_case": str(
                ACTIVE_CASE_FILE
            ),
            "command_center": str(
                COMMAND_CENTER_FILE
            ),
            "evidence_ledger": str(
                EVIDENCE_LEDGER_FILE
            ),
            "investigation_timeline": str(
                TIMELINE_FILE
            ),
        },
    }

    return report


# ============================================================
# TEXT REPORT
# ============================================================

def build_text_report(
    report: dict
) -> str:

    case = report.get(
        "case",
        {}
    )

    evidence = report.get(
        "evidence_summary",
        {}
    )

    timeline = report.get(
        "timeline_summary",
        {}
    )

    financial = report.get(
        "financial_analysis",
        {}
    )

    findings = report.get(
        "investigative_findings",
        []
    )

    actions = report.get(
        "recommended_actions",
        []
    )

    lines = []

    lines.append("=" * 78)
    lines.append(
        "CHANAKYA-GRAPH — PHASE 16"
    )
    lines.append(
        "FINAL EVIDENCE-LINKED CASE BRIEF"
    )
    lines.append("=" * 78)

    lines.append("")

    # --------------------------------------------------------
    # CASE
    # --------------------------------------------------------

    lines.append("CASE INFORMATION")
    lines.append("-" * 78)

    lines.append(
        f"Case ID       : "
        f"{case.get('case_id', 'UNKNOWN')}"
    )

    lines.append(
        f"Title         : "
        f"{case.get('title', '')}"
    )

    lines.append(
        f"Status        : "
        f"{case.get('status', '')}"
    )

    lines.append(
        f"Created       : "
        f"{case.get('created_at', '')}"
    )

    lines.append(
        f"Updated       : "
        f"{case.get('updated_at', '')}"
    )

    if case.get("description"):
        lines.append(
            f"Description   : "
            f"{case.get('description')}"
        )

    lines.append("")

    # --------------------------------------------------------
    # EVIDENCE
    # --------------------------------------------------------

    lines.append("EVIDENCE SUMMARY")
    lines.append("-" * 78)

    lines.append(
        f"Total Evidence : "
        f"{evidence.get('total_evidence', 0)}"
    )

    categories = evidence.get(
        "categories",
        {}
    )

    if categories:

        for category, count in categories.items():

            lines.append(
                f"  {category}: {count}"
            )

    lines.append("")

    # --------------------------------------------------------
    # TIMELINE
    # --------------------------------------------------------

    lines.append("TIMELINE SUMMARY")
    lines.append("-" * 78)

    lines.append(
        f"Total Events       : "
        f"{timeline.get('total_events', 0)}"
    )

    lines.append(
        f"Calls              : "
        f"{timeline.get('calls', 0)}"
    )

    lines.append(
        f"Transactions       : "
        f"{timeline.get('transactions', 0)}"
    )

    lines.append(
        f"Complaints         : "
        f"{timeline.get('complaints', 0)}"
    )

    lines.append(
        f"Device Observations: "
        f"{timeline.get('device_observations', 0)}"
    )

    lines.append(
        f"Transaction Amount : INR "
        f"{timeline.get('total_transaction_amount', 0):,.2f}"
    )

    lines.append(
        f"First Event        : "
        f"{timeline.get('first_event', '')}"
    )

    lines.append(
        f"Last Event         : "
        f"{timeline.get('last_event', '')}"
    )

    lines.append("")

    # --------------------------------------------------------
    # FINANCIAL
    # --------------------------------------------------------

    lines.append("FINANCIAL ANALYSIS")
    lines.append("-" * 78)

    lines.append(
        f"Transaction Count : "
        f"{financial.get('transaction_count', 0)}"
    )

    lines.append(
        f"Total Amount      : INR "
        f"{financial.get('total_amount_inr', 0):,.2f}"
    )

    lines.append(
        f"Average Amount    : INR "
        f"{financial.get('average_amount_inr', 0):,.2f}"
    )

    lines.append(
        f"Maximum Amount    : INR "
        f"{financial.get('maximum_amount_inr', 0):,.2f}"
    )

    lines.append("")

    # --------------------------------------------------------
    # FINDINGS
    # --------------------------------------------------------

    lines.append(
        "INVESTIGATIVE FINDINGS"
    )

    lines.append("-" * 78)

    if findings:

        for index, finding in enumerate(
            findings,
            start=1,
        ):

            lines.append(
                f"{index}. "
                f"{finding.get('finding', '')}"
            )

            detail = finding.get(
                "detail",
                ""
            )

            if detail:
                lines.append(
                    f"   {detail}"
                )

            source = finding.get(
                "source",
                ""
            )

            if source:
                lines.append(
                    f"   Source: {source}"
                )

    else:

        lines.append(
            "No additional investigative findings."
        )

    lines.append("")

    # --------------------------------------------------------
    # RECOMMENDED ACTIONS
    # --------------------------------------------------------

    lines.append(
        "RECOMMENDED INVESTIGATIVE ACTIONS"
    )

    lines.append("-" * 78)

    for index, action in enumerate(
        actions,
        start=1,
    ):

        lines.append(
            f"{index}. "
            f"[{action.get('priority', 'NORMAL')}] "
            f"{action.get('action', '')}"
        )

        if action.get("basis"):
            lines.append(
                f"   Basis: "
                f"{action.get('basis')}"
            )

    lines.append("")

    # --------------------------------------------------------
    # EVIDENCE LINKS
    # --------------------------------------------------------

    links = report.get(
        "evidence_links",
        []
    )

    lines.append(
        "EVIDENCE LINKS"
    )

    lines.append("-" * 78)

    if links:

        for link in links:

            lines.append(
                f"- {link.get('type', '')} | "
                f"{link.get('id', '')}"
            )

            if link.get("description"):
                lines.append(
                    f"  {link.get('description')}"
                )

            if link.get("timestamp"):
                lines.append(
                    f"  Timestamp: "
                    f"{link.get('timestamp')}"
                )

    else:

        lines.append(
            "No evidence links available."
        )

    lines.append("")
    lines.append("=" * 78)
    lines.append(
        "END OF PHASE 16 CASE BRIEF"
    )
    lines.append("=" * 78)

    return "\n".join(lines)


# ============================================================
# SAVE REPORT
# ============================================================

def save_text_report(
    report: dict
) -> Path:

    text_path = (
        OUTPUT_DIR
        / "phase16_case_brief.txt"
    )

    text = build_text_report(
        report
    )

    with open(
        text_path,
        "w",
        encoding="utf-8",
    ) as f:

        f.write(text)

    return text_path


def save_json_report(
    report: dict
) -> Path:

    json_path = (
        OUTPUT_DIR
        / "phase16_case_brief.json"
    )

    save_json(
        json_path,
        report
    )

    return json_path


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 78)
    print(
        "CHANAKYA-GRAPH — PHASE 16"
    )
    print(
        "FINAL EVIDENCE-LINKED CASE BRIEF"
    )
    print("=" * 78)

    try:

        # ----------------------------------------------------
        # Build
        # ----------------------------------------------------

        report = build_report()

        # ----------------------------------------------------
        # Save JSON
        # ----------------------------------------------------

        json_path = save_json_report(
            report
        )

        # ----------------------------------------------------
        # Save TXT
        # ----------------------------------------------------

        text_path = save_text_report(
            report
        )

        # ----------------------------------------------------
        # Console summary
        # ----------------------------------------------------

        timeline = report.get(
            "timeline_summary",
            {}
        )

        evidence = report.get(
            "evidence_summary",
            {}
        )

        financial = report.get(
            "financial_analysis",
            {}
        )

        print()
        print("PHASE 16 COMPLETED SUCCESSFULLY")
        print("-" * 78)

        print(
            f"Case ID              : "
            f"{report['case'].get('case_id', 'UNKNOWN')}"
        )

        print(
            f"Evidence Items       : "
            f"{evidence.get('total_evidence', 0)}"
        )

        print(
            f"Timeline Events      : "
            f"{timeline.get('total_events', 0)}"
        )

        print(
            f"Calls                : "
            f"{timeline.get('calls', 0)}"
        )

        print(
            f"Transactions         : "
            f"{timeline.get('transactions', 0)}"
        )

        print(
            f"Complaints           : "
            f"{timeline.get('complaints', 0)}"
        )

        print(
            f"Device Observations  : "
            f"{timeline.get('device_observations', 0)}"
        )

        print(
            f"Total Financial Value: INR "
            f"{financial.get('total_amount_inr', 0):,.2f}"
        )

        print()
        print(
            f"JSON Report: {json_path}"
        )

        print(
            f"Text Report: {text_path}"
        )

        print()
        print("=" * 78)

    except Exception as exc:

        print()
        print(
            "PHASE 16 FAILED"
        )

        print(
            "-" * 78
        )

        print(
            f"{type(exc).__name__}: {exc}"
        )

        print(
            "-" * 78
        )

        raise


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()