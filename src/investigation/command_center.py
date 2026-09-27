from __future__ import annotations

import json
from pathlib import Path
from collections import Counter
from datetime import datetime
import hashlib

import pandas as pd

import sys

try:
    sys.stdout.reconfigure(
        encoding="utf-8",
        errors="replace"
    )
except Exception:
    pass

try:
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

ACTIVE_CASE_FILE = CASES_DIR / "active_case.json"

OUTPUT_DIR = SRC_DIR / "output" / "investigation"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

COMMAND_CENTER_OUTPUT = OUTPUT_DIR / "command_center.json"


# ============================================================
# EVIDENCE CONFIGURATION
# ============================================================

EVIDENCE_FILES = {
    "cdr": "cdr_records.csv",
    "upi": "upi_transactions.csv",
    "complaints": "complaints.csv",
    "devices": "device_records.csv",
}


# ============================================================
# HELPERS
# ============================================================

def load_json(path: Path) -> dict:
    if not path.exists():
        return {}

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json(data: dict, path: Path):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, default=str)


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(path, dtype=str)
    except Exception:
        return pd.DataFrame()


def safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def normalize(value):
    if value is None:
        return ""

    return str(value).strip()


def unique_nonempty(values):
    return {
        normalize(value)
        for value in values
        if normalize(value)
    }


# ============================================================
# ACTIVE CASE
# ============================================================

def get_active_case():
    """
    Reads src/data/cases/active_case.json and determines
    the active case directory.
    """

    active = load_json(ACTIVE_CASE_FILE)

    if not active:
        return {
            "active": False,
            "case_id": None,
            "case_dir": None,
            "active_case": {},
        }

    case_id = (
        active.get("case_id")
        or active.get("active_case_id")
        or active.get("id")
    )

    if not case_id:
        return {
            "active": False,
            "case_id": None,
            "case_dir": None,
            "active_case": active,
        }

    case_dir = CASES_DIR / case_id

    return {
        "active": case_dir.exists(),
        "case_id": case_id,
        "case_dir": case_dir,
        "active_case": active,
    }


# ============================================================
# CASE MANIFEST
# ============================================================

def load_case_manifest(case_dir: Path):
    manifest_path = case_dir / "case_manifest.json"

    if not manifest_path.exists():
        return {}

    return load_json(manifest_path)


# ============================================================
# EVIDENCE LOADING
# ============================================================

def load_evidence(case_dir: Path):
    normalized_dir = case_dir / "normalized"

    evidence = {}

    for evidence_type, filename in EVIDENCE_FILES.items():
        path = normalized_dir / filename

        evidence[evidence_type] = {
            "path": str(path),
            "exists": path.exists(),
            "data": read_csv(path),
        }

    return evidence


# ============================================================
# EVIDENCE METRICS
# ============================================================

def calculate_evidence_metrics(evidence):
    metrics = {}

    for evidence_type, info in evidence.items():
        dataframe = info["data"]

        metrics[evidence_type] = {
            "records": len(dataframe),
            "available": info["exists"],
            "columns": list(dataframe.columns),
        }

    metrics["total_records"] = sum(
        item["records"]
        for item in metrics.values()
    )

    return metrics


# ============================================================
# ENTITY EXTRACTION
# ============================================================

