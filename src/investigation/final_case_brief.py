from pathlib import Path
from datetime import datetime
import json


# ============================================================
# CHANAKYA-GRAPH — PHASE 16
# FINAL EVIDENCE-LINKED CASE BRIEF
# ============================================================


# ============================================================
# PATHS
# ============================================================

SRC_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = SRC_DIR / "data"
CASES_DIR = DATA_DIR / "cases"

OUTPUT_DIR = SRC_DIR / "output" / "investigation"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# JSON HELPERS
# ============================================================

def load_json(path):
    """
    Safely load JSON.

    Returns:
        dict/list/etc. when valid
        {} when file does not exist or JSON is invalid
    """

    if not path.exists():
        print(f"[WARNING] File not found: {path}")
        return {}

    try:
        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:
            return json.load(f)

    except json.JSONDecodeError as exc:
        print(
            f"[WARNING] Invalid JSON in {path}: {exc}"
        )
        return {}

    except Exception as exc:
        print(
            f"[WARNING] Could not load {path}: {exc}"
        )
        return {}


def ensure_dict(value):
    """
    Return a dictionary or an empty dictionary.
    """

    if isinstance(value, dict):
        return value

    return {}


def ensure_list(value):
    """
    Return a list.

    Supports:
        list
        dict containing common list keys

    Prevents strings/dicts from accidentally being
    iterated as individual records.
    """

    if isinstance(value, list):
        return value

    if isinstance(value, dict):

        possible_keys = [
            "events",
            "timeline",
            "records",
            "evidence",
            "items",
            "data",
            "findings",
            "results",
        ]

        for key in possible_keys:

            candidate = value.get(key)

            if isinstance(candidate, list):
                return candidate

    return []


def normalize_record_list(value):
    """
    Convert a collection into a list containing only dictionaries.

    Non-dictionary entries are ignored safely.

    This is the main protection against:

        AttributeError:
        'list' object has no attribute 'get'
    """

    raw_items = ensure_list(value)

    normalized = []

    for item in raw_items:

        if isinstance(item, dict):
            normalized.append(item)

        elif isinstance(item, list):
            # Some generators may accidentally create nested lists.
            # Flatten one level and retain dictionary records.
            for nested_item in item:

                if isinstance(nested_item, dict):
                    normalized.append(nested_item)

        else:
            # Ignore strings/numbers/etc.
            continue

    return normalized


# ============================================================
# ACTIVE CASE
# ============================================================

def load_active_case():

    path = (
        CASES_DIR /
        "active_case.json"
    )

    return ensure_dict(
        load_json(path)
    )


def get_case_directory():

    active_case = load_active_case()

    if not active_case:
        return None

    case_id = active_case.get(
        "case_id"
    )

    if not case_id:
        return None

    case_dir = CASES_DIR / str(case_id)

    if not case_dir.exists():
        return None

    return case_dir


# ============================================================
# LOAD PHASE OUTPUTS
# ============================================================

def load_command_center():

    path = (
        OUTPUT_DIR /
        "command_center.json"
    )

    return load_json(path)


def load_evidence_ledger():

    path = (
        OUTPUT_DIR /
        "evidence_ledger.json"
    )

    return load_json(path)


def load_timeline():

    path = (
        OUTPUT_DIR /
        "investigation_timeline.json"
    )

    return load_json(path)


# ============================================================
# CASE INFORMATION
# ============================================================

def get_case_information():

    active_case = load_active_case()

    case_dir = get_case_directory()

    manifest = {}

    if case_dir:

        manifest_path = (
            case_dir /
            "case_manifest.json"
        )

        manifest = ensure_dict(
            load_json(manifest_path)
        )

    return {
        "case_id":
            active_case.get(
                "case_id",
                manifest.get(
                    "case_id",
                    "UNKNOWN"
                )
            ),

        "case_title":
            active_case.get(
                "case_title",
                manifest.get(
                    "case_title",
                    "Cyber-Fraud Investigation"
                )
            ),

        "status":
            active_case.get(
                "status",
                "ACTIVE"
            ),

        "data_class":
            active_case.get(
                "data_class",
                "SYNTHETIC_DEMO"
            ),

        "created_at":
            active_case.get(
                "created_at",
                ""
            ),

        "manifest":
            manifest,
    }


