import pandas as pd
from pathlib import Path


# ============================================================
# DEMO CASE INFORMATION
# ============================================================

DEMO_CASE_ID = "DEMO-CYB-2026-0001"
DATA_SOURCE = "SYNTHETIC_DEMO"

VICTIM_ACCOUNT = "ACC-MULTIDAY-VICTIM-001"
VICTIM_PHONE = "+919800000101"

RECIPIENT_1 = "ACC-MULE-001"
RECIPIENT_2 = "ACC-MULE-002"
RECIPIENT_3 = "ACC-MULE-003"


# ============================================================
# MULTI-DAY TRANSACTIONS
# ============================================================

MULTI_DAY_TRANSACTIONS = [
    {
        "transaction_id": "MD-FRAUD-001",
        "timestamp": "2026-09-10 10:15:00",
        "sender_account": VICTIM_ACCOUNT,
        "receiver_account": RECIPIENT_1,
        "sender_type": "VICTIM",
        "receiver_type": "MULE",
        "amount_inr": 2500,
        "transaction_status": "SUCCESS",
        "reference_id": "MD-REF-001",
    },
    {
        "transaction_id": "MD-FRAUD-002",
        "timestamp": "2026-09-11 14:32:00",
        "sender_account": VICTIM_ACCOUNT,
        "receiver_account": RECIPIENT_1,
        "sender_type": "VICTIM",
        "receiver_type": "MULE",
        "amount_inr": 7000,
        "transaction_status": "SUCCESS",
        "reference_id": "MD-REF-002",
    },
    {
        "transaction_id": "MD-FRAUD-003",
        "timestamp": "2026-09-13 09:47:00",
        "sender_account": VICTIM_ACCOUNT,
        "receiver_account": RECIPIENT_2,
        "sender_type": "VICTIM",
        "receiver_type": "MULE",
        "amount_inr": 1800,
        "transaction_status": "SUCCESS",
        "reference_id": "MD-REF-003",
    },
    {
        "transaction_id": "MD-FRAUD-004",
        "timestamp": "2026-09-16 18:21:00",
        "sender_account": VICTIM_ACCOUNT,
        "receiver_account": RECIPIENT_1,
        "sender_type": "VICTIM",
        "receiver_type": "MULE",
        "amount_inr": 12000,
        "transaction_status": "SUCCESS",
        "reference_id": "MD-REF-004",
    },
    {
        "transaction_id": "MD-FRAUD-005",
        "timestamp": "2026-09-19 11:06:00",
        "sender_account": VICTIM_ACCOUNT,
        "receiver_account": RECIPIENT_3,
        "sender_type": "VICTIM",
        "receiver_type": "MULE",
        "amount_inr": 6500,
        "transaction_status": "SUCCESS",
        "reference_id": "MD-REF-005",
    },
]


# ============================================================
# MULTI-DAY COMPLAINT
# ============================================================

MULTI_DAY_COMPLAINT = {
    "complaint_id": "MD-COMPLAINT-001",
    "complaint_timestamp": "2026-09-20 09:30:00",
    "victim_name": "DEMO MULTI DAY VICTIM",
    "victim_phone": VICTIM_PHONE,
    "victim_account": VICTIM_ACCOUNT,
    "fraud_category": "SUSPECTED_UPI_FRAUD",
    "complaint_description": (
        "Victim reported multiple unauthorized UPI deductions "
        "noticed after several transactions occurred across "
        "different dates."
    ),
    "reported_amount_inr": 29800,
    "reported_caller": VICTIM_PHONE,
}


# ============================================================
# REQUIRED COLUMNS
# ============================================================

UPI_COLUMNS = [
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
]


COMPLAINT_COLUMNS = [
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
]


# ============================================================
# FORCE IDENTIFIER COLUMNS TO STRING
# ============================================================

