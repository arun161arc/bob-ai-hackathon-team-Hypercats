import json
from collections import defaultdict
from pathlib import Path

import pandas as pd


# ============================================================
# PATHS
# ============================================================

SRC_DIR = Path(__file__).resolve().parents[1]

CASES_DIR = SRC_DIR / "data" / "cases"
ACTIVE_CASE_FILE = CASES_DIR / "active_case.json"

OUTPUT_DIR = SRC_DIR / "output" / "investigation"

OUTPUT_FILE = (
    OUTPUT_DIR / "edge_case_intelligence.json"
)


# ============================================================
# HELPERS
# ============================================================

def load_json(path):

    path = Path(path)

    if not path.exists():
        return {}

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


def save_json(path, data):

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            indent=2,
            ensure_ascii=False,
            default=str
        )


def clean(value):

    if value is None:
        return ""

    return str(value).strip()


def unique(values):

    result = []

    seen = set()

    for value in values:

        value = clean(value)

        if not value:
            continue

        if value not in seen:

            seen.add(value)

            result.append(value)

    return result


def evidence_id(row, fallback):

    for field in [
        "record_id",
        "transaction_id",
        "complaint_id",
        "device_record_id",
    ]:

        value = clean(
            row.get(field, "")
        )

        if value:
            return value

    return fallback


# ============================================================
# ACTIVE CASE
# ============================================================

def load_active_case():

    active = load_json(
        ACTIVE_CASE_FILE
    )

    if not active:

        raise RuntimeError(
            "No active case found."
        )

    return active


def get_case_directory(active):

    case_id = (
        active.get("case_id")
        or active.get("active_case_id")
    )

    if not case_id:

        raise RuntimeError(
            "Active case has no case_id."
        )

    return (
        CASES_DIR / str(case_id)
    )


# ============================================================
# LOAD DATA
# ============================================================

def load_data(active):

    case_dir = get_case_directory(
        active
    )

    canonical = (
        case_dir / "canonical"
    )

    paths = {
        "cdr":
            canonical / "cdr.csv",

        "upi":
            canonical / "upi.csv",

        "complaints":
            canonical / "complaints.csv",

        "devices":
            canonical / "devices.csv",
    }

    data = {}

    for name, path in paths.items():

        if path.exists():

            df = pd.read_csv(
                path,
                dtype=str
            ).fillna("")

        else:

            df = pd.DataFrame()

        data[name] = df

    return data


# ============================================================
# FINDING BUILDER
# ============================================================

def finding(
    edge_case,
    classification,
    message,
    evidence_ids=None,
    severity="INFO"
):

    return {
        "edge_case": edge_case,
        "classification": classification,
        "severity": severity,
        "message": message,
        "evidence_ids":
            unique(evidence_ids or []),
    }


# ============================================================
# 1. BURNED SIM / CLOSED ACCOUNT
# ============================================================

def detect_burned_sim_and_closed_account(
    data
):

    findings = []

    cdr = data["cdr"]

    upi = data["upi"]

    devices = data["devices"]

    # We cannot establish that a SIM/account
    # was actually burned/closed unless the
    # supplied evidence contains such status.

    sim_status_columns = [
        "sim_status",
        "phone_status",
        "status",
    ]

    account_status_columns = [
        "account_status",
        "bank_account_status",
    ]

    has_sim_status = any(
        column in cdr.columns
        for column in sim_status_columns
    )

    has_account_status = any(
        column in upi.columns
        for column in account_status_columns
    )

    if not has_sim_status:

        findings.append(
            finding(
                "BURNED_SIM",
                "EVIDENCE_GAP",
                "SIM closure/burn status is not directly "
                "observable from the supplied CDR fields.",
            )
        )

    if not has_account_status:

        findings.append(
            finding(
                "CLOSED_ACCOUNT",
                "EVIDENCE_GAP",
                "Bank-account closure status is not directly "
                "observable from the supplied UPI fields.",
            )
        )

    # Historical IMEI pivot

    phone_imeis = defaultdict(set)

    for _, row in devices.iterrows():

        phone = clean(
            row.get("phone_number")
        )

        imei = clean(
            row.get("imei")
        )

        if phone and imei:

            phone_imeis[phone].add(
                imei
            )

    historical_links = []

    for phone, imeis in phone_imeis.items():

        if len(imeis) > 0:

            historical_links.append(
                {
                    "phone": phone,
                    "historical_imeis":
                        sorted(imeis),
                }
            )

    if historical_links:

        evidence = []

        for _, row in devices.head(50).iterrows():

            evidence.append(
                evidence_id(
                    row,
                    "DEVICE"
                )
            )

        findings.append(
            finding(
                "HISTORICAL_DEVICE_PIVOT",
                "DERIVED",
                f"{len(historical_links)} phone numbers "
                "have historical device associations that "
                "can be used as a pivot when a SIM is no "
                "longer active.",
                evidence,
                "INFO",
            )
        )

    # Last known transaction destination

    if not upi.empty:

        receiver_column = (
            "receiver_account"
            if "receiver_account"
            in upi.columns
            else None
        )

        if receiver_column:

            receivers = unique(
                upi[receiver_column].tolist()
            )

            if receivers:

                findings.append(
                    finding(
                        "LAST_KNOWN_DESTINATIONS",
                        "DERIVED",
                        f"{len(receivers)} destination "
                        "accounts are present in the supplied "
                        "transaction history and can be "
                        "reviewed as downstream pivots.",
                    )
                )

    return findings