# ============================================================
# EVIDENCE SUMMARY
# ============================================================

def build_evidence_summary(evidence):

    evidence = normalize_record_list(
        evidence
    )

    summary = {
        "total": len(evidence),
        "CDR": 0,
        "UPI": 0,
        "COMPLAINT": 0,
        "DEVICE": 0,
        "OBSERVED": 0,
    }

    for item in evidence:

        evidence_type = str(
            item.get(
                "evidence_type",
                ""
            )
        ).upper()

        status = str(
            item.get(
                "evidence_status",
                ""
            )
        ).upper()

        if evidence_type in summary:

            summary[
                evidence_type
            ] += 1

        if status == "OBSERVED":

            summary[
                "OBSERVED"
            ] += 1

    return summary


# ============================================================
# TIMELINE NORMALIZATION
# ============================================================

def normalize_timeline(timeline):

    """
    Handles several possible timeline JSON formats.

    Supported examples:

        [
            {...},
            {...}
        ]

    or:

        {
            "timeline": [
                {...},
                {...}
            ]
        }

    or:

        {
            "events": [
                {...},
                {...}
            ]
        }

    Nested lists are also handled.
    """

    return normalize_record_list(
        timeline
    )


# ============================================================
# TIMELINE SUMMARY
# ============================================================

