import json
import sys
from pathlib import Path
from datetime import datetime

import pandas as pd


# ============================================================
# WINDOWS CONSOLE UTF-8 SAFETY
# ============================================================

try:
    sys.stdout.reconfigure(
        encoding="utf-8",
        errors="replace"
    )
    sys.stderr.reconfigure(
        encoding="utf-8",
        errors="replace"
    )
except Exception:
    pass


# ============================================================
# PATHS
# ============================================================

SRC_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = SRC_DIR / "data"
CASES_DIR = DATA_DIR / "cases"

OUTPUT_DIR = SRC_DIR / "output" / "investigation"

TIMELINE_FILE = (
    OUTPUT_DIR / "investigation_timeline.json"
)

ACTIVE_CASE_FILE = (
    CASES_DIR / "active_case.json"
)


# ============================================================
# ACTIVE CASE
# ============================================================

def get_active_case_id():

    if not ACTIVE_CASE_FILE.exists():
        raise RuntimeError(
            f"Active case file not found:\n"
            f"{ACTIVE_CASE_FILE}"
        )

    with open(
        ACTIVE_CASE_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        data = json.load(file)

    case_id = data.get("case_id")

    if not case_id:
        raise RuntimeError(
            "Active case ID is missing."
        )

    return case_id


# ============================================================
# CASE DIRECTORY
# ============================================================

def get_case_directory():

    case_id = get_active_case_id()

    case_dir = CASES_DIR / case_id

    if not case_dir.exists():
        raise RuntimeError(
            f"Case directory not found:\n"
            f"{case_dir}"
        )

    return case_dir


# ============================================================
# LOAD CSV
# ============================================================

def load_csv(path):

    if not path.exists():
        raise FileNotFoundError(
            f"Evidence file not found:\n{path}"
        )

    df = pd.read_csv(path)

    return df


# ============================================================
# SAFE VALUE
# ============================================================

def safe_value(value):

    if pd.isna(value):
        return None

    return value


# ============================================================
# NORMALIZE TIMESTAMP
# ============================================================

def normalize_timestamp(value):

    if pd.isna(value):
        return None

    try:

        timestamp = pd.to_datetime(
            value,
            errors="coerce"
        )

        if pd.isna(timestamp):
            return None

        return timestamp.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    except Exception:

        return str(value)


# ============================================================
# BUILD CDR EVENTS
# ============================================================

def build_cdr_events(df):

    events = []

    for _, row in df.iterrows():

        evidence_id = safe_value(
            row.get("record_id")
        )

        event = {
            "event_id": evidence_id,
            "event_type": "CALL",
            "timestamp": normalize_timestamp(
                row.get("timestamp")
            ),
            "evidence_id": evidence_id,

            "source": safe_value(
                row.get("caller")
            ),

            "target": safe_value(
                row.get("called")
            ),

            "caller": safe_value(
                row.get("caller")
            ),

            "called": safe_value(
                row.get("called")
            ),

            "duration_seconds": safe_value(
                row.get("duration_seconds")
            ),

            "imei": safe_value(
                row.get("imei")
            ),

            "tower_id": safe_value(
                row.get("tower_id")
            ),

            "call_type": safe_value(
                row.get("call_type")
            ),

            "source_type": "CDR",
            "evidence_status": "OBSERVED"
        }

        events.append(event)

    return events


# ============================================================
# BUILD UPI EVENTS
# ============================================================

def build_upi_events(df):

    events = []

    for _, row in df.iterrows():

        evidence_id = safe_value(
            row.get("transaction_id")
        )

        amount = safe_value(
            row.get("amount_inr")
        )

        try:

            if amount is not None:
                amount = float(amount)

        except Exception:
            pass

        event = {
            "event_id": evidence_id,
            "event_type": "TRANSACTION",
            "timestamp": normalize_timestamp(
                row.get("timestamp")
            ),
            "evidence_id": evidence_id,

            "transaction_id": evidence_id,

            "source": safe_value(
                row.get("sender_account")
            ),

            "target": safe_value(
                row.get("receiver_account")
            ),

            "sender_account": safe_value(
                row.get("sender_account")
            ),

            "receiver_account": safe_value(
                row.get("receiver_account")
            ),

            "sender_type": safe_value(
                row.get("sender_type")
            ),

            "receiver_type": safe_value(
                row.get("receiver_type")
            ),

            "amount_inr": amount,

            "transaction_status": safe_value(
                row.get("transaction_status")
            ),

            "reference_id": safe_value(
                row.get("reference_id")
            ),

            "source_type": "UPI",
            "evidence_status": "OBSERVED"
        }

        events.append(event)

    return events


# ============================================================
# BUILD COMPLAINT EVENTS
# ============================================================

def build_complaint_events(df):

    events = []

    for _, row in df.iterrows():

        evidence_id = safe_value(
            row.get("complaint_id")
        )

        event = {
            "event_id": evidence_id,
            "event_type": "COMPLAINT",
            "timestamp": normalize_timestamp(
                row.get("complaint_timestamp")
            ),
            "evidence_id": evidence_id,

            "complaint_id": evidence_id,

            "victim_name": safe_value(
                row.get("victim_name")
            ),

            "victim_phone": safe_value(
                row.get("victim_phone")
            ),

            "victim_account": safe_value(
                row.get("victim_account")
            ),

            "fraud_category": safe_value(
                row.get("fraud_category")
            ),

            "complaint_description": safe_value(
                row.get("complaint_description")
            ),

            "reported_amount_inr": safe_value(
                row.get("reported_amount_inr")
            ),

            "reported_caller": safe_value(
                row.get("reported_caller")
            ),

            "source_type": "COMPLAINT",
            "evidence_status": "OBSERVED"
        }

        events.append(event)

    return events


# ============================================================
# BUILD DEVICE EVENTS
# ============================================================

def build_device_events(df):

    events = []

    for _, row in df.iterrows():

        evidence_id = safe_value(
            row.get("device_record_id")
        )

        timestamp = normalize_timestamp(
            row.get("first_seen")
        )

        if timestamp is None:

            timestamp = normalize_timestamp(
                row.get("last_seen")
            )

        event = {
            "event_id": evidence_id,
            "event_type": "DEVICE_OBSERVATION",
            "timestamp": timestamp,
            "evidence_id": evidence_id,

            "device_record_id": evidence_id,

            "phone_number": safe_value(
                row.get("phone_number")
            ),

            "imei": safe_value(
                row.get("imei")
            ),

            "device_type": safe_value(
                row.get("device_type")
            ),

            "tower_id": safe_value(
                row.get("tower_id")
            ),

            "first_seen": normalize_timestamp(
                row.get("first_seen")
            ),

            "last_seen": normalize_timestamp(
                row.get("last_seen")
            ),

            "source_type": "DEVICE",
            "evidence_status": "OBSERVED"
        }

        events.append(event)

    return events


# ============================================================
# BUILD TIMELINE
# ============================================================

def build_timeline():

    case_dir = get_case_directory()

    normalized_dir = (
        case_dir / "normalized"
    )

    if not normalized_dir.exists():
        raise RuntimeError(
            f"Normalized directory not found:\n"
            f"{normalized_dir}"
        )

    # --------------------------------------------------------
    # CURRENT FILE NAMES
    # --------------------------------------------------------

    cdr_file = (
        normalized_dir / "cdr_records.csv"
    )

    upi_file = (
        normalized_dir / "upi_transactions.csv"
    )

    complaints_file = (
        normalized_dir / "complaints.csv"
    )

    devices_file = (
        normalized_dir / "device_records.csv"
    )

    # --------------------------------------------------------
    # LOAD
    # --------------------------------------------------------

    cdr_df = load_csv(cdr_file)

    upi_df = load_csv(upi_file)

    complaints_df = load_csv(
        complaints_file
    )

    devices_df = load_csv(
        devices_file
    )

    print(
        f"CDR records          : {len(cdr_df)}"
    )

    print(
        f"UPI transactions     : {len(upi_df)}"
    )

    print(
        f"Complaints           : {len(complaints_df)}"
    )

    print(
        f"Device observations  : {len(devices_df)}"
    )

    # --------------------------------------------------------
    # CREATE EVENTS
    # --------------------------------------------------------

    events = []

    events.extend(
        build_cdr_events(cdr_df)
    )

    events.extend(
        build_upi_events(upi_df)
    )

    events.extend(
        build_complaint_events(
            complaints_df
        )
    )

    events.extend(
        build_device_events(
            devices_df
        )
    )

    # --------------------------------------------------------
    # SORT EVENTS
    # --------------------------------------------------------

    def sort_key(event):

        timestamp = event.get(
            "timestamp"
        )

        if not timestamp:
            return datetime.max

        try:

            return datetime.strptime(
                timestamp,
                "%Y-%m-%d %H:%M:%S"
            )

        except Exception:

            return datetime.max

    events.sort(
        key=sort_key
    )

    # --------------------------------------------------------
    # SEQUENCE NUMBER
    # --------------------------------------------------------

    for number, event in enumerate(
        events,
        start=1
    ):

        event["sequence"] = number

    return events


# ============================================================
# CREATE SUMMARY
# ============================================================

def create_summary(events):

    calls = 0
    transactions = 0
    complaints = 0
    devices = 0

    total_transaction_amount = 0.0

    timestamps = []

    for event in events:

        event_type = event.get(
            "event_type"
        )

        if event_type == "CALL":
            calls += 1

        elif event_type == "TRANSACTION":

            transactions += 1

            amount = event.get(
                "amount_inr"
            )

            try:

                if amount is not None:
                    total_transaction_amount += float(
                        amount
                    )

            except Exception:
                pass

        elif event_type == "COMPLAINT":
            complaints += 1

        elif event_type == "DEVICE_OBSERVATION":
            devices += 1

        timestamp = event.get(
            "timestamp"
        )

        if timestamp:
            timestamps.append(timestamp)

    return {
        "total_events": len(events),
        "calls": calls,
        "transactions": transactions,
        "complaints": complaints,
        "device_observations": devices,
        "total_transaction_amount": (
            total_transaction_amount
        ),
        "first_event": (
            timestamps[0]
            if timestamps
            else None
        ),
        "last_event": (
            timestamps[-1]
            if timestamps
            else None
        )
    }


# ============================================================
# SAVE TIMELINE
# ============================================================

def save_timeline(
    events,
    summary,
    case_id
):

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # Keep timeline as a list because the
    # existing Phase 15 / Phase 16 logic
    # supports this format.

    with open(
        TIMELINE_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            events,
            file,
            indent=2,
            ensure_ascii=False,
            default=str
        )

    return TIMELINE_FILE


# ============================================================
# PRINT SUMMARY
# ============================================================

def print_summary(summary):

    print()

    print(
        f"Total Events        : "
        f"{summary['total_events']}"
    )

    print(
        f"Calls               : "
        f"{summary['calls']}"
    )

    print(
        f"Transactions        : "
        f"{summary['transactions']}"
    )

    print(
        f"Complaints          : "
        f"{summary['complaints']}"
    )

    print(
        f"Device Observations : "
        f"{summary['device_observations']}"
    )

    # IMPORTANT:
    # Use INR instead of the rupee Unicode symbol
    # because Windows CP1252 may not support INR .

    print(
        f"Transaction Amount  : "
        f"INR {summary['total_transaction_amount']:,.2f}"
    )

    if summary["first_event"]:

        print(
            f"First Event         : "
            f"{summary['first_event']}"
        )

    if summary["last_event"]:

        print(
            f"Last Event          : "
            f"{summary['last_event']}"
        )


# ============================================================
# PHASE 14
# ============================================================

def run_phase14():

    print()
    print("=" * 70)
    print(
        "CHANAKYA-GRAPH — PHASE 14"
    )
    print(
        "INVESTIGATION TIMELINE"
    )
    print("=" * 70)

    # --------------------------------------------------------
    # CASE
    # --------------------------------------------------------

    case_id = get_active_case_id()

    print(
        f"Case ID: {case_id}"
    )

    # --------------------------------------------------------
    # BUILD
    # --------------------------------------------------------

    events = build_timeline()

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    summary = create_summary(
        events
    )

    print_summary(
        summary
    )


    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    output = save_timeline(
        events,
        summary,
        case_id
    )

    print()

    print(
        f"Output              : "
        f"{output}"
    )

    print()

    print(
        "PHASE 14 COMPLETE"
    )


# ============================================================
# STREAMLIT TIMELINE HELPERS
# ============================================================

def timeline_summary(timeline):
    """
    Return summary information used by the Streamlit timeline page.
    """

    if not timeline:
        return {
            "total_events": 0,
            "calls": 0,
            "transactions": 0,
            "complaints": 0,
            "device_observations": 0,
            "total_transaction_amount": 0.0,
            "first_event": None,
            "last_event": None,
        }

    calls = sum(
        1 for event in timeline
        if event.get("event_type") == "CALL"
    )

    transactions = sum(
        1 for event in timeline
        if event.get("event_type") == "TRANSACTION"
    )

    complaints = sum(
        1 for event in timeline
        if event.get("event_type") == "COMPLAINT"
    )

    devices = sum(
        1 for event in timeline
        if event.get("event_type") == "DEVICE_OBSERVATION"
    )

    total_amount = 0.0

    for event in timeline:
        if event.get("event_type") == "TRANSACTION":
            try:
                total_amount += float(
                    event.get("amount_inr", 0) or 0
                )
            except (TypeError, ValueError):
                pass

    timestamps = [
        event.get("timestamp")
        for event in timeline
        if event.get("timestamp")
    ]

    timestamps.sort()

    return {
        "total_events": len(timeline),
        "calls": calls,
        "transactions": transactions,
        "complaints": complaints,
        "device_observations": devices,
        "total_transaction_amount": total_amount,
        "first_event": timestamps[0] if timestamps else None,
        "last_event": timestamps[-1] if timestamps else None,
    }


def filter_timeline(timeline, event_type):
    """
    Filter timeline by event type.
    """

    if not timeline:
        return []

    if event_type == "ALL":
        return timeline

    return [
        event
        for event in timeline
        if event.get("event_type") == event_type
    ]


def search_timeline(timeline, query):
    """
    Search timeline across the main evidence fields.
    """

    if not timeline or not query:
        return timeline

    query = str(query).strip().lower()

    if not query:
        return timeline

    results = []

    for event in timeline:

        searchable_values = [
            event.get("event_id", ""),
            event.get("evidence_id", ""),
            event.get("evidence_type", ""),
            event.get("event_type", ""),
            event.get("actor", ""),
            event.get("target", ""),
            event.get("description", ""),
            event.get("timestamp", ""),
        ]

        details = event.get("details", {})

        if isinstance(details, dict):
            searchable_values.extend(
                str(value)
                for value in details.values()
            )

        searchable_text = " ".join(
            str(value)
            for value in searchable_values
            if value is not None
        ).lower()

        if query in searchable_text:
            results.append(event)

    return results


def financial_timeline(timeline):
    """
    Build a transaction-only financial timeline.
    """

    if not timeline:
        return []

    transactions = [
        event
        for event in timeline
        if event.get("event_type") == "TRANSACTION"
    ]

    transactions.sort(
        key=lambda event: str(
            event.get("timestamp", "")
        )
    )

    results = []

    cumulative_amount = 0.0

    for event in transactions:

        try:
            amount = float(
                event.get("amount_inr", 0) or 0
            )
        except (TypeError, ValueError):
            amount = 0.0

        cumulative_amount += amount

        results.append({
            "timestamp": event.get(
                "timestamp",
                ""
            ),

            "transaction_id": event.get(
                "transaction_id",
                event.get("details", {}).get(
                    "transaction_id",
                    ""
                )
            ),

            "sender": event.get(
                "actor",
                event.get("details", {}).get(
                    "sender_account",
                    ""
                )
            ),

            "receiver": event.get(
                "target",
                event.get("details", {}).get(
                    "receiver_account",
                    ""
                )
            ),

            "amount_inr": amount,

            "cumulative_amount_inr":
                cumulative_amount,

            "evidence_id": event.get(
                "evidence_id",
                ""
            ),
        })

    return results

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    run_phase14()