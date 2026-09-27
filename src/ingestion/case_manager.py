import os
import json
import hashlib
import random
import string
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd

from .demo_scenarios import ensure_multiday_demo_scenario


# ============================================================
# PATHS
# ============================================================

SRC_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = SRC_DIR / "data"

DEMO_DIR = DATA_DIR / "demo"

CASES_DIR = DATA_DIR / "cases"

ACTIVE_CASE_FILE = CASES_DIR / "active_case.json"


# ============================================================
# STANDARD WORKING FILES
# ============================================================

WORKING_FILES = {
    "cdr": "cdr_records.csv",
    "upi": "upi_transactions.csv",
    "complaints": "complaints.csv",
    "devices": "device_records.csv",
}


# ============================================================
# REQUIRED SCHEMAS
# ============================================================

REQUIRED_COLUMNS = {

    "cdr": [
        "record_id",
        "timestamp",
        "caller",
        "called",
        "duration_seconds",
        "imei",
        "tower_id",
        "call_type",
    ],

    "upi": [
        "transaction_id",
        "timestamp",
        "sender_account",
        "receiver_account",
        "sender_type",
        "receiver_type",
        "amount_inr",
        "transaction_status",
        "reference_id",
    ],

    "complaints": [
        "complaint_id",
        "complaint_timestamp",
        "victim_name",
        "victim_phone",
        "victim_account",
        "fraud_category",
        "complaint_description",
        "reported_amount_inr",
        "reported_caller",
    ],

    "devices": [
        "device_record_id",
        "phone_number",
        "imei",
        "device_type",
        "first_seen",
        "last_seen",
        "tower_id",
    ],
}


# ============================================================
# COLUMN ALIASES
# ============================================================

COLUMN_ALIASES = {

    "recordid": "record_id",
    "record_id": "record_id",

    "transactionid": "transaction_id",
    "transaction_id": "transaction_id",

    "complaintid": "complaint_id",
    "complaint_id": "complaint_id",

    "devicerecordid": "device_record_id",
    "device_record_id": "device_record_id",

    "datetime": "timestamp",
    "date_time": "timestamp",
    "time": "timestamp",

    "caller_number": "caller",
    "caller_phone": "caller",
    "source": "caller",

    "called_number": "called",
    "receiver_phone": "called",
    "destination": "called",

    "phone": "phone_number",
    "mobile": "phone_number",
    "mobile_number": "phone_number",

    "sender": "sender_account",
    "from_account": "sender_account",

    "receiver": "receiver_account",
    "to_account": "receiver_account",

    "amount": "amount_inr",
    "amount_rs": "amount_inr",
    "amount_rupees": "amount_inr",

    "status": "transaction_status",

    "reference": "reference_id",
    "referenceid": "reference_id",

    "name": "victim_name",

    "reported_amount": "reported_amount_inr",

    "reported_phone": "reported_caller",

    "device": "device_type",

    "device_id": "imei",

    "tower": "tower_id",
}


# ============================================================
# DIRECTORY SETUP
# ============================================================

def ensure_directories():

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    DEMO_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    CASES_DIR.mkdir(
        parents=True,
        exist_ok=True
    )


# ============================================================
# COLUMN NORMALIZATION
# ============================================================

def normalize_column_name(column):

    column = str(column).strip().lower()

    column = (
        column
        .replace(" ", "_")
        .replace("-", "_")
        .replace("/", "_")
    )

    compact = column.replace("_", "")

    if column in COLUMN_ALIASES:
        return COLUMN_ALIASES[column]

    if compact in COLUMN_ALIASES:
        return COLUMN_ALIASES[compact]

    return column


def normalize_dataframe_columns(df):

    df = df.copy()

    df.columns = [
        normalize_column_name(column)
        for column in df.columns
    ]

    return df


# ============================================================
# SHA256
# ============================================================

def sha256_bytes(data):

    return hashlib.sha256(data).hexdigest()


def sha256_file(path):

    sha256 = hashlib.sha256()

    with open(path, "rb") as file:

        while True:

            chunk = file.read(1024 * 1024)

            if not chunk:
                break

            sha256.update(chunk)

    return sha256.hexdigest()