def build_timeline_summary(timeline=None):
    """
    Build a robust summary from investigation timeline data.

    Handles:
    - list of dictionaries
    - nested lists
    - dictionary wrappers such as {"events": [...]}
    - missing / malformed timeline data
    """

    calls = 0
    transactions = 0
    complaints = 0
    devices = 0
    total_amount = 0.0
    timestamps = []

    # ------------------------------------------------------------
    # Get timeline data
    # ------------------------------------------------------------
    if timeline is None:
        # Do NOT call load_timeline() because this project version
        # does not define that function.

        # Try to obtain timeline from the module-level variable if
        # your existing file already defines one.
        timeline = globals().get("timeline")

        # If no global timeline exists, try the known JSON file.
        if timeline is None:
            timeline_file = DATA_DIR / "investigation_timeline.json"

            try:
                if timeline_file.exists():
                    with open(timeline_file, "r", encoding="utf-8") as f:
                        timeline = json.load(f)
                else:
                    timeline = []
            except (OSError, json.JSONDecodeError):
                timeline = []

    # ------------------------------------------------------------
    # Handle dictionary wrappers
    # ------------------------------------------------------------
    if isinstance(timeline, dict):

        possible_keys = (
            "timeline",
            "events",
            "records",
            "items",
            "data",
        )

        extracted = None

        for key in possible_keys:
            value = timeline.get(key)

            if isinstance(value, list):
                extracted = value
                break

        timeline = extracted if extracted is not None else []

    # ------------------------------------------------------------
    # Make sure timeline is a list
    # ------------------------------------------------------------
    if not isinstance(timeline, list):
        timeline = []

    # ------------------------------------------------------------
    # Flatten nested timeline lists
    # ------------------------------------------------------------
    normalized_events = []

    for item in timeline:

        if isinstance(item, dict):
            normalized_events.append(item)

        elif isinstance(item, list):

            for nested_item in item:

                if isinstance(nested_item, dict):
                    normalized_events.append(nested_item)

    # ------------------------------------------------------------
    # Analyze events
    # ------------------------------------------------------------
    for event in normalized_events:

        event_type = str(
            event.get("event_type", "")
        ).strip().upper()

        # Support alternate field name
        if not event_type:
            event_type = str(
                event.get("type", "")
            ).strip().upper()

        # --------------------------------------------------------
        # Calls
        # --------------------------------------------------------
        if event_type in (
            "CALL",
            "PHONE_CALL",
            "CALL_EVENT",
        ):
            calls += 1

        # --------------------------------------------------------
        # Transactions
        # --------------------------------------------------------
        elif event_type in (
            "TRANSACTION",
            "PAYMENT",
            "TRANSFER",
            "TRANSACTION_EVENT",
        ):
            transactions += 1

            amount = event.get("amount_inr", 0)

            if amount in (None, ""):
                amount = event.get("amount", 0)

            try:
                total_amount += float(amount)
            except (TypeError, ValueError):
                pass

        # --------------------------------------------------------
        # Complaints
        # --------------------------------------------------------
        elif event_type in (
            "COMPLAINT",
            "COMPLAINT_EVENT",
        ):
            complaints += 1

        # --------------------------------------------------------
        # Device observations
        # --------------------------------------------------------
        elif event_type in (
            "DEVICE",
            "DEVICE_EVENT",
            "DEVICE_OBSERVATION",
            "DEVICE_OBSERVATION_EVENT",
        ):
            devices += 1

        # --------------------------------------------------------
        # Timestamp
        # --------------------------------------------------------
        timestamp = (
            event.get("timestamp")
            or event.get("time")
            or event.get("datetime")
            or event.get("date")
        )

        if timestamp:
            timestamps.append(str(timestamp))

    # ------------------------------------------------------------
    # Sort timestamps
    # ------------------------------------------------------------
    timestamps.sort()

    # ------------------------------------------------------------
    # Final summary
    # ------------------------------------------------------------
    return {
        "total_events": len(normalized_events),
        "calls": calls,
        "transactions": transactions,
        "complaints": complaints,
        "device_observations": devices,
        "total_transaction_amount": total_amount,
        "first_event": timestamps[0] if timestamps else "",
        "last_event": timestamps[-1] if timestamps else "",
    }

    timeline = normalize_timeline(
        timeline
    )

    calls = 0
    transactions = 0
    complaints = 0
    devices = 0

    total_amount = 0.0

    timestamps = []

    for event in timeline:

        # ----------------------------------------------------
        # EXTRA SAFETY
        # ----------------------------------------------------

        if not isinstance(event, dict):
            continue

        event_type = str(
            event.get(
                "event_type",
                ""
            )
        ).upper()

        # ----------------------------------------------------
        # EVENT COUNTS
        # ----------------------------------------------------

        if event_type == "CALL":

            calls += 1

        elif event_type == "TRANSACTION":

            transactions += 1

            try:

                total_amount += float(
                    event.get(
                        "amount_inr",
                        0
                    )
                )

            except (
                TypeError,
                ValueError
            ):

                pass

        elif event_type == "COMPLAINT":

            complaints += 1

        elif event_type in (
            "DEVICE_OBSERVATION",
            "DEVICE",
            "DEVICE_EVENT"
        ):

            devices += 1

        # ----------------------------------------------------
        # TIMESTAMP
        # ----------------------------------------------------

        timestamp = event.get(
            "timestamp",
            ""
        )

        if timestamp:

            timestamps.append(
                str(timestamp)
            )

    timestamps.sort()

    return {

        "total_events":
            len(timeline),

        "calls":
            calls,

        "transactions":
            transactions,

        "complaints":
            complaints,

        "device_observations":
            devices,

        "total_transaction_amount":
            total_amount,

        "first_event":
            timestamps[0]
            if timestamps
            else "",

        "last_event":
            timestamps[-1]
            if timestamps
            else "",
    }


# ============================================================
# FINANCIAL ANALYSIS
# ============================================================

def build_financial_analysis(timeline):

    timeline = normalize_timeline(
        timeline
    )

    transactions = []

    total = 0.0

    largest = None

    recipients = {}

    for event in timeline:

        if not isinstance(event, dict):
            continue

        if str(
            event.get(
                "event_type",
                ""
            )
        ).upper() != "TRANSACTION":

            continue

        try:

            amount = float(
                event.get(
                    "amount_inr",
                    0
                )
            )

        except (
            TypeError,
            ValueError
        ):

            continue

        sender = event.get(
            "actor",
            event.get(
                "sender",
                ""
            )
        )

        receiver = event.get(
            "target",
            event.get(
                "receiver",
                ""
            )
        )

        transaction = {

            "transaction_id":
                event.get(
                    "event_id",
                    event.get(
                        "transaction_id",
                        ""
                    )
                ),

            "evidence_id":
                event.get(
                    "evidence_id",
                    ""
                ),

            "timestamp":
                event.get(
                    "timestamp",
                    ""
                ),

            "sender":
                sender,

            "receiver":
                receiver,

            "amount_inr":
                amount,
        }

        transactions.append(
            transaction
        )

        total += amount

        if receiver:

            recipients[
                str(receiver)
            ] = (
                recipients.get(
                    str(receiver),
                    0
                ) + amount
            )

        if (
            largest is None
            or amount >
            largest["amount_inr"]
        ):

            largest = transaction

    return {

        "transaction_count":
            len(transactions),

        "total_amount_inr":
            total,

        "largest_transaction":
            largest,

        "recipients":
            [
                {
                    "account":
                        account,

                    "total_received_inr":
                        amount,
                }

                for account, amount

                in sorted(
                    recipients.items(),
                    key=lambda x: x[1],
                    reverse=True
                )
            ],

        "transactions":
            transactions,
    }