# ============================================================
# 2. CHANGED SIM / DEVICE
# ============================================================

def detect_changed_sim_device(data):

    findings = []

    devices = data["devices"]

    if devices.empty:

        return [
            finding(
                "CHANGED_SIM_DEVICE",
                "EVIDENCE_GAP",
                "No device records are available."
            )
        ]

    imei_phones = defaultdict(set)

    phone_imeis = defaultdict(set)

    for _, row in devices.iterrows():

        phone = clean(
            row.get("phone_number")
        )

        imei = clean(
            row.get("imei")
        )

        if phone and imei:

            imei_phones[imei].add(
                phone
            )

            phone_imeis[phone].add(
                imei
            )

    shared_imeis = {
        imei: sorted(phones)
        for imei, phones
        in imei_phones.items()
        if len(phones) > 1
    }

    changed_devices = {
        phone: sorted(imeis)
        for phone, imeis
        in phone_imeis.items()
        if len(imeis) > 1
    }

    if shared_imeis:

        findings.append(
            finding(
                "CHANGED_SIM_DEVICE",
                "DERIVED",
                f"{len(shared_imeis)} IMEIs are associated "
                "with more than one phone number. These "
                "relationships should be correlated with "
                "timestamps and transaction activity.",
            )
        )

    if changed_devices:

        findings.append(
            finding(
                "CHANGED_DEVICE",
                "DERIVED",
                f"{len(changed_devices)} phone numbers are "
                "associated with multiple IMEIs. This is a "
                "device-transition signal, not proof of a "
                "shared actor.",
            )
        )

    return findings


# ============================================================
# 3. INNOCENT / LEGITIMATE MULE POSSIBILITY
# ============================================================

def detect_legitimate_account_risk(data):

    findings = []

    upi = data["upi"]

    if upi.empty:

        return findings

    if "receiver_account" not in upi.columns:

        return [
            finding(
                "LEGITIMATE_ACCOUNT",
                "EVIDENCE_GAP",
                "Receiver-account information is unavailable."
            )
        ]

    receiver_counts = (
        upi[
            "receiver_account"
        ]
        .replace("", pd.NA)
        .dropna()
        .value_counts()
    )

    if len(receiver_counts) == 0:
        return findings

    top_receivers = receiver_counts.head(10)

    findings.append(
        finding(
            "LEGITIMATE_ACCOUNT",
            "INVESTIGATIVE_SAFEGUARD",
            "Recipient accounts should be evaluated at the "
            "transaction level. A recipient account should "
            "not automatically be treated as a fraudulent "
            "person or organization.",
        )
    )

    findings.append(
        finding(
            "RECIPIENT_REVIEW",
            "DERIVED",
            f"{len(top_receivers)} frequently observed "
            "recipient accounts are available for "
            "transaction-level review.",
        )
    )

    return findings


# ============================================================
# 4. SHARED DEVICE
# ============================================================

def detect_shared_devices(data):

    findings = []

    devices = data["devices"]

    if devices.empty:
        return findings

    grouped = defaultdict(list)

    for _, row in devices.iterrows():

        imei = clean(
            row.get("imei")
        )

        phone = clean(
            row.get("phone_number")
        )

        if imei and phone:

            grouped[imei].append(
                phone
            )

    shared = {
        imei: unique(phones)
        for imei, phones
        in grouped.items()
        if len(unique(phones)) > 1
    }

    if shared:

        findings.append(
            finding(
                "SHARED_DEVICE",
                "DERIVED",
                f"{len(shared)} device identifiers are "
                "associated with multiple phone numbers. "
                "Timestamp correlation is required before "
                "drawing conclusions.",
            )
        )

    return findings


# ============================================================
# 5. SHARED TOWER
# ============================================================

