import json
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


FILES = {
    "cdr": DATA_DIR / "cdr_records.csv",
    "upi": DATA_DIR / "upi_transactions.csv",
    "complaints": DATA_DIR / "complaints.csv",
    "devices": DATA_DIR / "device_records.csv",
    "metadata": DATA_DIR / "case_metadata.json",
}


REQUIRED_COLUMNS = {
    "cdr": [
        "record_id",
        "case_id",
        "timestamp",
        "caller",
        "called",
        "duration_seconds",
        "imei",
        "tower_id",
        "call_type",
        "data_source",
    ],
    "upi": [
        "transaction_id",
        "case_id",
        "timestamp",
        "sender_account",
        "receiver_account",
        "sender_type",
        "receiver_type",
        "amount_inr",
        "transaction_status",
        "reference_id",
        "data_source",
    ],
    "complaints": [
        "complaint_id",
        "case_id",
        "complaint_timestamp",
        "victim_name",
        "victim_phone",
        "victim_account",
        "fraud_category",
        "complaint_description",
        "reported_amount_inr",
        "reported_caller",
        "data_source",
    ],
    "devices": [
        "device_record_id",
        "case_id",
        "phone_number",
        "imei",
        "device_type",
        "first_seen",
        "last_seen",
        "tower_id",
        "data_source",
    ],
}


def load_csv(path):
    """Load a CSV evidence file."""

    if not path.exists():
        raise FileNotFoundError(f"Missing evidence file: {path}")

    return pd.read_csv(path)


def load_metadata(path):
    """Load case metadata JSON."""

    if not path.exists():
        raise FileNotFoundError(f"Missing metadata file: {path}")

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def validate_columns(name, dataframe):
    """Check whether all required columns exist."""

    required = REQUIRED_COLUMNS[name]

    missing = [
        column
        for column in required
        if column not in dataframe.columns
    ]

    if missing:
        raise ValueError(
            f"{name}: missing required columns: {missing}"
        )


def validate_case_id(name, dataframe, expected_case_id):
    """Make sure records belong to the current investigation."""

    if "case_id" not in dataframe.columns:
        return

    invalid = dataframe[
        dataframe["case_id"] != expected_case_id
    ]

    if not invalid.empty:
        raise ValueError(
            f"{name}: records from unexpected case IDs found."
        )


def validate_synthetic_source(name, dataframe):
    """Make sure the demo dataset is explicitly synthetic."""

    if "data_source" not in dataframe.columns:
        raise ValueError(
            f"{name}: data_source column is missing."
        )

    invalid = dataframe[
        dataframe["data_source"] != "SYNTHETIC_DEMO"
    ]

    if not invalid.empty:
        raise ValueError(
            f"{name}: non-synthetic records detected."
        )


def validate_numeric_fields(data):
    """Validate numeric investigation fields."""

    checks = {
        "cdr": ["duration_seconds"],
        "upi": ["amount_inr"],
        "complaints": ["reported_amount_inr"],
    }

    for name, dataframe in data.items():

        if name not in checks:
            continue

        for column in checks[name]:

            dataframe[column] = pd.to_numeric(
                dataframe[column],
                errors="coerce"
            )

            if dataframe[column].isna().any():
                raise ValueError(
                    f"{name}: invalid numeric values in {column}"
                )


def normalize_phone(phone):
    """Normalize Indian demo phone numbers."""

    phone = str(phone).strip()

    if phone.startswith("+91"):
        return phone

    if phone.startswith("91") and len(phone) == 12:
        return "+" + phone

    if len(phone) == 10:
        return "+91" + phone

    return phone


def normalize_phone_columns(data):
    """Normalize phone identifiers across evidence sources."""

    phone_columns = {
        "cdr": ["caller", "called"],
        "complaints": ["victim_phone", "reported_caller"],
        "devices": ["phone_number"],
    }

    for name, columns in phone_columns.items():

        dataframe = data[name]

        for column in columns:
            dataframe[column] = dataframe[column].apply(
                normalize_phone
            )


def standardize_timestamps(data):

    timestamp_columns = {
        "cdr": ["timestamp"],
        "upi": ["timestamp"],
        "complaints": ["complaint_timestamp"],
        "devices": ["first_seen", "last_seen"],
    }

    for name, columns in timestamp_columns.items():

        dataframe = data[name]

        for column in columns:
            dataframe[column] = pd.to_datetime(
                dataframe[column],
                errors="coerce"
            )

            if dataframe[column].isna().any():
                raise ValueError(
                    f"{name}: invalid timestamp in {column}"
                )