# ============================================================
# COMMAND CENTER FINDINGS
# ============================================================

def extract_findings(command_center):

    findings = []

    # --------------------------------------------------------
    # COMMAND CENTER MAY BE DICT
    # --------------------------------------------------------

    if isinstance(
        command_center,
        dict
    ):

        raw_findings = (
            command_center.get(
                "findings",
                []
            )
        )

        if isinstance(
            raw_findings,
            list
        ):

            findings = raw_findings

        elif isinstance(
            raw_findings,
            dict
        ):

            findings = [
                raw_findings
            ]

    # --------------------------------------------------------
    # OR COMMAND CENTER ITSELF MAY BE A LIST
    # --------------------------------------------------------

    elif isinstance(
        command_center,
        list
    ):

        findings = command_center

    return findings


# ============================================================
# SAFE FINDINGS
# ============================================================

def build_investigative_findings(
    command_center,
    evidence_summary,
    financial
):

    findings = []

    # --------------------------------------------------------
    # EVIDENCE
    # --------------------------------------------------------

    findings.append({

        "classification":
            "OBSERVED",

        "finding":
            (
                f"{evidence_summary['total']} "
                "evidence records were processed."
            ),

        "support":
            "Evidence ledger",
    })

    # --------------------------------------------------------
    # TRANSACTIONS
    # --------------------------------------------------------

    if financial[
        "transaction_count"
    ] > 0:

        findings.append({

            "classification":
                "OBSERVED",

            "finding":
                (
                    f"{financial['transaction_count']} "
                    "financial transaction records "
                    "were identified."
                ),

            "support":
                "UPI evidence",
        })

    # --------------------------------------------------------
    # TOTAL TRANSACTION VALUE
    # --------------------------------------------------------

    if financial[
        "total_amount_inr"
    ] > 0:

        findings.append({

            "classification":
                "DERIVED",

            "finding":
                (
                    "The total value of transactions "
                    "represented in the processed "
                    "timeline is "
                    f"INR {financial['total_amount_inr']:,.2f}."
                ),

            "support":
                "UPI transaction aggregation",
        })

    # --------------------------------------------------------
    # RECIPIENT COUNT
    # --------------------------------------------------------

    if len(
        financial["recipients"]
    ) > 1:

        findings.append({

            "classification":
                "DERIVED",

            "finding":
                (
                    "Transactions were associated "
                    "with "
                    f"{len(financial['recipients'])} "
                    "distinct recipient entities."
                ),

            "support":
                "UPI transaction graph",
        })

    # --------------------------------------------------------
    # LARGEST TRANSACTION
    # --------------------------------------------------------

    if (
        financial["largest_transaction"]
        is not None
    ):

        largest = financial[
            "largest_transaction"
        ]

        findings.append({

            "classification":
                "DERIVED",

            "finding":
                (
                    "The largest observed transaction "
                    "was "
                    f"INR {largest['amount_inr']:,.2f}."
                ),

            "support":
                largest.get(
                    "evidence_id",
                    "UPI transaction"
                ),
        })

    # --------------------------------------------------------
    # COMMAND CENTER FINDINGS
    # --------------------------------------------------------

    raw_findings = extract_findings(
        command_center
    )

    for finding in raw_findings:

        # ----------------------------------------------------
        # DICTIONARY FINDING
        # ----------------------------------------------------

        if isinstance(
            finding,
            dict
        ):

            classification = finding.get(
                "classification",
                finding.get(
                    "type",
                    "ANALYTICAL INFERENCE"
                )
            )

            text = finding.get(
                "finding",
                finding.get(
                    "message",
                    str(finding)
                )
            )

        # ----------------------------------------------------
        # NON-DICT FINDING
        # ----------------------------------------------------

        else:

            classification = (
                "ANALYTICAL INFERENCE"
            )

            text = str(
                finding
            )

        findings.append({

            "classification":
                str(classification),

            "finding":
                str(text),

            "support":
                "Command Center",
        })

    return findings