# ============================================================
# CASE ID
# ============================================================

def generate_case_id():

    timestamp = datetime.now().strftime(
        "%Y%m%d-%H%M%S"
    )

    random_part = "".join(
        random.choices(
            string.ascii_uppercase + string.digits,
            k=6
        )
    )

    return f"CASE-{timestamp}-{random_part}"


# ============================================================
# VALIDATE DATAFRAME
# ============================================================

def validate_dataframe(
    df,
    evidence_type
):

    if evidence_type not in REQUIRED_COLUMNS:

        return False, [
            f"Unknown evidence type: {evidence_type}"
        ]

    required = REQUIRED_COLUMNS[evidence_type]

    missing = [
        column
        for column in required
        if column not in df.columns
    ]

    if missing:

        return False, missing

    if len(df) == 0:

        return False, [
            "Dataset contains no records."
        ]

    return True, []


# ============================================================
# PREPARE DATAFRAME
# ============================================================

def prepare_dataframe(
    df,
    evidence_type,
    case_id
):

    df = normalize_dataframe_columns(df)

    valid, errors = validate_dataframe(
        df,
        evidence_type
    )

    if not valid:

        raise ValueError(
            f"{evidence_type.upper()} validation failed. "
            f"Missing columns: {errors}"
        )

    # --------------------------------------------------------
    # CASE ID
    # --------------------------------------------------------

    if "case_id" not in df.columns:

        df["case_id"] = case_id

    else:

        df["case_id"] = case_id

    # --------------------------------------------------------
    # DATA SOURCE
    # --------------------------------------------------------

    df["data_source"] = "USER_UPLOAD"

    # --------------------------------------------------------
    # NUMERIC FIELDS
    # --------------------------------------------------------

    if "amount_inr" in df.columns:

        df["amount_inr"] = pd.to_numeric(
            df["amount_inr"],
            errors="coerce"
        ).fillna(0)

    if "reported_amount_inr" in df.columns:

        df["reported_amount_inr"] = pd.to_numeric(
            df["reported_amount_inr"],
            errors="coerce"
        ).fillna(0)

    if "duration_seconds" in df.columns:

        df["duration_seconds"] = pd.to_numeric(
            df["duration_seconds"],
            errors="coerce"
        ).fillna(0)

    # --------------------------------------------------------
    # TIMESTAMPS
    # --------------------------------------------------------

    timestamp_columns = [
        "timestamp",
        "complaint_timestamp",
        "first_seen",
        "last_seen",
    ]

    for column in timestamp_columns:

        if column in df.columns:

            parsed = pd.to_datetime(
                df[column],
                errors="coerce"
            )

            df[column] = parsed.astype(str)

    # --------------------------------------------------------
    # REMOVE COMPLETELY EMPTY ROWS
    # --------------------------------------------------------

    df = df.dropna(
        how="all"
    )

    # --------------------------------------------------------
    # RESET INDEX
    # --------------------------------------------------------

    df = df.reset_index(
        drop=True
    )

    return df


# ============================================================
# READ UPLOADED FILE
# ============================================================

def read_uploaded_file(uploaded_file):

    if uploaded_file is None:
        return None

    try:
        # Always read the complete file from the beginning
        uploaded_file.seek(0)

        file_bytes = uploaded_file.read()

        if not file_bytes:
            raise ValueError(
                f"Uploaded file '{uploaded_file.name}' is empty."
            )

        # Read CSV from the captured bytes
        from io import BytesIO

        df = pd.read_csv(
            BytesIO(file_bytes)
        )

        if df.empty:
            raise ValueError(
                f"Uploaded file '{uploaded_file.name}' "
                "contains no data rows."
            )

        if len(df.columns) == 0:
            raise ValueError(
                f"Uploaded file '{uploaded_file.name}' "
                "contains no columns."
            )

        return df, file_bytes

    except Exception as error:

        if isinstance(error, ValueError):
            raise

        raise ValueError(
            f"Could not read '{uploaded_file.name}' "
            f"as CSV: {error}"
        )


# ============================================================
# CREATE NEW CASE
# ============================================================