def extract_entities(evidence):
    phones = set()
    accounts = set()
    imeis = set()
    towers = set()
    persons = set()
    transactions = set()

    cdr = evidence["cdr"]["data"]

    if not cdr.empty:
        for column in ["caller", "called"]:
            if column in cdr.columns:
                phones.update(unique_nonempty(cdr[column]))

        if "imei" in cdr.columns:
            imeis.update(unique_nonempty(cdr["imei"]))

        if "tower_id" in cdr.columns:
            towers.update(unique_nonempty(cdr["tower_id"]))

    upi = evidence["upi"]["data"]

    if not upi.empty:
        for column in ["sender_account", "receiver_account"]:
            if column in upi.columns:
                accounts.update(unique_nonempty(upi[column]))

        if "transaction_id" in upi.columns:
            transactions.update(
                unique_nonempty(upi["transaction_id"])
            )

    complaints = evidence["complaints"]["data"]

    if not complaints.empty:
        if "victim_phone" in complaints.columns:
            phones.update(
                unique_nonempty(complaints["victim_phone"])
            )

        if "victim_account" in complaints.columns:
            accounts.update(
                unique_nonempty(complaints["victim_account"])
            )

        if "victim_name" in complaints.columns:
            persons.update(
                unique_nonempty(complaints["victim_name"])
            )

        if "reported_caller" in complaints.columns:
            phones.update(
                unique_nonempty(complaints["reported_caller"])
            )

    devices = evidence["devices"]["data"]

    if not devices.empty:
        if "phone_number" in devices.columns:
            phones.update(
                unique_nonempty(devices["phone_number"])
            )

        if "imei" in devices.columns:
            imeis.update(
                unique_nonempty(devices["imei"])
            )

        if "tower_id" in devices.columns:
            towers.update(
                unique_nonempty(devices["tower_id"])
            )

    return {
        "phones": sorted(phones),
        "accounts": sorted(accounts),
        "imeis": sorted(imeis),
        "towers": sorted(towers),
        "persons": sorted(persons),
        "transactions": sorted(transactions),
    }


# ============================================================
# CONNECTION ANALYSIS
# ============================================================

def calculate_connections(evidence):
    connections = []

    cdr = evidence["cdr"]["data"]

    if not cdr.empty:
        for _, row in cdr.iterrows():

            caller = normalize(row.get("caller"))
            called = normalize(row.get("called"))

            if caller and called:
                connections.append({
                    "source": caller,
                    "target": called,
                    "relationship": "CALLED",
                    "evidence_type": "CDR",
                    "evidence_id": normalize(
                        row.get("record_id")
                    ),
                    "timestamp": normalize(
                        row.get("timestamp")
                    ),
                })

    upi = evidence["upi"]["data"]

    if not upi.empty:
        for _, row in upi.iterrows():

            sender = normalize(
                row.get("sender_account")
            )

            receiver = normalize(
                row.get("receiver_account")
            )

            if sender and receiver:
                connections.append({
                    "source": sender,
                    "target": receiver,
                    "relationship": "TRANSFERRED_FUNDS",
                    "evidence_type": "UPI",
                    "evidence_id": normalize(
                        row.get("transaction_id")
                    ),
                    "timestamp": normalize(
                        row.get("timestamp")
                    ),
                    "amount_inr": safe_float(
                        row.get("amount_inr")
                    ),
                })

    devices = evidence["devices"]["data"]

    if not devices.empty:
        for _, row in devices.iterrows():

            phone = normalize(
                row.get("phone_number")
            )

            imei = normalize(
                row.get("imei")
            )

            if phone and imei:
                connections.append({
                    "source": phone,
                    "target": imei,
                    "relationship": "ASSOCIATED_WITH_DEVICE",
                    "evidence_type": "DEVICE",
                    "evidence_id": normalize(
                        row.get("device_record_id")
                    ),
                    "timestamp": normalize(
                        row.get("first_seen")
                    ),
                })

    return connections


# ============================================================
# TRANSACTION ANALYSIS
# ============================================================

def calculate_transaction_analysis(evidence):

    upi = evidence["upi"]["data"]

    if upi.empty:
        return {
            "transaction_count": 0,
            "total_amount_inr": 0,
            "average_amount_inr": 0,
            "maximum_transaction": None,
            "unique_senders": 0,
            "unique_receivers": 0,
        }

    amounts = pd.to_numeric(
        upi.get("amount_inr"),
        errors="coerce"
    ).fillna(0)

    total_amount = float(amounts.sum())

    maximum_transaction = None

    if len(upi) > 0:

        max_index = amounts.idxmax()

        row = upi.loc[max_index]

        maximum_transaction = {
            "transaction_id": normalize(
                row.get("transaction_id")
            ),
            "timestamp": normalize(
                row.get("timestamp")
            ),
            "sender": normalize(
                row.get("sender_account")
            ),
            "receiver": normalize(
                row.get("receiver_account")
            ),
            "amount_inr": safe_float(
                row.get("amount_inr")
            ),
        }

    return {
        "transaction_count": len(upi),
        "total_amount_inr": total_amount,
        "average_amount_inr": (
            total_amount / len(upi)
            if len(upi) > 0
            else 0
        ),
        "maximum_transaction": maximum_transaction,
        "unique_senders": (
            upi["sender_account"].nunique()
            if "sender_account" in upi.columns
            else 0
        ),
        "unique_receivers": (
            upi["receiver_account"].nunique()
            if "receiver_account" in upi.columns
            else 0
        ),
    }