def detect_shared_towers(data):

    findings = []

    cdr = data["cdr"]

    devices = data["devices"]

    records = []

    if "tower_id" in cdr.columns:

        for _, row in cdr.iterrows():

            tower = clean(
                row.get("tower_id")
            )

            phone = clean(
                row.get("caller")
            )

            if tower and phone:

                records.append(
                    (tower, phone)
                )

    if "tower_id" in devices.columns:

        for _, row in devices.iterrows():

            tower = clean(
                row.get("tower_id")
            )

            phone = clean(
                row.get("phone_number")
            )

            if tower and phone:

                records.append(
                    (tower, phone)
                )

    tower_phones = defaultdict(set)

    for tower, phone in records:

        tower_phones[tower].add(
            phone
        )

    shared = {
        tower: sorted(phones)
        for tower, phones
        in tower_phones.items()
        if len(phones) > 1
    }

    if shared:

        findings.append(
            finding(
                "SHARED_TOWER",
                "DERIVED",
                f"{len(shared)} tower identifiers "
                "involve multiple phone numbers. A shared "
                "tower is supporting context only and does "
                "not independently establish a relationship.",
            )
        )

    return findings


# ============================================================
# 6. MISSING DATA
# ============================================================

def detect_missing_data(data):

    findings = []

    required_fields = {
        "cdr": [
            "timestamp",
            "caller",
            "called",
            "imei",
            "tower_id",
        ],

        "upi": [
            "timestamp",
            "sender_account",
            "receiver_account",
            "amount_inr",
        ],

        "complaints": [
            "complaint_timestamp",
            "victim_phone",
            "victim_account",
        ],

        "devices": [
            "phone_number",
            "imei",
            "first_seen",
            "last_seen",
            "tower_id",
        ],
    }

    for name, fields in required_fields.items():

        df = data[name]

        if df.empty:

            findings.append(
                finding(
                    "MISSING_DATA",
                    "EVIDENCE_GAP",
                    f"{name.upper()} evidence is empty."
                )
            )

            continue

        for field in fields:

            if field not in df.columns:

                findings.append(
                    finding(
                        "MISSING_DATA",
                        "EVIDENCE_GAP",
                        f"{name.upper()} is missing the "
                        f"expected field '{field}'."
                    )
                )

                continue

            missing_count = (
                df[field]
                .astype(str)
                .str.strip()
                .eq("")
                .sum()
            )

            if missing_count:

                findings.append(
                    finding(
                        "MISSING_DATA",
                        "EVIDENCE_GAP",
                        f"{name.upper()}.{field} has "
                        f"{missing_count} missing values."
                    )
                )

    if findings:

        findings.append(
            finding(
                "MISSING_DATA",
                "INVESTIGATIVE_SAFEGUARD",
                "Missing values are surfaced as evidence "
                "gaps. The system does not invent missing "
                "facts."
            )
        )

    return findings


# ============================================================
# 7. FALSE TRAIL / MULTI-HOP
# ============================================================

def detect_transaction_patterns(data):

    findings = []

    upi = data["upi"]

    required = {
        "sender_account",
        "receiver_account",
    }

    if not required.issubset(
        set(upi.columns)
    ):

        return findings

    graph = defaultdict(set)

    for _, row in upi.iterrows():

        sender = clean(
            row.get("sender_account")
        )

        receiver = clean(
            row.get("receiver_account")
        )

        if sender and receiver:

            graph[sender].add(
                receiver
            )

    fan_out = {
        account: receivers
        for account, receivers
        in graph.items()
        if len(receivers) >= 3
    }

    if fan_out:

        findings.append(
            finding(
                "FAN_OUT",
                "DERIVED",
                f"{len(fan_out)} accounts send funds "
                "to three or more distinct destination "
                "accounts. These structures can be reviewed "
                "for possible layering or distribution."
            )
        )

    receiver_sources = defaultdict(set)

    for sender, receivers in graph.items():

        for receiver in receivers:

            receiver_sources[receiver].add(
                sender
            )

    fan_in = {
        account: senders
        for account, senders
        in receiver_sources.items()
        if len(senders) >= 3
    }

    if fan_in:

        findings.append(
            finding(
                "FAN_IN",
                "DERIVED",
                f"{len(fan_in)} accounts receive funds "
                "from three or more distinct senders. "
                "These are candidates for transaction-level "
                "review."
            )
        )

    if fan_in and fan_out:

        findings.append(
            finding(
                "MULTI_HOP",
                "ANALYTICAL INFERENCE",
                "The transaction graph contains both "
                "fan-in and fan-out structures. This can "
                "support review for layered transaction "
                "paths, but does not independently establish "
                "fraud."
            )
        )

    return findings