def create_case(
    case_name,
    description,
    uploaded_files
):

    ensure_directories()

    # --------------------------------------------hlm,------------
    # CHECK INPUT
    # --------------------------------------------------------

    if not case_name or not case_name.strip():

        raise ValueError(
            "Case name is required."
        )

    required_types = [
        "cdr",
        "upi",
        "complaints",
        "devices",
    ]

    missing_files = []

    for evidence_type in required_types:

        if uploaded_files.get(evidence_type) is None:

            missing_files.append(
                evidence_type
            )

    if missing_files:

        raise ValueError(
            "Missing evidence files: "
            + ", ".join(missing_files)
        )

    # --------------------------------------------------------
    # CREATE CASE
    # --------------------------------------------------------

    case_id = generate_case_id()

    case_dir = CASES_DIR / case_id

    raw_dir = case_dir / "raw"

    normalized_dir = case_dir / "normalized"

    raw_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    normalized_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    evidence_records = []

    # --------------------------------------------------------
    # PROCESS EACH FILE
    # --------------------------------------------------------

    for evidence_type in required_types:

        uploaded_file = uploaded_files[
            evidence_type
        ]

        filename = uploaded_file.name

        df, file_bytes = read_uploaded_file(
            uploaded_file
        )

        # Normalize data
        prepared_df = prepare_dataframe(
            df,
            evidence_type,
            case_id
        )

        # ----------------------------------------------------
        # RAW FILE
        # ----------------------------------------------------

        raw_path = raw_dir / filename

        with open(
            raw_path,
            "wb"
        ) as file:

            file.write(
                file_bytes
            )

        # ----------------------------------------------------
        # NORMALIZED FILE
        # ----------------------------------------------------

        normalized_filename = WORKING_FILES[
            evidence_type
        ]

        normalized_path = (
            normalized_dir
            / normalized_filename
        )

        prepared_df.to_csv(
            normalized_path,
            index=False
        )

        # ----------------------------------------------------
        # HASH
        # ----------------------------------------------------

        file_hash = sha256_bytes(
            file_bytes
        )

        # ----------------------------------------------------
        # EVIDENCE RECORD
        # ----------------------------------------------------

        evidence_record = {

            "evidence_type": evidence_type,

            "original_filename": filename,

            "raw_file": str(
                raw_path.relative_to(
                    case_dir
                )
            ),

            "normalized_file": str(
                normalized_path.relative_to(
                    case_dir
                )
            ),

            "record_count": int(
                len(prepared_df)
            ),

            "sha256": file_hash,

            "data_source": "USER_UPLOAD",

            "evidence_status": "OBSERVED",
        }

        evidence_records.append(
            evidence_record
        )

        # ----------------------------------------------------
        # COPY NORMALIZED DATA TO ACTIVE WORKING DIRECTORY
        # ----------------------------------------------------

        working_path = (
            DATA_DIR
            / normalized_filename
        )

        shutil.copy2(
            normalized_path,
            working_path
        )

    # ========================================================
    # CASE MANIFEST
    # ========================================================

    manifest = {

        "case_id": case_id,

        "case_name": case_name.strip(),

        "description": (
            description.strip()
            if description
            else ""
        ),

        "case_type": "USER_INVESTIGATION",

        "created_at": datetime.now().isoformat(),

        "data_classification": "USER_PROVIDED",

        "evidence_count": len(
            evidence_records
        ),

        "evidence": evidence_records,

        "analysis_status": {

            "phase_1_ingestion": "READY",

            "phase_2_entities": "PENDING",

            "phase_3_graph": "PENDING",

            "phase_4_algorithms": "PENDING",

            "phase_5_ui": "READY",

            "phase_6_explain_connection": "PENDING",

            "phase_7_copilot": "PENDING",

            "phase_8_case_report": "PENDING",

            "phase_9_edge_cases": "PENDING",

        },
    }

    # --------------------------------------------------------
    # SAVE MANIFEST
    # --------------------------------------------------------

    manifest_path = (
        case_dir
        / "case_manifest.json"
    )

    with open(
        manifest_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            manifest,
            file,
            indent=4
        )

    # --------------------------------------------------------
    # SET ACTIVE CASE
    # --------------------------------------------------------

    active_case = {

        "case_id": case_id,

        "case_name": case_name.strip(),

        "case_type": "USER_INVESTIGATION",

        "case_path": str(
            case_dir
        ),

        "manifest_path": str(
            manifest_path
        ),

        "activated_at": datetime.now().isoformat(),
    }

    with open(
        ACTIVE_CASE_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            active_case,
            file,
            indent=4
        )

    return manifest