def create_evidence_ledger(data, metadata):
    """
    Convert different source records into a common
    evidence representation.

    This is the bridge between Phase 1 and Phase 2.
    """

    ledger = []

    case_id = metadata["case_id"]

    # -----------------------------
    # CDR evidence
    # -----------------------------

    for _, row in data["cdr"].iterrows():

        ledger.append({
            "evidence_id": f"EVD-CDR-{row['record_id']}",
            "case_id": case_id,
            "source_type": "CDR",
            "source_record_id": row["record_id"],
            "timestamp": str(row["timestamp"]),
            "subject": row["caller"],
            "object": row["called"],
            "relationship": "CALLED",
            "attributes": {
                "duration_seconds": row["duration_seconds"],
                "imei": row["imei"],
                "tower_id": row["tower_id"],
                "call_type": row["call_type"],
            },
            "evidence_status": "OBSERVED",
            "data_source": row["data_source"],
        })

    # -----------------------------
    # UPI evidence
    # -----------------------------

    for _, row in data["upi"].iterrows():

        ledger.append({
            "evidence_id": f"EVD-UPI-{row['transaction_id']}",
            "case_id": case_id,
            "source_type": "UPI",
            "source_record_id": row["transaction_id"],
            "timestamp": str(row["timestamp"]),
            "subject": row["sender_account"],
            "object": row["receiver_account"],
            "relationship": "TRANSFERRED_FUNDS",
            "attributes": {
                "amount_inr": row["amount_inr"],
                "sender_type": row["sender_type"],
                "receiver_type": row["receiver_type"],
                "status": row["transaction_status"],
                "reference_id": row["reference_id"],
            },
            "evidence_status": "OBSERVED",
            "data_source": row["data_source"],
        })

    # -----------------------------
    # Complaint evidence
    # -----------------------------

    for _, row in data["complaints"].iterrows():

        ledger.append({
            "evidence_id": f"EVD-COMP-{row['complaint_id']}",
            "case_id": case_id,
            "source_type": "COMPLAINT",
            "source_record_id": row["complaint_id"],
            "timestamp": str(row["complaint_timestamp"]),
            "subject": row["victim_phone"],
            "object": row["reported_caller"],
            "relationship": "REPORTED_FRAUD_CALL",
            "attributes": {
                "victim_name": row["victim_name"],
                "victim_account": row["victim_account"],
                "fraud_category": row["fraud_category"],
                "description": row["complaint_description"],
                "reported_amount_inr": row["reported_amount_inr"],
            },
            "evidence_status": "OBSERVED",
            "data_source": row["data_source"],
        })

    # -----------------------------
    # Device evidence
    # -----------------------------

    for _, row in data["devices"].iterrows():

        ledger.append({
            "evidence_id": f"EVD-DEV-{row['device_record_id']}",
            "case_id": case_id,
            "source_type": "DEVICE",
            "source_record_id": row["device_record_id"],
            "timestamp": str(row["first_seen"]),
            "subject": row["phone_number"],
            "object": row["imei"],
            "relationship": "USED_HARDWARE",
            "attributes": {
                "device_type": row["device_type"],
                "first_seen": str(row["first_seen"]),
                "last_seen": str(row["last_seen"]),
                "tower_id": row["tower_id"],
            },
            "evidence_status": "OBSERVED",
            "data_source": row["data_source"],
        })

    return ledger


def print_summary(data, metadata, ledger):

    print("\n" + "=" * 70)
    print("CHANAKYA-GRAPH — PHASE 1 EVIDENCE INGESTION")
    print("=" * 70)

    print(f"\nCase ID        : {metadata['case_id']}")
    print(f"Case Title     : {metadata['case_title']}")
    print(f"Data Class     : {metadata['data_classification']}")

    print("\nInput Records")
    print("-" * 40)

    print(f"CDR records    : {len(data['cdr'])}")
    print(f"UPI records    : {len(data['upi'])}")
    print(f"Complaints     : {len(data['complaints'])}")
    print(f"Device records : {len(data['devices'])}")

    print("\nEvidence Ledger")
    print("-" * 40)

    print(f"Total evidence : {len(ledger)}")

    print("\nEvidence Types")

    evidence_types = {}

    for item in ledger:
        evidence_type = item["source_type"]
        evidence_types[evidence_type] = (
            evidence_types.get(evidence_type, 0) + 1
        )

    for evidence_type, count in evidence_types.items():
        print(f"{evidence_type:<15}: {count}")

    print("\n" + "=" * 70)
    print("PHASE 1 INGESTION SUCCESSFUL")
    print("=" * 70)


def main():

    # -----------------------------
    # Load files
    # -----------------------------

    data = {
        "cdr": load_csv(FILES["cdr"]),
        "upi": load_csv(FILES["upi"]),
        "complaints": load_csv(FILES["complaints"]),
        "devices": load_csv(FILES["devices"]),
    }

    metadata = load_metadata(FILES["metadata"])

    expected_case_id = metadata["case_id"]

    # -----------------------------
    # Validate structure
    # -----------------------------

    for name, dataframe in data.items():

        validate_columns(name, dataframe)

        validate_case_id(
            name,
            dataframe,
            expected_case_id
        )

        validate_synthetic_source(
            name,
            dataframe
        )

    # -----------------------------
    # Validate metadata
    # -----------------------------

    if metadata["data_classification"] != "SYNTHETIC_DEMO":
        raise ValueError(
            "Dataset is not marked as SYNTHETIC_DEMO."
        )

    # -----------------------------
    # Normalize
    # -----------------------------

    normalize_phone_columns(data)

    standardize_timestamps(data)

    validate_numeric_fields(data)

    # -----------------------------
    # Evidence ledger
    # -----------------------------

    ledger = create_evidence_ledger(
        data,
        metadata
    )

    # -----------------------------
    # Display result
    # -----------------------------

    print_summary(
        data,
        metadata,
        ledger
    )

    return data, metadata, ledger


if __name__ == "__main__":
    main()