# ============================================================
# 8. GRAPH EXPLOSION
# ============================================================

def detect_graph_explosion(data):

    findings = []

    nodes = set()
    edges = 0

    cdr = data["cdr"]

    upi = data["upi"]

    for _, row in cdr.iterrows():

        for field in [
            "caller",
            "called",
            "imei",
            "tower_id",
        ]:

            value = clean(
                row.get(field)
            )

            if value:
                nodes.add(value)

        edges += 1

    for _, row in upi.iterrows():

        for field in [
            "sender_account",
            "receiver_account",
        ]:

            value = clean(
                row.get(field)
            )

            if value:
                nodes.add(value)

        edges += 1

    if len(nodes) > 1000 or edges > 5000:

        findings.append(
            finding(
                "GRAPH_EXPLOSION",
                "DERIVED",
                f"The current evidence produces approximately "
                f"{len(nodes)} raw identifiers and {edges} "
                "relationship records. Focused 1-hop, 2-hop "
                "and 3-hop investigation views are recommended.",
                severity="WARNING",
            )
        )

    return findings


# ============================================================
# 9. MULTIPLE PATTERNS
# ============================================================

def detect_multiple_patterns(data):

    findings = []

    pattern_names = []

    cdr = data["cdr"]

    devices = data["devices"]

    upi = data["upi"]

    # Shared device

    if not devices.empty:

        grouped = (
            devices.groupby(
                "imei"
            )["phone_number"]
            .nunique()
        )

        if (
            grouped.gt(1).any()
        ):

            pattern_names.append(
                "SHARED_DEVICE"
            )

    # Multiple recipients

    if (
        not upi.empty
        and "receiver_account"
        in upi.columns
    ):

        receiver_count = (
            upi["receiver_account"]
            .replace("", pd.NA)
            .dropna()
            .nunique()
        )

        if receiver_count >= 3:

            pattern_names.append(
                "MULTI_RECIPIENT"
            )

    # Communication

    if (
        not cdr.empty
        and "caller" in cdr.columns
        and "called" in cdr.columns
    ):

        if len(cdr) >= 2:

            pattern_names.append(
                "COMMUNICATION_NETWORK"
            )

    if len(pattern_names) > 1:

        findings.append(
            finding(
                "MULTIPLE_FRAUD_PATTERNS",
                "ANALYTICAL INFERENCE",
                "Multiple structural patterns are present: "
                + ", ".join(pattern_names)
                + ". The application should display them "
                  "together rather than forcing a single "
                  "pattern classification."
            )
        )

    return findings


# ============================================================
# 10. CONFLICTING INFORMATION
# ============================================================

def detect_conflicts(data):

    findings = []

    devices = data["devices"]

    if devices.empty:
        return findings

    # Same phone -> multiple IMEIs

    if {
        "phone_number",
        "imei",
    }.issubset(
        set(devices.columns)
    ):

        grouped = (
            devices
            .groupby("phone_number")["imei"]
            .apply(
                lambda x:
                sorted(
                    unique(
                        x.tolist()
                    )
                )
            )
        )

        conflicts = grouped[
            grouped.apply(
                lambda x:
                len(x) > 1
            )
        ]

        if not conflicts.empty:

            findings.append(
                finding(
                    "CONFLICTING_INFORMATION",
                    "CONFLICT DETECTED",
                    f"{len(conflicts)} phone numbers "
                    "have multiple IMEI associations. "
                    "Review the underlying timestamps and "
                    "source records before interpretation."
                )
            )

    # Same phone -> multiple towers

    if {
        "phone_number",
        "tower_id",
    }.issubset(
        set(devices.columns)
    ):

        grouped = (
            devices
            .groupby("phone_number")["tower_id"]
            .apply(
                lambda x:
                sorted(
                    unique(
                        x.tolist()
                    )
                )
            )
        )

        conflicts = grouped[
            grouped.apply(
                lambda x:
                len(x) > 1
            )
        ]

        if not conflicts.empty:

            findings.append(
                finding(
                    "CONFLICTING_INFORMATION",
                    "CONTEXTUAL_VARIATION",
                    f"{len(conflicts)} phone numbers "
                    "have multiple tower associations. "
                    "This may represent movement rather than "
                    "a contradiction and requires timestamp review."
                )
            )

    return findings


# ============================================================
# 11. ACCOUNT EMPTIED / CASH-OUT
# ============================================================