# ============================================================
# DEMO DATASET
# ============================================================

def ensure_demo_dataset():

    ensure_directories()

    source_files = {
        "cdr_records.csv":
            DATA_DIR / "cdr_records.csv",

        "upi_transactions.csv":
            DATA_DIR / "upi_transactions.csv",

        "complaints.csv":
            DATA_DIR / "complaints.csv",

        "device_records.csv":
            DATA_DIR / "device_records.csv",
    }

    for filename, source_path in source_files.items():

        destination = (
            DEMO_DIR / filename
        )

        if (
            source_path.exists()
            and not destination.exists()
        ):

            shutil.copy2(
                source_path,
                destination
            )

    # IMPORTANT:
    # Add OR repair the multi-day scenario
    ensure_multiday_demo_scenario(
        DEMO_DIR
    )

    return DEMO_DIR

    # --------------------------------------------------------
    # Create demo snapshot only if it does not exist
    # --------------------------------------------------------

    for filename, source_path in source_files.items():

        destination = (
            DEMO_DIR
            / filename
        )

        if (
            source_path.exists()
            and not destination.exists()
        ):

            shutil.copy2(
                source_path,
                destination
            )

    # --------------------------------------------------------
    # ADD MULTI-DAY FRAUD SCENARIO
    # --------------------------------------------------------

    ensure_multiday_demo_scenario(
        DEMO_DIR
    )

    return DEMO_DIR


# ============================================================
# ACTIVATE DEMO DATASET
# ============================================================

def activate_demo_dataset():

    ensure_directories()

    # Make sure demo dataset exists
    ensure_demo_dataset()

    # --------------------------------------------------------
    # Copy demo files into active working directory
    # --------------------------------------------------------

    for filename in WORKING_FILES.values():

        source_path = (
            DEMO_DIR
            / filename
        )

        destination = (
            DATA_DIR
            / filename
        )

        if source_path.exists():

            shutil.copy2(
                source_path,
                destination
            )

    # --------------------------------------------------------
    # Multi-day scenario information
    # --------------------------------------------------------

    multi_day_info = {

        "enabled": True,

        "scenario": (
            "MULTI_DAY_REPEATED_DEDUCTION"
        ),

        "transaction_count": 5,

        "total_amount_inr": 29800,

        "first_transaction":
            "2026-09-10 10:15:00",

        "last_transaction":
            "2026-09-19 11:06:00",

        "complaint_timestamp":
            "2026-09-20 09:30:00",

        "unique_recipients": 3,

        "detection_delay_days": 1,
    }

    # --------------------------------------------------------
    # Demo manifest
    # --------------------------------------------------------

    manifest = {

        "case_id":
            "DEMO-CYB-2026-0001",

        "case_name":
            "Synthetic Cyber-Fraud Investigation Dataset",

        "description":
            (
                "Synthetic demonstration dataset "
                "for Chanakya-Graph."
            ),

        "case_type":
            "SYNTHETIC_DEMO",

        "data_classification":
            "SYNTHETIC_DEMO",

        "source":
            "CHANAKYA_GRAPH_DEMO",

        "activated_at":
            datetime.now().isoformat(),

        "multi_day_scenario":
            multi_day_info,

        "evidence": [

            {
                "evidence_type": "cdr",
                "file": "cdr_records.csv",
                "data_source": "SYNTHETIC_DEMO",
            },

            {
                "evidence_type": "upi",
                "file": "upi_transactions.csv",
                "data_source": "SYNTHETIC_DEMO",
            },

            {
                "evidence_type": "complaints",
                "file": "complaints.csv",
                "data_source": "SYNTHETIC_DEMO",
            },

            {
                "evidence_type": "devices",
                "file": "device_records.csv",
                "data_source": "SYNTHETIC_DEMO",
            },
        ],
    }

    # --------------------------------------------------------
    # Save demo manifest
    # --------------------------------------------------------

    manifest_path = (
        DEMO_DIR
        / "case_manifest.json"
    )

    with open(
        manifest_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            manifest,
            file,
            indent=4
        )

    # --------------------------------------------------------
    # Set active case
    # --------------------------------------------------------

    active_case = {

        "case_id":
            "DEMO-CYB-2026-0001",

        "case_name":
            "Synthetic Cyber-Fraud Investigation Dataset",

        "case_type":
            "SYNTHETIC_DEMO",

        "case_path":
            str(DEMO_DIR),

        "manifest_path":
            str(manifest_path),

        "activated_at":
            datetime.now().isoformat(),
    }

    with open(
        ACTIVE_CASE_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            active_case,
            file,
            indent=4
        )

    return manifest