# ============================================================
# RECOMMENDED ACTIONS
# ============================================================

def build_recommended_actions(
    evidence_summary,
    financial
):

    actions = []

    # --------------------------------------------------------
    # EVIDENCE PRESERVATION
    # --------------------------------------------------------

    if evidence_summary[
        "total"
    ] > 0:

        actions.append({

            "priority":
                "HIGH",

            "action":
                (
                    "Preserve the original evidence "
                    "files and associated integrity "
                    "metadata."
                ),

            "reason":
                "Evidence preservation",
        })

    # --------------------------------------------------------
    # FINANCIAL TRACEABILITY
    # --------------------------------------------------------

    if financial[
        "transaction_count"
    ] > 0:

        actions.append({

            "priority":
                "HIGH",

            "action":
                (
                    "Review the identified financial "
                    "transactions and associated "
                    "accounts against the underlying "
                    "UPI evidence."
                ),

            "reason":
                "Financial traceability",
        })

    # --------------------------------------------------------
    # NETWORK ANALYSIS
    # --------------------------------------------------------

    if financial[
        "recipients"
    ]:

        actions.append({

            "priority":
                "MEDIUM",

            "action":
                (
                    "Review recipient accounts and "
                    "their relationships with other "
                    "entities in the investigation graph."
                ),

            "reason":
                "Network analysis",
        })

    # --------------------------------------------------------
    # INFRASTRUCTURE CORRELATION
    # --------------------------------------------------------

    actions.append({

        "priority":
            "MEDIUM",

        "action":
            (
                "Correlate relevant phone, device and "
                "tower evidence with the timeline."
            ),

        "reason":
            "Infrastructure correlation",
    })

    # --------------------------------------------------------
    # HUMAN VERIFICATION
    # --------------------------------------------------------

    actions.append({

        "priority":
            "MEDIUM",

        "action":
            (
                "Verify analytical findings against "
                "the underlying source records before "
                "taking investigative or legal action."
            ),

        "reason":
            "Human verification",
    })

    return actions


# ============================================================
# BUILD FINAL BRIEF
# ============================================================

def build_case_brief():

    # --------------------------------------------------------
    # LOAD DATA
    # --------------------------------------------------------

    case_info = (
        get_case_information()
    )

    command_center = (
        load_command_center()
    )

    evidence_raw = (
        load_evidence_ledger()
    )

    timeline_raw = (
        load_timeline()
    )

    # --------------------------------------------------------
    # NORMALIZE DATA
    # --------------------------------------------------------

    evidence = normalize_record_list(
        evidence_raw
    )

    timeline = normalize_timeline(
        timeline_raw
    )

    # --------------------------------------------------------
    # SUMMARIES
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

    financial = (
        build_financial_analysis(
            timeline
        )
    )

    # --------------------------------------------------------
    # FINDINGS
    # --------------------------------------------------------

    findings = (
        build_investigative_findings(
            command_center,
            evidence_summary,
            financial
        )
    )

    # --------------------------------------------------------
    # ACTIONS
    # --------------------------------------------------------

    actions = (
        build_recommended_actions(
            evidence_summary,
            financial
        )
    )

    # --------------------------------------------------------
    # TIMESTAMP
    # --------------------------------------------------------

    generated_at = (
        datetime.now().isoformat(
            timespec="seconds"
        )
    )

    # --------------------------------------------------------
    # FINAL BRIEF
    # --------------------------------------------------------

    brief = {

        "report_metadata": {

            "report_title":
                "Chanakya-Graph "
                "Investigation Case Brief",

            "generated_at":
                generated_at,

            "report_type":
                "AI-assisted investigation brief",

            "status":
                "DRAFT_FOR_HUMAN_REVIEW",

            "automated_guilt_determination":
                False,
        },

        "case_information":
            case_info,

        "evidence_summary":
            evidence_summary,

        "timeline_summary":
            timeline_summary,

        "financial_analysis":
            financial,

        "investigative_findings":
            findings,

        "recommended_actions":
            actions,

        "methodology": {

            "observed":
                (
                    "Directly recorded in the "
                    "processed evidence."
                ),

            "derived":
                (
                    "Calculated or aggregated from "
                    "observed evidence."
                ),

            "analytical_inference":
                (
                    "Investigator-oriented interpretation "
                    "that requires human verification."
                ),
        },

        "limitations": [

            (
                "This report is generated from the "
                "processed case dataset."
            ),

            (
                "Analytical findings do not by "
                "themselves establish wrongdoing."
            ),

            (
                "Synthetic or demonstration datasets "
                "must not be represented as real "
                "law-enforcement records."
            ),

            (
                "Any legal classification or "
                "investigative action should be "
                "validated by the appropriate "
                "authorized investigator."
            ),
        ],
    }

    return brief