def detect_emptied_accounts(data):

    findings = []

    upi = data["upi"]

    required = {
        "sender_account",
        "receiver_account",
        "amount_inr",
    }

    if not required.issubset(
        set(upi.columns)
    ):

        return [
            finding(
                "ACCOUNT_EMPTIED",
                "EVIDENCE_GAP",
                "The supplied UPI fields do not contain "
                "enough information to reconstruct account "
                "balances."
            )
        ]

    received = defaultdict(float)

    sent = defaultdict(float)

    for _, row in upi.iterrows():

        sender = clean(
            row.get("sender_account")
        )

        receiver = clean(
            row.get("receiver_account")
        )

        try:

            amount = float(
                row.get(
                    "amount_inr",
                    0
                )
            )

        except Exception:

            amount = 0

        if sender:
            sent[sender] += amount

        if receiver:
            received[receiver] += amount

    candidates = []

    for account in set(
        list(received.keys())
        + list(sent.keys())
    ):

        incoming = received.get(
            account,
            0
        )

        outgoing = sent.get(
            account,
            0
        )

        if (
            incoming > 0
            and outgoing >= incoming * 0.8
        ):

            candidates.append(
                account
            )

    if candidates:

        findings.append(
            finding(
                "ACCOUNT_EMPTIED",
                "ANALYTICAL INFERENCE",
                f"{len(candidates)} accounts show outgoing "
                "transaction value approaching or exceeding "
                "their observed incoming value. This is a "
                "transaction-flow signal, not proof of cash-out "
                "or wrongdoing."
            )
        )

    findings.append(
        finding(
            "ACCOUNT_BALANCE_GAP",
            "EVIDENCE_GAP",
            "Actual bank balances and cash withdrawals cannot "
            "be established from transaction records alone "
            "unless balance or cash-out records are supplied."
        )
    )

    return findings


# ============================================================
# 12. AI / LLM HALLUCINATION GUARDRAIL
# ============================================================

def build_llm_guardrails():

    return {
        "enabled": True,

        "rules": [
            "AI output must be grounded in supplied evidence.",
            "AI must not invent missing records.",
            "Every factual finding should reference evidence.",
            "Analytical inference must be labelled as inference.",
            "Shared devices do not independently establish identity.",
            "Shared towers do not independently establish identity.",
            "A recipient account must not automatically be labelled criminal.",
            "The system must not make automated guilt determinations.",
            "Human investigators remain responsible for attribution."
        ],

        "allowed_language": [
            "warrants review",
            "associated with",
            "observed",
            "derived",
            "analytical inference",
            "potential coordination node",
            "high-connectivity node",
            "transaction-level review"
        ],

        "avoid_language": [
            "mastermind",
            "criminal",
            "guilty",
            "confirmed fraudster",
            "criminal organization"
        ]
    }


# ============================================================
# MAIN ANALYSIS
# ============================================================

def build_report():

    active = load_active_case()

    case_id = (
        active.get("case_id")
        or active.get("active_case_id")
    )

    data = load_data(
        active
    )

    findings = []

    detectors = [
        detect_burned_sim_and_closed_account,
        detect_changed_sim_device,
        detect_legitimate_account_risk,
        detect_shared_devices,
        detect_shared_towers,
        detect_missing_data,
        detect_transaction_patterns,
        detect_graph_explosion,
        detect_multiple_patterns,
        detect_conflicts,
        detect_emptied_accounts,
    ]

    for detector in detectors:

        try:

            result = detector(
                data
            )

            if result:
                findings.extend(
                    result
                )

        except Exception as exc:

            findings.append(
                finding(
                    "ANALYSIS_ERROR",
                    "EVIDENCE_GAP",
                    f"{detector.__name__} could not "
                    f"complete: {exc}",
                    severity="WARNING"
                )
            )

    report = {

        "case_id": case_id,

        "module":
            "Edge Case Intelligence",

        "generated_from":
            "Current active case canonical evidence",

        "findings":
            findings,

        "finding_count":
            len(findings),

        "llm_guardrails":
            build_llm_guardrails(),

        "limitations": [
            "Edge-case signals are investigative aids.",
            "Missing data is not replaced by AI-generated facts.",
            "Shared infrastructure does not independently establish identity.",
            "Final attribution requires human investigation and supporting evidence."
        ]
    }

    return report


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 78)
    print(
        "CHANAKYA-GRAPH — EDGE CASE INTELLIGENCE"
    )
    print("=" * 78)

    report = build_report()

    save_json(
        OUTPUT_FILE,
        report
    )

    print(
        f"Case ID       : {report['case_id']}"
    )

    print(
        f"Findings      : {report['finding_count']}"
    )

    print(
        f"Output        : {OUTPUT_FILE}"
    )

    print("=" * 78)


if __name__ == "__main__":
    main()