# ============================================================
# MONEY FLOW
# ============================================================

def calculate_money_flow(evidence):

    upi = evidence["upi"]["data"]

    if upi.empty:
        return []

    flow = []

    for _, row in upi.iterrows():

        amount = safe_float(
            row.get("amount_inr")
        )

        sender = normalize(
            row.get("sender_account")
        )

        receiver = normalize(
            row.get("receiver_account")
        )

        if not sender or not receiver:
            continue

        flow.append({
            "timestamp": normalize(
                row.get("timestamp")
            ),
            "transaction_id": normalize(
                row.get("transaction_id")
            ),
            "sender": sender,
            "receiver": receiver,
            "amount_inr": amount,
            "sender_type": normalize(
                row.get("sender_type")
            ),
            "receiver_type": normalize(
                row.get("receiver_type")
            ),
        })

    flow.sort(
        key=lambda item: item["timestamp"]
    )

    return flow


# ============================================================
# SHARED INFRASTRUCTURE
# ============================================================

def calculate_shared_devices(evidence):

    devices = evidence["devices"]["data"]

    if devices.empty:
        return []

    if not {
        "phone_number",
        "imei"
    }.issubset(devices.columns):
        return []

    result = []

    grouped = devices.groupby("imei")

    for imei, group in grouped:

        phones = sorted(
            unique_nonempty(
                group["phone_number"]
            )
        )

        if len(phones) > 1:

            result.append({
                "imei": normalize(imei),
                "phone_numbers": phones,
                "phone_count": len(phones),
            })

    return result


def calculate_shared_towers(evidence):

    cdr = evidence["cdr"]["data"]

    if cdr.empty:
        return []

    if not {
        "tower_id",
        "caller"
    }.issubset(cdr.columns):
        return []

    result = []

    grouped = cdr.groupby("tower_id")

    for tower, group in grouped:

        phones = sorted(
            unique_nonempty(
                group["caller"]
            )
        )

        if len(phones) > 1:

            result.append({
                "tower_id": normalize(tower),
                "phone_numbers": phones,
                "phone_count": len(phones),
            })

    return result


# ============================================================
# FINDINGS
# ============================================================