# ============================================================
# SAVE JSON REPORT
# ============================================================

def save_json_report(brief):

    path = (
        OUTPUT_DIR /
        "final_case_brief.json"
    )

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            brief,
            f,
            indent=2,
            ensure_ascii=False
        )

    return path


# ============================================================
# TEXT REPORT
# ============================================================

def build_text_report(brief):

    case = brief[
        "case_information"
    ]

    evidence = brief[
        "evidence_summary"
    ]

    timeline = brief[
        "timeline_summary"
    ]

    financial = brief[
        "financial_analysis"
    ]

    findings = brief[
        "investigative_findings"
    ]

    actions = brief[
        "recommended_actions"
    ]

    lines = []

    # ========================================================
    # HEADER
    # ========================================================

    lines.append(
        "=" * 75
    )

    lines.append(
        "CHANAKYA-GRAPH"
    )

    lines.append(
        "FINAL INVESTIGATION CASE BRIEF"
    )

    lines.append(
        "=" * 75
    )

    lines.append("")

    lines.append(
        "REPORT STATUS: DRAFT FOR HUMAN REVIEW"
    )

    lines.append("")

    # ========================================================
    # CASE INFORMATION
    # ========================================================

    lines.append(
        "1. CASE INFORMATION"
    )

    lines.append(
        "-" * 75
    )

    lines.append(
        f"Case ID       : "
        f"{case.get('case_id', '')}"
    )

    lines.append(
        f"Case Title    : "
        f"{case.get('case_title', '')}"
    )

    lines.append(
        f"Case Status   : "
        f"{case.get('status', '')}"
    )

    lines.append(
        f"Data Class    : "
        f"{case.get('data_class', '')}"
    )

    lines.append(
        f"Created At    : "
        f"{case.get('created_at', '')}"
    )

    lines.append("")

    # ========================================================
    # EVIDENCE SUMMARY
    # ========================================================

    lines.append(
        "2. EVIDENCE SUMMARY"
    )

    lines.append(
        "-" * 75
    )

    lines.append(
        f"Total Evidence : "
        f"{evidence['total']}"
    )

    lines.append(
        f"CDR            : "
        f"{evidence['CDR']}"
    )

    lines.append(
        f"UPI            : "
        f"{evidence['UPI']}"
    )

    lines.append(
        f"Complaints     : "
        f"{evidence['COMPLAINT']}"
    )

    lines.append(
        f"Devices        : "
        f"{evidence['DEVICE']}"
    )

    lines.append(
        f"Observed       : "
        f"{evidence['OBSERVED']}"
    )

    lines.append("")

    # ========================================================
    # TIMELINE
    # ========================================================

    lines.append(
        "3. TIMELINE SUMMARY"
    )

    lines.append(
        "-" * 75
    )

    lines.append(
        f"Total Events   : "
        f"{timeline['total_events']}"
    )

    lines.append(
        f"Calls          : "
        f"{timeline['calls']}"
    )

    lines.append(
        f"Transactions   : "
        f"{timeline['transactions']}"
    )

    lines.append(
        f"Complaints     : "
        f"{timeline['complaints']}"
    )

    lines.append(
        f"Device Events  : "
        f"{timeline['device_observations']}"
    )

    lines.append(
        f"Transaction Value : "
        f"INR {timeline['total_transaction_amount']:,.2f}"
    )

    lines.append(
        f"First Event    : "
        f"{timeline['first_event']}"
    )

    lines.append(
        f"Last Event     : "
        f"{timeline['last_event']}"
    )

    lines.append("")

    # ========================================================
    # FINANCIAL ANALYSIS
    # ========================================================

    lines.append(
        "4. FINANCIAL ANALYSIS"
    )

    lines.append(
        "-" * 75
    )

    lines.append(
        f"Transactions   : "
        f"{financial['transaction_count']}"
    )

    lines.append(
        f"Total Value    : "
        f"INR {financial['total_amount_inr']:,.2f}"
    )

    largest = (
        financial[
            "largest_transaction"
        ]
    )

    if largest:

        lines.append(
            f"Largest        : "
            f"INR {largest['amount_inr']:,.2f}"
        )

        lines.append(
            f"Largest TXN    : "
            f"{largest['transaction_id']}"
        )

        lines.append(
            f"Evidence ID    : "
            f"{largest['evidence_id']}"
        )

        lines.append(
            f"Sender         : "
            f"{largest['sender']}"
        )

        lines.append(
            f"Receiver       : "
            f"{largest['receiver']}"
        )

    lines.append("")

    # ========================================================
    # FINDINGS
    # ========================================================

    lines.append(
        "5. INVESTIGATIVE FINDINGS"
    )

    lines.append(
        "-" * 75
    )

    if not findings:

        lines.append(
            "No investigative findings available."
        )

    else:

        for index, finding in enumerate(
            findings,
            start=1
        ):

            classification = finding.get(
                "classification",
                "UNKNOWN"
            )

            finding_text = finding.get(
                "finding",
                ""
            )

            support = finding.get(
                "support",
                ""
            )

            lines.append(
                f"{index}. "
                f"[{classification}] "
                f"{finding_text}"
            )

            lines.append(
                f"   Support: "
                f"{support}"
            )

    lines.append("")

    # ========================================================
    # RECIPIENTS
    # ========================================================

    lines.append(
        "6. IDENTIFIED RECIPIENT ACCOUNTS"
    )

    lines.append(
        "-" * 75
    )

    recipients = financial.get(
        "recipients",
        []
    )

    if not recipients:

        lines.append(
            "No recipient accounts identified."
        )

    else:

        for item in recipients:

            lines.append(
                f"- {item['account']} : "
                f"INR {item['total_received_inr']:,.2f}"
            )

    lines.append("")

    # ========================================================
    # ACTIONS
    # ========================================================

    lines.append(
        "7. RECOMMENDED INVESTIGATIVE ACTIONS"
    )

    lines.append(
        "-" * 75
    )

    for index, action in enumerate(
        actions,
        start=1
    ):

        lines.append(
            f"{index}. "
            f"[{action['priority']}] "
            f"{action['action']}"
        )

        lines.append(
            f"   Reason: "
            f"{action['reason']}"
        )

    lines.append("")

    # ========================================================
    # LIMITATIONS
    # ========================================================

    lines.append(
        "8. LIMITATIONS"
    )

    lines.append(
        "-" * 75
    )

    for limitation in brief[
        "limitations"
    ]:

        lines.append(
            f"- {limitation}"
        )

    lines.append("")

    # ========================================================
    # FOOTER
    # ========================================================

    lines.append(
        "=" * 75
    )

    lines.append(
        "END OF REPORT"
    )

    lines.append(
        "=" * 75
    )

    return "\n".join(
        lines
    )


