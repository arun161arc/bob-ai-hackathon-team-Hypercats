from pathlib import Path
import json
import pandas as pd


SRC_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = SRC_DIR / "data"
CASES_DIR = DATA_DIR / "cases"

OUTPUT_DIR = SRC_DIR / "output" / "investigation"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_active_case():
    active_file = CASES_DIR / "active_case.json"

    if not active_file.exists():
        return None

    with open(active_file, "r", encoding="utf-8") as f:
        return json.load(f)


def get_case_directory():
    active_case = load_active_case()

    if not active_case:
        return None

    case_id = active_case.get("case_id")

    if not case_id:
        return None

    case_dir = CASES_DIR / case_id

    if not case_dir.exists():
        return None

    return case_dir


def load_evidence_files():
    """
    Load evidence from the CURRENT normalized case directory.
    """

    case_dir = get_case_directory()

    if not case_dir:
        return {}

    normalized_dir = case_dir / "normalized"

    files = {
        "CDR": normalized_dir / "cdr_records.csv",
        "UPI": normalized_dir / "upi_transactions.csv",
        "COMPLAINT": normalized_dir / "complaints.csv",
        "DEVICE": normalized_dir / "device_records.csv",
    }

    evidence = {}

    for evidence_type, path in files.items():

        if not path.exists():
            print(f"Evidence file not found: {path}")
            continue

        try:
            df = pd.read_csv(path, dtype=str).fillna("")
            evidence[evidence_type] = df

        except Exception as exc:
            print(f"Could not load {evidence_type}: {exc}")

    return evidence


def get_evidence_id(row, evidence_type):

    if evidence_type == "CDR":
        return row.get("record_id", "")

    if evidence_type == "UPI":
        return row.get("transaction_id", "")

    if evidence_type == "COMPLAINT":
        return row.get("complaint_id", "")

    if evidence_type == "DEVICE":
        return row.get("device_record_id", "")

    return ""


def get_timestamp(row, evidence_type):

    timestamp_fields = {
        "CDR": ["timestamp"],
        "UPI": ["timestamp"],
        "COMPLAINT": ["complaint_timestamp"],
        "DEVICE": ["first_seen", "last_seen"],
    }

    for field in timestamp_fields.get(evidence_type, []):

        value = row.get(field, "")

        if value:
            return value

    return ""


def normalize_record(row, evidence_type):

    row = {
        str(k): str(v)
        for k, v in row.items()
    }

    evidence_id = get_evidence_id(
        row,
        evidence_type
    )

    timestamp = get_timestamp(
        row,
        evidence_type
    )

    amount = ""

    if evidence_type == "UPI":
        amount = row.get("amount_inr", "")

    elif evidence_type == "COMPLAINT":
        amount = row.get("reported_amount_inr", "")

    return {
        "evidence_id": evidence_id,
        "evidence_type": evidence_type,
        "timestamp": timestamp,
        "evidence_status": "OBSERVED",
        "amount_inr": amount,
        "data_source": row.get(
            "data_source",
            "UNKNOWN"
        ),
        "record": row,
    }


def build_evidence_ledger():

    evidence_files = load_evidence_files()

    ledger = []

    for evidence_type, df in evidence_files.items():

        for _, row in df.iterrows():

            record = normalize_record(
                row.to_dict(),
                evidence_type
            )

            ledger.append(record)

    return ledger


def search_evidence(ledger, query=""):

    query = str(query).strip().lower()

    if not query:
        return ledger

    results = []

    for evidence in ledger:

        searchable = [
            str(evidence.get("evidence_id", "")),
            str(evidence.get("evidence_type", "")),
            str(evidence.get("timestamp", "")),
        ]

        record = evidence.get("record", {})

        searchable.extend(
            str(value)
            for value in record.values()
        )

        text = " ".join(searchable).lower()

        if query in text:
            results.append(evidence)

    return results


def filter_evidence(
    ledger,
    evidence_type=None,
    status=None
):

    results = ledger

    if evidence_type:
        results = [
            item
            for item in results
            if item.get("evidence_type") == evidence_type
        ]

    if status:
        results = [
            item
            for item in results
            if item.get("evidence_status") == status
        ]

    return results


def get_evidence_by_id(
    ledger,
    evidence_id
):

    evidence_id = str(
        evidence_id
    ).strip().lower()

    for evidence in ledger:

        current_id = str(
            evidence.get(
                "evidence_id",
                ""
            )
        ).lower()

        if current_id == evidence_id:
            return evidence

    return None


def evidence_summary(ledger):

    summary = {
        "total": len(ledger),
        "CDR": 0,
        "UPI": 0,
        "COMPLAINT": 0,
        "DEVICE": 0,
        "OBSERVED": 0,
    }

    for evidence in ledger:

        evidence_type = evidence.get(
            "evidence_type"
        )

        status = evidence.get(
            "evidence_status"
        )

        if evidence_type in summary:
            summary[evidence_type] += 1

        if status == "OBSERVED":
            summary["OBSERVED"] += 1

    return summary


def save_evidence_ledger(ledger):

    output_file = (
        OUTPUT_DIR /
        "evidence_ledger.json"
    )

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            ledger,
            f,
            indent=2,
            ensure_ascii=False
        )

    return output_file


def run_evidence_explorer():

    ledger = build_evidence_ledger()

    output_file = save_evidence_ledger(
        ledger
    )

    summary = evidence_summary(
        ledger
    )

    print("=" * 65)
    print("CHANAKYA-GRAPH — PHASE 13")
    print("EVIDENCE EXPLORER / EVIDENCE LEDGER")
    print("=" * 65)

    print(f"Total Evidence : {summary['total']}")
    print(f"CDR            : {summary['CDR']}")
    print(f"UPI            : {summary['UPI']}")
    print(f"Complaints     : {summary['COMPLAINT']}")
    print(f"Devices        : {summary['DEVICE']}")
    print(f"Observed       : {summary['OBSERVED']}")
    print(f"Output         : {output_file}")

    print("=" * 65)
    print("PHASE 13 COMPLETE")

    return ledger


if __name__ == "__main__":
    run_evidence_explorer()