def generate_findings(
    evidence_metrics,
    entities,
    transactions,
    money_flow,
    shared_devices,
    shared_towers,
):

    findings = []

    # --------------------------------------------------------
    # OBSERVED
    # --------------------------------------------------------

    findings.append({
        "type": "OBSERVED",
        "title": "Evidence successfully processed",
        "description": (
            f"{evidence_metrics['total_records']:,} "
            "records are available across the four evidence "
            "categories."
        ),
        "evidence": [
            "CDR",
            "UPI",
            "COMPLAINTS",
            "DEVICES",
        ],
    })

    if transactions["transaction_count"] > 0:

        findings.append({
            "type": "OBSERVED",
            "title": "Financial transactions identified",
            "description": (
                f"{transactions['transaction_count']:,} "
                "UPI transaction records were identified."
            ),
            "evidence": ["UPI"],
        })

    # --------------------------------------------------------
    # DERIVED
    # --------------------------------------------------------

    findings.append({
        "type": "DERIVED",
        "title": "Unique entity inventory",
        "description": (
            f"{len(entities['phones'])} phones, "
            f"{len(entities['accounts'])} accounts, "
            f"{len(entities['imeis'])} IMEIs and "
            f"{len(entities['towers'])} towers were "
            "identified from the available evidence."
        ),
        "evidence": [
            "CDR",
            "UPI",
            "DEVICES",
            "COMPLAINTS",
        ],
    })

    if transactions["unique_receivers"] > 1:

        findings.append({
            "type": "DERIVED",
            "title": "Multiple transaction recipients",
            "description": (
                f"Funds were transferred to "
                f"{transactions['unique_receivers']} "
                "unique recipient accounts."
            ),
            "evidence": ["UPI"],
        })

    if shared_devices:

        findings.append({
            "type": "DERIVED",
            "title": "Shared device associations",
            "description": (
                f"{len(shared_devices)} IMEI association(s) "
                "are linked to multiple phone numbers."
            ),
            "evidence": ["DEVICES"],
        })

    if shared_towers:

        findings.append({
            "type": "DERIVED",
            "title": "Shared tower observations",
            "description": (
                f"{len(shared_towers)} tower(s) have "
                "observations involving multiple phone numbers."
            ),
            "evidence": ["CDR"],
        })

    # --------------------------------------------------------
    # ANALYTICAL INFERENCE
    # --------------------------------------------------------

    if transactions["unique_receivers"] > 1:

        findings.append({
            "type": "ANALYTICAL INFERENCE",
            "title": "Fund-distribution pattern warrants review",
            "description": (
                "The presence of multiple transaction recipients "
                "may warrant further investigation of the money "
                "flow and recipient relationships. This is an "
                "analytical lead and is not a determination of "
                "wrongdoing."
            ),
            "evidence": ["UPI"],
        })

    if shared_devices:

        findings.append({
            "type": "ANALYTICAL INFERENCE",
            "title": "Device correlation warrants review",
            "description": (
                "A device associated with multiple phone numbers "
                "may provide a useful investigative pivot. "
                "Additional evidence should be reviewed before "
                "drawing conclusions."
            ),
            "evidence": ["DEVICES"],
        })

    return findings


# ============================================================
# COMMAND CENTER
# ============================================================

def build_command_center():

    active_case = get_active_case()

    if not active_case["active"]:

        result = {
            "status": "NO_ACTIVE_CASE",
            "generated_at": datetime.now().isoformat(),
            "message": (
                "No active Phase 8 investigation case was found."
            ),
        }

        save_json(result, COMMAND_CENTER_OUTPUT)

        return result

    case_id = active_case["case_id"]
    case_dir = active_case["case_dir"]

    manifest = load_case_manifest(case_dir)

    evidence = load_evidence(case_dir)

    evidence_metrics = calculate_evidence_metrics(
        evidence
    )

    entities = extract_entities(
        evidence
    )

    connections = calculate_connections(
        evidence
    )

    transaction_analysis = calculate_transaction_analysis(
        evidence
    )

    money_flow = calculate_money_flow(
        evidence
    )

    shared_devices = calculate_shared_devices(
        evidence
    )

    shared_towers = calculate_shared_towers(
        evidence
    )

    findings = generate_findings(
        evidence_metrics=evidence_metrics,
        entities=entities,
        transactions=transaction_analysis,
        money_flow=money_flow,
        shared_devices=shared_devices,
        shared_towers=shared_towers,
    )

    result = {
        "status": "ACTIVE",
        "generated_at": datetime.now().isoformat(),

        "case": {
            "case_id": case_id,
            "case_directory": str(case_dir),
            "title": (
                manifest.get("case_title")
                or manifest.get("title")
                or "Cyber-Fraud Investigation"
            ),
            "description": (
                manifest.get("case_description")
                or manifest.get("description")
                or ""
            ),
        },

        "evidence": evidence_metrics,

        "entities": {
            "phones": len(entities["phones"]),
            "accounts": len(entities["accounts"]),
            "imeis": len(entities["imeis"]),
            "towers": len(entities["towers"]),
            "persons": len(entities["persons"]),
            "transactions": len(entities["transactions"]),
        },

        "connections": {
            "total": len(connections),
            "by_relationship": dict(
                Counter(
                    connection["relationship"]
                    for connection in connections
                )
            ),
        },

        "transactions": transaction_analysis,

        "money_flow": money_flow,

        "shared_devices": shared_devices,

        "shared_towers": shared_towers,

        "findings": findings,

        "investigation_actions": [
            {
                "id": "GRAPH",
                "label": "Open Investigation Graph",
                "target": "Investigation Graph",
            },
            {
                "id": "CONNECTION",
                "label": "Explain Connection",
                "target": "Explain Connection",
            },
            {
                "id": "IMEI",
                "label": "Analyze IMEI",
                "target": "IMEI Investigation",
            },
            {
                "id": "TOWER",
                "label": "Analyze Towers",
                "target": "Location/Tower Investigation",
            },
            {
                "id": "EDGE",
                "label": "Analyze Edge Cases",
                "target": "Edge Case Analysis",
            },
            {
                "id": "COPILOT",
                "label": "Open Investigation Copilot",
                "target": "Investigation Copilot",
            },
            {
                "id": "REPORT",
                "label": "Generate Case Brief",
                "target": "Case Brief",
            },
        ],
    }

    save_json(
        result,
        COMMAND_CENTER_OUTPUT
    )

    return result