# ============================================================
# GET ACTIVE CASE
# ============================================================

def get_active_case():

    ensure_directories()

    if not ACTIVE_CASE_FILE.exists():

        return None

    try:

        with open(
            ACTIVE_CASE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception:

        return None


# ============================================================
# ACTIVATE EXISTING CASE
# ============================================================

def activate_case(case_id):

    ensure_directories()

    case_dir = (
        CASES_DIR
        / case_id
    )

    manifest_path = (
        case_dir
        / "case_manifest.json"
    )

    if not case_dir.exists():

        raise FileNotFoundError(
            f"Case not found: {case_id}"
        )

    if not manifest_path.exists():

        raise FileNotFoundError(
            f"Case manifest not found: {manifest_path}"
        )

    # --------------------------------------------------------
    # Load manifest
    # --------------------------------------------------------

    with open(
        manifest_path,
        "r",
        encoding="utf-8"
    ) as file:

        manifest = json.load(file)

    # --------------------------------------------------------
    # Copy normalized files to working directory
    # --------------------------------------------------------

    normalized_dir = (
        case_dir
        / "normalized"
    )

    for filename in WORKING_FILES.values():

        source_path = (
            normalized_dir
            / filename
        )

        destination = (
            DATA_DIR
            / filename
        )

        if source_path.exists():

            shutil.copy2(
                source_path,
                destination
            )

    # --------------------------------------------------------
    # Update active case
    # --------------------------------------------------------

    active_case = {

        "case_id":
            case_id,

        "case_name":
            manifest.get(
                "case_name",
                case_id
            ),

        "case_type":
            manifest.get(
                "case_type",
                "USER_INVESTIGATION"
            ),

        "case_path":
            str(case_dir),

        "manifest_path":
            str(manifest_path),

        "activated_at":
            datetime.now().isoformat(),
    }

    with open(
        ACTIVE_CASE_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            active_case,
            file,
            indent=4
        )

    return manifest


# ============================================================
# MAIN TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 70)
    print("CHANAKYA-GRAPH — CASE MANAGER")
    print("=" * 70)

    ensure_directories()

    print("\nChecking demo dataset...")

    demo_dir = ensure_demo_dataset()

    print(
        f"Demo directory: {demo_dir}"
    )

    print("\nActivating demo dataset...")

    manifest = activate_demo_dataset()

    print(
        f"\nActive Case: "
        f"{manifest['case_id']}"
    )

    print(
        f"Case Name: "
        f"{manifest['case_name']}"
    )

    if "multi_day_scenario" in manifest:

        scenario = manifest[
            "multi_day_scenario"
        ]

        print("\nMulti-Day Scenario:")

        print(
            f"Transactions: "
            f"{scenario['transaction_count']}"
        )

        print(
            f"Total Loss: "
            f"INR {scenario['total_amount_inr']:,}"
        )

        print(
            f"First Transaction: "
            f"{scenario['first_transaction']}"
        )

        print(
            f"Last Transaction: "
            f"{scenario['last_transaction']}"
        )

        print(
            f"Complaint: "
            f"{scenario['complaint_timestamp']}"
        )

    print("\n" + "=" * 70)
    print("CASE MANAGER READY")
    print("=" * 70)