def force_string_columns(df, columns):

    for column in columns:

        if column not in df.columns:
            df[column] = ""

        # object dtype prevents Pandas 3.x upcast errors
        df[column] = df[column].astype("object")

        # Convert existing non-null values to strings
        df[column] = df[column].apply(
            lambda value:
                str(value)
                if pd.notna(value)
                else ""
        )

    return df


# ============================================================
# ADD / REPAIR MULTI-DAY TRANSACTIONS
# ============================================================

def add_multiday_transactions(demo_dir: Path):

    upi_path = demo_dir / "upi_transactions.csv"

    if upi_path.exists():

        upi_df = pd.read_csv(
            upi_path,
            dtype=str
        )

    else:

        upi_df = pd.DataFrame(
            columns=UPI_COLUMNS
        )

    # --------------------------------------------------------
    # Ensure columns exist
    # --------------------------------------------------------

    for column in UPI_COLUMNS:

        if column not in upi_df.columns:
            upi_df[column] = ""

    # --------------------------------------------------------
    # Force identifiers to strings
    # --------------------------------------------------------

    string_columns = [
        "transaction_id",
        "case_id",
        "timestamp",
        "sender_account",
        "receiver_account",
        "sender_type",
        "receiver_type",
        "transaction_status",
        "reference_id",
        "data_source",
    ]

    upi_df = force_string_columns(
        upi_df,
        string_columns
    )

    # --------------------------------------------------------
    # Add OR repair all 5 transactions
    # --------------------------------------------------------

    for transaction in MULTI_DAY_TRANSACTIONS:

        transaction_id = str(
            transaction["transaction_id"]
        )

        existing = (
            upi_df["transaction_id"]
            .astype(str)
            .eq(transaction_id)
        )

        complete_record = {
            **transaction,
            "case_id": DEMO_CASE_ID,
            "data_source": DATA_SOURCE,
        }

        if existing.any():

            index = upi_df.index[
                existing
            ][0]

            for column, value in complete_record.items():

                upi_df.at[
                    index,
                    column
                ] = str(value)

        else:

            new_record = pd.DataFrame(
                [complete_record]
            )

            upi_df = pd.concat(
                [
                    upi_df,
                    new_record
                ],
                ignore_index=True
            )

    # --------------------------------------------------------
    # Correct amount dtype
    # --------------------------------------------------------

    upi_df["amount_inr"] = pd.to_numeric(
        upi_df["amount_inr"],
        errors="coerce"
    ).fillna(0)

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    upi_df.to_csv(
        upi_path,
        index=False
    )

    return upi_df


# ============================================================
# ADD / REPAIR MULTI-DAY COMPLAINT
# ============================================================

def add_multiday_complaint(demo_dir: Path):

    complaints_path = (
        demo_dir / "complaints.csv"
    )

    if complaints_path.exists():

        complaints_df = pd.read_csv(
            complaints_path,
            dtype=str
        )

    else:

        complaints_df = pd.DataFrame(
            columns=COMPLAINT_COLUMNS
        )

    # --------------------------------------------------------
    # Ensure columns exist
    # --------------------------------------------------------

    for column in COMPLAINT_COLUMNS:

        if column not in complaints_df.columns:
            complaints_df[column] = ""

    # --------------------------------------------------------
    # Force ALL complaint columns to object/string
    # --------------------------------------------------------

    complaints_df = force_string_columns(
        complaints_df,
        COMPLAINT_COLUMNS
    )

    complaint_id = str(
        MULTI_DAY_COMPLAINT[
            "complaint_id"
        ]
    )

    existing = (
        complaints_df["complaint_id"]
        .astype(str)
        .eq(complaint_id)
    )

    complete_complaint = {
        **MULTI_DAY_COMPLAINT,
        "case_id": DEMO_CASE_ID,
        "data_source": DATA_SOURCE,
    }

    if existing.any():

        index = complaints_df.index[
            existing
        ][0]

        for column, value in complete_complaint.items():

            complaints_df.at[
                index,
                column
            ] = str(value)

    else:

        new_record = pd.DataFrame(
            [complete_complaint]
        )

        complaints_df = pd.concat(
            [
                complaints_df,
                new_record
            ],
            ignore_index=True
        )

    # --------------------------------------------------------
    # Amount as numeric
    # --------------------------------------------------------

    complaints_df["reported_amount_inr"] = pd.to_numeric(
        complaints_df["reported_amount_inr"],
        errors="coerce"
    ).fillna(0)

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    complaints_df.to_csv(
        complaints_path,
        index=False
    )

    return complaints_df