# ============================================================
# TERMINAL DISPLAY
# ============================================================

def print_command_center(result):

    print()
    print("=" * 70)
    print("CHANAKYA-GRAPH — PHASE 9")
    print("INVESTIGATION COMMAND CENTER")
    print("=" * 70)

    print()

    print("STATUS")
    print("-" * 70)

    print(
        "Status     :",
        result.get("status")
    )

    if result.get("status") != "ACTIVE":
        print(
            result.get("message")
        )
        return

    case = result["case"]

    print(
        "Case ID    :",
        case["case_id"]
    )

    print(
        "Case Title :",
        case["title"]
    )

    print()

    print("EVIDENCE")
    print("-" * 70)

    evidence = result["evidence"]

    print(
        "CDR        :",
        evidence["cdr"]["records"]
    )

    print(
        "UPI        :",
        evidence["upi"]["records"]
    )

    print(
        "Complaints :",
        evidence["complaints"]["records"]
    )

    print(
        "Devices    :",
        evidence["devices"]["records"]
    )

    print(
        "Total      :",
        evidence["total_records"]
    )

    print()

    print("ENTITIES")
    print("-" * 70)

    entities = result["entities"]

    for key, value in entities.items():

        print(
            f"{key.replace('_', ' ').title():20}: {value}"
        )

    print()

    print("CONNECTIONS")
    print("-" * 70)

    print(
        "Total:",
        result["connections"]["total"]
    )

    for relationship, count in result[
        "connections"
    ]["by_relationship"].items():

        print(
            f"{relationship:25}: {count}"
        )

    print()

    print("FINANCIAL ANALYSIS")
    print("-" * 70)

    transactions = result["transactions"]

    print(
        "Transactions       :",
        transactions["transaction_count"]
    )

    print(
        "Total Amount       : INR {:,.2f}".format(
            transactions["total_amount_inr"]
        )
    )

    print(
        "Average Amount     : INR {:,.2f}".format(
            transactions["average_amount_inr"]
        )
    )

    print(
        "Unique Senders     :",
        transactions["unique_senders"]
    )

    print(
        "Unique Receivers   :",
        transactions["unique_receivers"]
    )

    if transactions["maximum_transaction"]:

        maximum = transactions[
            "maximum_transaction"
        ]

        print(
            "Largest Transaction: INR {:,.2f}".format(
                maximum["amount_inr"]
            )
        )

        print(
            "Transaction ID     :",
            maximum["transaction_id"]
        )

    print()

    print("INVESTIGATION FINDINGS")
    print("-" * 70)

    for finding in result["findings"]:

        print(
            f"[{finding['type']}] "
            f"{finding['title']}"
        )

        print(
            f"  {finding['description']}"
        )

    print()

    print("OUTPUT")
    print("-" * 70)

    print(
        "Saved:",
        COMMAND_CENTER_OUTPUT
    )

    print()

    print("PHASE 9 COMPLETE")
    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    result = build_command_center()

    print_command_center(result)