# ============================================================
# SAVE TEXT REPORT
# ============================================================

def save_text_report(report):

    path = (
        OUTPUT_DIR /
        "final_case_brief.txt"
    )

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(
            report
        )

    return path


# ============================================================
# DIAGNOSTIC INFORMATION
# ============================================================

def print_input_diagnostics():

    print("")
    print(
        "INPUT DATA CHECK"
    )
    print(
        "-" * 75
    )

    # --------------------------------------------------------
    # Timeline
    # --------------------------------------------------------

    timeline_path = (
        OUTPUT_DIR /
        "investigation_timeline.json"
    )

    if timeline_path.exists():

        timeline_raw = load_json(
            timeline_path
        )

        print(
            f"Timeline file : {timeline_path}"
        )

        print(
            f"Timeline JSON type : "
            f"{type(timeline_raw).__name__}"
        )

        if isinstance(
            timeline_raw,
            list
        ):

            print(
                f"Timeline raw items : "
                f"{len(timeline_raw)}"
            )

            dict_count = sum(
                1
                for item in timeline_raw
                if isinstance(
                    item,
                    dict
                )
            )

            print(
                f"Dictionary events : "
                f"{dict_count}"
            )

            print(
                f"Ignored non-dict items : "
                f"{len(timeline_raw) - dict_count}"
            )

        elif isinstance(
            timeline_raw,
            dict
        ):

            print(
                "Timeline is a wrapped dictionary."
            )

    else:

        print(
            f"[WARNING] Timeline file does not exist:"
        )

        print(
            timeline_path
        )

    # --------------------------------------------------------
    # Evidence
    # --------------------------------------------------------

    evidence_path = (
        OUTPUT_DIR /
        "evidence_ledger.json"
    )

    print("")

    if evidence_path.exists():

        evidence_raw = load_json(
            evidence_path
        )

        print(
            f"Evidence file : {evidence_path}"
        )

        print(
            f"Evidence JSON type : "
            f"{type(evidence_raw).__name__}"
        )

        evidence = normalize_record_list(
            evidence_raw
        )

        print(
            f"Usable evidence records : "
            f"{len(evidence)}"
        )

    else:

        print(
            "[WARNING] Evidence ledger not found."
        )

    print(
        "-" * 75
    )