# ============================================================
# MAIN SCENARIO
# ============================================================

def add_multiday_demo_scenario(demo_dir: Path):

    demo_dir = Path(demo_dir)

    demo_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    # Add / repair UPI transactions
    upi_df = add_multiday_transactions(
        demo_dir
    )

    # Add / repair complaint
    complaints_df = add_multiday_complaint(
        demo_dir
    )

    # --------------------------------------------------------
    # Extract our five transactions
    # --------------------------------------------------------

    scenario_ids = {
        item["transaction_id"]
        for item in MULTI_DAY_TRANSACTIONS
    }

    scenario_df = upi_df[
        upi_df["transaction_id"]
        .astype(str)
        .isin(scenario_ids)
    ].copy()

    # --------------------------------------------------------
    # Numeric amount
    # --------------------------------------------------------

    scenario_df["amount_inr"] = pd.to_numeric(
        scenario_df["amount_inr"],
        errors="coerce"
    ).fillna(0)

    # --------------------------------------------------------
    # Timestamp
    # --------------------------------------------------------

    scenario_df["timestamp"] = pd.to_datetime(
        scenario_df["timestamp"],
        errors="coerce"
    )

    # --------------------------------------------------------
    # Calculations
    # --------------------------------------------------------

    total_amount = int(
        scenario_df["amount_inr"].sum()
    )

    first_transaction = (
        scenario_df["timestamp"].min()
    )

    last_transaction = (
        scenario_df["timestamp"].max()
    )

    complaint_timestamp = pd.Timestamp(
        MULTI_DAY_COMPLAINT[
            "complaint_timestamp"
        ]
    )

    detection_delay = (
        complaint_timestamp
        - last_transaction
    ).total_seconds() / 86400

    unique_recipients = (
        scenario_df[
            "receiver_account"
        ]
        .nunique()
    )

    return {

        "scenario":
            "MULTI_DAY_REPEATED_DEDUCTION",

        "transaction_count":
            len(scenario_df),

        "total_amount_inr":
            total_amount,

        "first_transaction":
            str(first_transaction),

        "last_transaction":
            str(last_transaction),

        "complaint_timestamp":
            str(complaint_timestamp),

        "unique_recipients":
            int(unique_recipients),

        "detection_delay_days":
            round(
                detection_delay,
                2
            ),
    }


# ============================================================
# PUBLIC FUNCTION
# ============================================================

def ensure_multiday_demo_scenario(
    demo_dir: Path
):

    result = add_multiday_demo_scenario(
        demo_dir
    )

    print()
    print("=" * 65)
    print("CHANAKYA-GRAPH — MULTI-DAY DEMO SCENARIO")
    print("=" * 65)

    print(
        f"Transactions       : "
        f"{result['transaction_count']}"
    )

    print(
        f"Total amount       : "
        f"INR {result['total_amount_inr']:,}"
    )

    print(
        f"First transaction  : "
        f"{result['first_transaction']}"
    )

    print(
        f"Last transaction   : "
        f"{result['last_transaction']}"
    )

    print(
        f"Complaint date     : "
        f"{result['complaint_timestamp']}"
    )

    print(
        f"Unique recipients  : "
        f"{result['unique_recipients']}"
    )

    print(
        f"Detection delay    : "
        f"{result['detection_delay_days']} days"
    )

    print("=" * 65)

    return result