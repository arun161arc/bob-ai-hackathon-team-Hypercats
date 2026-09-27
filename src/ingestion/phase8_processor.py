"""
CHANAKYA-GRAPH
PHASE 8 — CASE INTAKE & EVIDENCE PROCESSING

This module:
1. Validates CDR, UPI, complaint and device CSV files
2. Creates a unique investigation case
3. Calculates SHA-256 hashes
4. Stores original evidence
5. Creates canonical/normalized evidence
6. Creates case_manifest.json
7. Activates the case
8. Creates phase8_processing_report.json

Does NOT modify Phases 1–7.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import pandas as pd


# ============================================================
# PATHS
# ============================================================

SRC_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = SRC_DIR / "data"

CASES_DIR = DATA_DIR / "cases"

OUTPUT_DIR = SRC_DIR / "output"

PROCESSING_DIR = OUTPUT_DIR / "processing"

CASES_DIR.mkdir(parents=True, exist_ok=True)
PROCESSING_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# EVIDENCE TYPES
# ============================================================

REQUIRED_EVIDENCE = {
    "cdr": {
        "display_name": "Call Detail Records (CDR)",
        "required_columns": [
            "record_id",
            "timestamp",
            "caller",
            "called",
            "duration_seconds",
            "imei",
            "tower_id",
            "call_type",
        ],
    },

    "upi": {
        "display_name": "UPI Transactions",
        "required_columns": [
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
    },

    "complaints": {
        "display_name": "Cyber Fraud Complaints",
        "required_columns": [
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
    },

    "devices": {
        "display_name": "Device / IMEI Records",
        "required_columns": [
            "device_record_id",
            "phone_number",
            "imei",
            "device_type",
            "first_seen",
            "last_seen",
            "tower_id",
        ],
    },
}


# ============================================================
# COLUMN ALIASES
# ============================================================

COLUMN_ALIASES = {
    "cdr": {
        "id": "record_id",
        "recordid": "record_id",
        "record_id": "record_id",
        "datetime": "timestamp",
        "date_time": "timestamp",
        "time": "timestamp",
        "caller_number": "caller",
        "calling_number": "caller",
        "called_number": "called",
        "receiver": "called",
        "duration": "duration_seconds",
        "duration_sec": "duration_seconds",
        "device_imei": "imei",
        "device_id": "imei",
        "tower": "tower_id",
        "towerid": "tower_id",
        "type": "call_type",
    },

    "upi": {
        "id": "transaction_id",
        "transactionid": "transaction_id",
        "transaction_id": "transaction_id",
        "datetime": "timestamp",
        "date_time": "timestamp",
        "time": "timestamp",
        "sender": "sender_account",
        "senderaccount": "sender_account",
        "sender_account": "sender_account",
        "receiver": "receiver_account",
        "receiveraccount": "receiver_account",
        "receiver_account": "receiver_account",
        "sender_category": "sender_type",
        "receiver_category": "receiver_type",
        "amount": "amount_inr",
        "amount_rs": "amount_inr",
        "amount_inr": "amount_inr",
        "status": "transaction_status",
        "transactionstatus": "transaction_status",
        "reference": "reference_id",
        "referenceid": "reference_id",
    },

    "complaints": {
        "id": "complaint_id",
        "complaintid": "complaint_id",
        "complaint_id": "complaint_id",
        "timestamp": "complaint_timestamp",
        "datetime": "complaint_timestamp",
        "date_time": "complaint_timestamp",
        "name": "victim_name",
        "victim": "victim_name",
        "victimname": "victim_name",
        "phone": "victim_phone",
        "mobile": "victim_phone",
        "victimphone": "victim_phone",
        "account": "victim_account",
        "victimaccount": "victim_account",
        "category": "fraud_category",
        "description": "complaint_description",
        "reported_amount": "reported_amount_inr",
        "amount": "reported_amount_inr",
        "reported_caller": "reported_caller",
        "caller": "reported_caller",
    },

    "devices": {
        "id": "device_record_id",
        "deviceid": "device_record_id",
        "device_record_id": "device_record_id",
        "phone": "phone_number",
        "mobile": "phone_number",
        "number": "phone_number",
        "imei": "imei",
        "device_imei": "imei",
        "device": "device_type",
        "type": "device_type",
        "firstseen": "first_seen",
        "first_seen": "first_seen",
        "lastseen": "last_seen",
        "last_seen": "last_seen",
        "tower": "tower_id",
        "towerid": "tower_id",
    },
}


# ============================================================
# NORMALIZE COLUMN NAME
# ============================================================

def clean_column_name(column: str) -> str:
    """
    Convert a column name into a consistent format.
    """

    return (
        str(column)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("/", "_")
    )


# ============================================================
# NORMALIZE DATAFRAME COLUMNS
# ============================================================

def normalize_columns(
    df: pd.DataFrame,
    evidence_type: str,
) -> pd.DataFrame:
    """
    Normalize column names and apply aliases.
    """

    df = df.copy()

    rename_map = {}

    aliases = COLUMN_ALIASES.get(
        evidence_type,
        {},
    )

    for column in df.columns:

        cleaned = clean_column_name(column)

        target = aliases.get(
            cleaned,
            cleaned,
        )

        rename_map[column] = target

    df = df.rename(
        columns=rename_map
    )

    return df


# ============================================================
# LOAD CSV
# ============================================================

def load_csv(
    file_path: Path,
) -> pd.DataFrame:
    """
    Load CSV with identifiers preserved as strings.
    """

    return pd.read_csv(
        file_path,
        dtype=str,
        keep_default_na=False,
    )


# ============================================================
# SHA-256
# ============================================================

def calculate_sha256(
    file_path: Path,
) -> str:
    """
    Calculate SHA-256 hash of original evidence.
    """

    sha256 = hashlib.sha256()

    with open(
        file_path,
        "rb",
    ) as file:

        while True:

            chunk = file.read(
                1024 * 1024
            )

            if not chunk:
                break

            sha256.update(chunk)

    return sha256.hexdigest()


# ============================================================
# VALIDATE EVIDENCE
# ============================================================

def validate_evidence(
    file_path: Path,
    evidence_type: str,
) -> Dict[str, Any]:
    """
    Validate one evidence CSV.
    """

    config = REQUIRED_EVIDENCE.get(
        evidence_type
    )

    result = {
        "evidence_type": evidence_type,
        "display_name": (
            config["display_name"]
            if config
            else evidence_type
        ),
        "file_name": file_path.name,
        "valid": False,
        "status": "FAILED",
        "row_count": 0,
        "columns": [],
        "missing_columns": [],
        "extra_columns": [],
        "sha256": None,
        "error": None,
    }

    # --------------------------------------------------------
    # File check
    # --------------------------------------------------------

    if not file_path.exists():

        result["error"] = (
            f"File not found: {file_path}"
        )

        return result

    if file_path.suffix.lower() != ".csv":

        result["error"] = (
            "Only CSV evidence files are supported."
        )

        return result

    # --------------------------------------------------------
    # Hash
    # --------------------------------------------------------

    try:

        result["sha256"] = calculate_sha256(
            file_path
        )

    except Exception as exc:

        result["error"] = (
            f"Unable to calculate SHA-256: {exc}"
        )

        return result

    # --------------------------------------------------------
    # Read CSV
    # --------------------------------------------------------

    try:

        df = load_csv(
            file_path
        )

    except Exception as exc:

        result["error"] = (
            f"Unable to read CSV: {exc}"
        )

        return result

    # --------------------------------------------------------
    # Normalize columns
    # --------------------------------------------------------

    df = normalize_columns(
        df,
        evidence_type,
    )

    result["row_count"] = len(df)

    result["columns"] = list(
        df.columns
    )

    # --------------------------------------------------------
    # Empty file
    # --------------------------------------------------------

    if df.empty:

        result["error"] = (
            "Evidence file contains zero records."
        )

        return result

    # --------------------------------------------------------
    # Required schema
    # --------------------------------------------------------

    if config is None:

        result["error"] = (
            f"Unknown evidence type: {evidence_type}"
        )

        return result

    required_columns = config[
        "required_columns"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    extra_columns = [
        column
        for column in df.columns
        if column not in required_columns
    ]

    result["missing_columns"] = (
        missing_columns
    )

    result["extra_columns"] = (
        extra_columns
    )

    if missing_columns:

        result["error"] = (
            "Missing required columns: "
            + ", ".join(missing_columns)
        )

        return result

    # --------------------------------------------------------
    # Valid
    # --------------------------------------------------------

    result["valid"] = True
    result["status"] = "VALIDATED"

    return result


# ============================================================
# GENERATE CASE ID
# ============================================================

def generate_case_id(
    case_title: str,
) -> str:
    """
    Generate unique investigation case ID.
    """

    timestamp = datetime.now()

    seed = (
        f"{timestamp.timestamp()}|"
        f"{case_title}"
    )

    unique_part = hashlib.sha256(
        seed.encode(
            "utf-8"
        )
    ).hexdigest()[:6].upper()

    return (
        "CASE-"
        + timestamp.strftime(
            "%Y%m%d-%H%M%S"
        )
        + "-"
        + unique_part
    )


# ============================================================
# CREATE CASE DIRECTORIES
# ============================================================

def create_case_directories(
    case_id: str,
) -> Dict[str, Path]:
    """
    Create case directory structure.
    """

    case_dir = (
        CASES_DIR
        / case_id
    )

    raw_dir = (
        case_dir
        / "raw"
    )

    normalized_dir = (
        case_dir
        / "normalized"
    )

    raw_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    normalized_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    return {
        "case": case_dir,
        "raw": raw_dir,
        "canonical": normalized_dir,
    }


# ============================================================
# PROCESS ONE EVIDENCE FILE
# ============================================================

def process_evidence(
    case_id: str,
    source_path: Path,
    evidence_type: str,
) -> Dict[str, Any]:
    """
    Validate and store one evidence file.
    """

    validation = validate_evidence(
        source_path,
        evidence_type,
    )

    if not validation["valid"]:

        return validation

    directories = create_case_directories(
        case_id
    )

    raw_dir = directories["raw"]

    normalized_dir = directories[
        "normalized"
    ]

    # --------------------------------------------------------
    # Preserve original evidence
    # --------------------------------------------------------

    raw_path = (
        raw_dir
        / source_path.name
    )

    shutil.copy2(
        source_path,
        raw_path,
    )

    # --------------------------------------------------------
    # Create canonical version
    # --------------------------------------------------------

    df = load_csv(
        source_path
    )

    df = normalize_columns(
        df,
        evidence_type,
    )

    canonical_path = (
        normalized_dir
        / f"{evidence_type}.csv"
    )

    df.to_csv(
        canonical_path,
        index=False,
    )

    # --------------------------------------------------------
    # Result
    # --------------------------------------------------------

    validation.update(
        {
            "status": "PROCESSED",
            "raw_path": str(
                raw_path
            ),
            "canonical_path": str(
                canonical_path
            ),
            "canonical_row_count": len(df),
        }
    )

    return validation


# ============================================================
# SAVE JSON
# ============================================================

def save_json(
    path: Path,
    data: Dict[str, Any],
) -> None:
    """
    Save JSON with readable formatting.
    """

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False,
        )


# ============================================================
# PROCESS COMPLETE CASE
# ============================================================

def process_case(
    evidence_files: Dict[str, Path],
    case_title: str = "Cyber-Fraud Investigation",
    description: str = "",
) -> Dict[str, Any]:
    """
    Main Phase 8 function.

    evidence_files:

        {
            "cdr": Path(...),
            "upi": Path(...),
            "complaints": Path(...),
            "devices": Path(...)
        }
    """

    started_at = datetime.now()

    result = {
        "phase": 8,
        "phase_name": (
            "Case Intake & Evidence Processing"
        ),
        "status": "STARTED",
        "success": False,
        "case_id": None,
        "case_title": case_title,
        "description": description,
        "started_at": started_at.isoformat(),
        "completed_at": None,
        "stages": [],
        "evidence": {},
        "errors": [],
    }

    # ========================================================
    # STAGE 1 — INTAKE
    # ========================================================

    result["stages"].append(
        {
            "stage": "CASE_INTAKE",
            "status": "COMPLETED",
            "message": (
                "Evidence intake initialized."
            ),
        }
    )

    # ========================================================
    # CHECK REQUIRED FILES
    # ========================================================

    required_types = list(
        REQUIRED_EVIDENCE.keys()
    )

    missing = [
        evidence_type
        for evidence_type in required_types
        if evidence_type not in evidence_files
        or evidence_files[evidence_type] is None
    ]

    if missing:

        for evidence_type in missing:

            result["errors"].append(
                "Missing evidence: "
                + REQUIRED_EVIDENCE[
                    evidence_type
                ]["display_name"]
            )

        result["status"] = "FAILED"

        result["completed_at"] = (
            datetime.now().isoformat()
        )

        return result

    # ========================================================
    # STAGE 2 — VALIDATION
    # ========================================================

    validation_failed = False

    for evidence_type in required_types:

        file_path = Path(
            evidence_files[
                evidence_type
            ]
        )

        validation = validate_evidence(
            file_path,
            evidence_type,
        )

        result["evidence"][
            evidence_type
        ] = validation

        if not validation["valid"]:

            validation_failed = True

            result["errors"].append(
                f"{validation['display_name']}: "
                f"{validation['error']}"
            )

    if validation_failed:

        result["stages"].append(
            {
                "stage": "EVIDENCE_VALIDATION",
                "status": "FAILED",
                "message": (
                    "Evidence validation failed."
                ),
            }
        )

        result["status"] = "FAILED"

        result["completed_at"] = (
            datetime.now().isoformat()
        )

        return result

    result["stages"].append(
        {
            "stage": "EVIDENCE_VALIDATION",
            "status": "COMPLETED",
            "message": (
                "All four evidence categories "
                "passed schema validation."
            ),
        }
    )

    # ========================================================
    # STAGE 3 — CREATE CASE
    # ========================================================

    case_id = generate_case_id(
        case_title
    )

    result["case_id"] = case_id

    directories = create_case_directories(
        case_id
    )

    result["stages"].append(
        {
            "stage": "CASE_CREATION",
            "status": "COMPLETED",
            "message": (
                f"Created investigation case "
                f"{case_id}."
            ),
        }
    )

    # ========================================================
    # STAGE 4 — PROCESS EVIDENCE
    # ========================================================

    processing_failed = False

    for evidence_type in required_types:

        file_path = Path(
            evidence_files[
                evidence_type
            ]
        )

        processed = process_evidence(
            case_id,
            file_path,
            evidence_type,
        )

        result["evidence"][
            evidence_type
        ] = processed

        if not processed["valid"]:

            processing_failed = True

            result["errors"].append(
                f"{processed['display_name']}: "
                f"{processed['error']}"
            )

    if processing_failed:

        result["stages"].append(
            {
                "stage": "EVIDENCE_PROCESSING",
                "status": "FAILED",
                "message": (
                    "One or more evidence files "
                    "could not be processed."
                ),
            }
        )

        result["status"] = "FAILED"

        result["completed_at"] = (
            datetime.now().isoformat()
        )

        report_path = (
            directories["case"]
            / "phase8_processing_report.json"
        )

        save_json(
            report_path,
            result,
        )

        return result

    result["stages"].append(
        {
            "stage": "EVIDENCE_PROCESSING",
            "status": "COMPLETED",
            "message": (
                "All evidence files were stored "
                "and canonicalized."
            ),
        }
    )

    # ========================================================
    # STAGE 5 — MANIFEST
    # ========================================================

    manifest = {
        "case_id": case_id,
        "case_title": case_title,
        "description": description,
        "created_at": datetime.now().isoformat(),
        "data_class": "CASE_EVIDENCE",
        "phase": 8,
        "evidence": {},
    }

    for evidence_type in required_types:

        evidence = result[
            "evidence"
        ][evidence_type]

        manifest["evidence"][
            evidence_type
        ] = {
            "display_name": evidence[
                "display_name"
            ],
            "file_name": evidence[
                "file_name"
            ],
            "row_count": evidence[
                "row_count"
            ],
            "sha256": evidence[
                "sha256"
            ],
            "raw_path": evidence.get(
                "raw_path"
            ),
            "canonical_path": evidence.get(
                "canonical_path"
            ),
        }

    manifest_path = (
        directories["case"]
        / "case_manifest.json"
    )

    save_json(
        manifest_path,
        manifest,
    )

    result["manifest_path"] = str(
        manifest_path
    )

    result["stages"].append(
        {
            "stage": "EVIDENCE_INTEGRITY",
            "status": "COMPLETED",
            "message": (
                "SHA-256 integrity hashes "
                "recorded for all evidence."
            ),
        }
    )

    # ========================================================
    # STAGE 6 — ACTIVATE CASE
    # ========================================================

    active_case_path = (
        CASES_DIR
        / "active_case.json"
    )

    active_case = {
        "case_id": case_id,
        "case_title": case_title,
        "description": description,
        "case_path": str(
            directories["case"]
        ),
        "activated_at": datetime.now().isoformat(),
        "data_class": "CASE_EVIDENCE",
        "phase": 8,
    }

    save_json(
        active_case_path,
        active_case,
    )

    result["active_case_path"] = str(
        active_case_path
    )

    result["stages"].append(
        {
            "stage": "CASE_ACTIVATION",
            "status": "COMPLETED",
            "message": (
                f"Case {case_id} is now active."
            ),
        }
    )

    # ========================================================
    # COMPLETE
    # ========================================================

    result["status"] = "COMPLETED"

    result["success"] = True

    result["completed_at"] = (
        datetime.now().isoformat()
    )

    report_path = (
        directories["case"]
        / "phase8_processing_report.json"
    )

    save_json(
        report_path,
        result,
    )

    result["processing_report_path"] = str(
        report_path
    )

    return result


# ============================================================
# PROCESS CURRENT DATASET
# ============================================================

def process_current_demo_dataset() -> Dict[str, Any]:
    """
    Process the existing src/data CSV files.

    This is used to test Phase 8 without Streamlit.
    """

    return process_case(
        {
            "cdr": DATA_DIR / "cdr_records.csv",
            "upi": DATA_DIR / "upi_transactions.csv",
            "complaints": DATA_DIR / "complaints.csv",
            "devices": DATA_DIR / "device_records.csv",
        },
        case_title=(
            "Synthetic Cyber-Fraud Investigation"
        ),
        description=(
            "Phase 8 validation using the "
            "current synthetic investigation dataset."
        ),
    )


# ============================================================
# PRINT RESULT
# ============================================================

def print_result(
    result: Dict[str, Any],
) -> None:

    print()
    print("=" * 72)
    print(
        "CHANAKYA-GRAPH — PHASE 8"
    )
    print(
        "CASE INTAKE & EVIDENCE PROCESSING"
    )
    print("=" * 72)

    print()

    print(
        "Status :",
        result.get("status"),
    )

    print(
        "Success:",
        result.get("success"),
    )

    print(
        "Case ID:",
        result.get("case_id"),
    )

    print()

    print("Evidence:")

    for evidence_type, evidence in result[
        "evidence"
    ].items():

        print(
            f"\n  {evidence['display_name']}"
        )

        print(
            f"    Status : "
            f"{evidence.get('status')}"
        )

        print(
            f"    Rows   : "
            f"{evidence.get('row_count')}"
        )

        print(
            f"    SHA256 : "
            f"{evidence.get('sha256')}"
        )

        if evidence.get(
            "canonical_path"
        ):

            print(
                f"    Canonical: "
                f"{evidence['canonical_path']}"
            )

    print()

    print("Processing stages:")

    for stage in result[
        "stages"
    ]:

        print(
            f"  [{stage['status']}] "
            f"{stage['stage']}"
        )

        print(
            f"      {stage['message']}"
        )

    if result["errors"]:

        print()

        print("Errors:")

        for error in result[
            "errors"
        ]:

            print(
                "  -",
                error,
            )

    print()

    print("=" * 72)

    if result["success"]:

        print(
            "PHASE 8 COMPLETE"
        )

    else:

        print(
            "PHASE 8 FAILED"
        )

    print("=" * 72)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    result = process_current_demo_dataset()

    print_result(
        result
    )