# ============================================================
# RUN PHASE 16
# ============================================================

def run_phase16():

    print("=" * 75)

    print(
        "CHANAKYA-GRAPH — PHASE 16"
    )

    print(
        "FINAL EVIDENCE-LINKED CASE BRIEF"
    )

    print("=" * 75)

    # --------------------------------------------------------
    # Diagnostics
    # --------------------------------------------------------

    print_input_diagnostics()

    print("")

    try:

        # ----------------------------------------------------
        # BUILD
        # ----------------------------------------------------

        brief = build_case_brief()

        # ----------------------------------------------------
        # SAVE JSON
        # ----------------------------------------------------

        json_path = (
            save_json_report(
                brief
            )
        )

        # ----------------------------------------------------
        # BUILD TEXT
        # ----------------------------------------------------

        text_report = (
            build_text_report(
                brief
            )
        )

        # ----------------------------------------------------
        # SAVE TEXT
        # ----------------------------------------------------

        text_path = (
            save_text_report(
                text_report
            )
        )

        # ----------------------------------------------------
        # DISPLAY SUMMARY
        # ----------------------------------------------------

        case = brief[
            "case_information"
        ]

        evidence = brief[
            "evidence_summary"
        ]

        timeline = brief[
            "timeline_summary"
        ]

        financial = brief[
            "financial_analysis"
        ]

        print("")

        print(
            "REPORT GENERATED SUCCESSFULLY"
        )

        print(
            "-" * 75
        )

        print(
            f"Case ID           : "
            f"{case.get('case_id', 'UNKNOWN')}"
        )

        print(
            f"Evidence Records  : "
            f"{evidence['total']}"
        )

        print(
            f"Timeline Events   : "
            f"{timeline['total_events']}"
        )

        print(
            f"Calls             : "
            f"{timeline['calls']}"
        )

        print(
            f"Transactions      : "
            f"{financial['transaction_count']}"
        )

        print(
            f"Transaction Value : "
            f"INR {financial['total_amount_inr']:,.2f}"
        )
        

        print(
            f"JSON Report       : "
            f"{json_path}"
        )

        print(
            f"Text Report       : "
            f"{text_path}"
        )

        print(
            "-" * 75
        )

        print(
            "PHASE 16 COMPLETE"
        )

        print("=" * 75)

        return brief

    except Exception as exc:

        print("")
        print(
            "[ERROR] Phase 16 failed."
        )

        print(
            f"Reason: {exc}"
        )

        print(
            "-" * 75
        )

        print(
            "Check the input files listed above."
        )

        print(
            "The timeline loader now ignores "
            "non-dictionary records."
        )

        print(
            "-" * 75
        )

        raise


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    run_phase16()