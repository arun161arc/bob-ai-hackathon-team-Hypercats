from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from investigation.command_center import (
    build_command_center,
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Chanakya-Graph | Command Center",
    page_icon="🔎",
    layout="wide",
)


# ============================================================
# STYLE
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 34px;
        font-weight: 700;
        margin-bottom: 0px;
    }

    .sub-title {
        color: #7d8590;
        font-size: 15px;
        margin-bottom: 25px;
    }

    .case-banner {
        padding: 18px;
        border-radius: 12px;
        border: 1px solid #30363d;
        background: #161b22;
        margin-bottom: 20px;
    }

    .case-id {
        font-size: 22px;
        font-weight: 700;
    }

    .status {
        display: inline-block;
        padding: 5px 12px;
        border-radius: 20px;
        background: #238636;
        color: white;
        font-size: 13px;
        font-weight: 600;
        margin-left: 10px;
    }

    .finding {
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #30363d;
        margin-bottom: 10px;
        background: #161b22;
    }

    .finding-type {
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.8px;
        margin-bottom: 5px;
    }

    .finding-title {
        font-size: 16px;
        font-weight: 650;
        margin-bottom: 5px;
    }

    .finding-description {
        color: #9da7b3;
        font-size: 14px;
    }

    .section-title {
        font-size: 21px;
        font-weight: 700;
        margin-top: 20px;
        margin-bottom: 12px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">🔎 Chanakya-Graph</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="sub-title">'
    'Cyber-Fraud Investigation Command Center'
    '</div>',
    unsafe_allow_html=True,
)


# ============================================================
# LOAD COMMAND CENTER
# ============================================================

try:

    result = build_command_center()

except Exception as error:

    st.error(
        "Unable to build the Investigation Command Center."
    )

    st.exception(error)

    st.stop()


# ============================================================
# NO ACTIVE CASE
# ============================================================

if result.get("status") != "ACTIVE":

    st.warning(
        result.get(
            "message",
            "No active investigation case found."
        )
    )

    st.info(
        "Run Phase 8 Case Intake first."
    )

    st.stop()


# ============================================================
# CASE BANNER
# ============================================================

case = result["case"]

st.markdown(
    f"""
    <div class="case-banner">
        <div class="case-id">
            {case["case_id"]}
            <span class="status">ACTIVE</span>
        </div>
        <div style="margin-top:7px;color:#8b949e;">
            {case["title"]}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# TOP METRICS
# ============================================================

evidence = result["evidence"]
entities = result["entities"]
transactions = result["transactions"]


st.markdown(
    '<div class="section-title">Investigation Overview</div>',
    unsafe_allow_html=True,
)


row1 = st.columns(4)

with row1[0]:
    st.metric(
        "Evidence Records",
        f"{evidence['total_records']:,}",
    )

with row1[1]:
    st.metric(
        "Entities",
        f"{sum(entities.values()):,}",
    )

with row1[2]:
    st.metric(
        "Connections",
        f"{result['connections']['total']:,}",
    )

with row1[3]:
    st.metric(
        "Transactions",
        f"{transactions['transaction_count']:,}",
    )


# ============================================================
# EVIDENCE
# ============================================================

st.markdown(
    '<div class="section-title">Evidence Inventory</div>',
    unsafe_allow_html=True,
)

evidence_columns = st.columns(4)

evidence_items = [
    ("CDR", evidence["cdr"]["records"]),
    ("UPI Transactions", evidence["upi"]["records"]),
    ("Complaints", evidence["complaints"]["records"]),
    ("Device / IMEI", evidence["devices"]["records"]),
]

for column, (label, count) in zip(
    evidence_columns,
    evidence_items,
):

    with column:

        st.metric(
            label,
            f"{count:,}",
        )


# ============================================================
# ENTITY INVENTORY
# ============================================================

st.markdown(
    '<div class="section-title">Entity Inventory</div>',
    unsafe_allow_html=True,
)

entity_columns = st.columns(6)

entity_items = [
    ("Phones", entities["phones"]),
    ("Accounts", entities["accounts"]),
    ("IMEIs", entities["imeis"]),
    ("Towers", entities["towers"]),
    ("Persons", entities["persons"]),
    ("Transactions", entities["transactions"]),
]

for column, (label, count) in zip(
    entity_columns,
    entity_items,
):

    with column:

        st.metric(
            label,
            f"{count:,}",
        )


# ============================================================
# FINANCIAL INTELLIGENCE
# ============================================================

st.markdown(
    '<div class="section-title">Financial Intelligence</div>',
    unsafe_allow_html=True,
)

finance_columns = st.columns(4)

with finance_columns[0]:

    st.metric(
        "Total Transaction Value",
        f"INR {transactions['total_amount_inr']:,.2f}",
    )

with finance_columns[1]:

    st.metric(
        "Average Transaction",
        f"INR {transactions['average_amount_inr']:,.2f}",
    )

with finance_columns[2]:

    st.metric(
        "Unique Senders",
        transactions["unique_senders"],
    )

with finance_columns[3]:

    st.metric(
        "Unique Receivers",
        transactions["unique_receivers"],
    )


# ============================================================
# LARGEST TRANSACTION
# ============================================================

maximum = transactions.get(
    "maximum_transaction"
)

if maximum:

    st.markdown(
        '<div class="section-title">'
        'Largest Transaction'
        '</div>',
        unsafe_allow_html=True,
    )

    largest_columns = st.columns(4)

    with largest_columns[0]:
        st.metric(
            "Amount",
            f"INR {maximum['amount_inr']:,.2f}",
        )

    with largest_columns[1]:
        st.write("**Transaction ID**")
        st.code(
            maximum["transaction_id"]
        )

    with largest_columns[2]:
        st.write("**Sender**")
        st.code(
            maximum["sender"]
        )

    with largest_columns[3]:
        st.write("**Receiver**")
        st.code(
            maximum["receiver"]
        )


# ============================================================
# MONEY FLOW
# ============================================================

st.markdown(
    '<div class="section-title">Money Flow</div>',
    unsafe_allow_html=True,
)

money_flow = result["money_flow"]

if money_flow:

    display_rows = []

    for item in money_flow[:100]:

        display_rows.append({
            "Timestamp": item["timestamp"],
            "Transaction": item["transaction_id"],
            "Sender": item["sender"],
            "Receiver": item["receiver"],
            "Amount (INR)": item["amount_inr"],
            "Sender Type": item["sender_type"],
            "Receiver Type": item["receiver_type"],
        })

    st.dataframe(
        display_rows,
        use_container_width=True,
        hide_index=True,
    )

    if len(money_flow) > 100:

        st.caption(
            f"Showing first 100 of "
            f"{len(money_flow):,} transactions."
        )

else:

    st.info(
        "No transaction flow is currently available."
    )


# ============================================================
# INFRASTRUCTURE CORRELATION
# ============================================================

st.markdown(
    '<div class="section-title">'
    'Infrastructure Correlation'
    '</div>',
    unsafe_allow_html=True,
)

infra_columns = st.columns(2)

shared_devices = result["shared_devices"]
shared_towers = result["shared_towers"]


with infra_columns[0]:

    st.write("### 📱 Shared Devices")

    if shared_devices:

        for item in shared_devices:

            st.warning(
                f"IMEI `{item['imei']}` is associated with "
                f"{item['phone_count']} phone numbers."
            )

            st.write(
                ", ".join(
                    item["phone_numbers"]
                )
            )

    else:

        st.success(
            "No shared-device correlation identified "
            "in the currently processed evidence."
        )


with infra_columns[1]:

    st.write("### 📡 Shared Towers")

    if shared_towers:

        for item in shared_towers:

            st.warning(
                f"Tower `{item['tower_id']}` has observations "
                f"for {item['phone_count']} phone numbers."
            )

            st.write(
                ", ".join(
                    item["phone_numbers"]
                )
            )

    else:

        st.success(
            "No multi-phone tower correlation identified "
            "in the currently processed evidence."
        )


# ============================================================
# FINDINGS
# ============================================================

st.markdown(
    '<div class="section-title">'
    'Investigation Findings'
    '</div>',
    unsafe_allow_html=True,
)


for finding in result["findings"]:

    finding_type = finding["type"]

    if finding_type == "OBSERVED":
        icon = "🔵"

    elif finding_type == "DERIVED":
        icon = "🟡"

    else:
        icon = "🟣"

    evidence_text = ", ".join(
        finding.get(
            "evidence",
            []
        )
    )

    st.markdown(
        f"""
        <div class="finding">
            <div class="finding-type">
                {icon} {finding_type}
            </div>

            <div class="finding-title">
                {finding["title"]}
            </div>

            <div class="finding-description">
                {finding["description"]}
            </div>

            <div style="
                margin-top:8px;
                color:#6e7681;
                font-size:12px;
            ">
                Evidence: {evidence_text}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# QUICK INVESTIGATION ACTIONS
# ============================================================

st.markdown(
    '<div class="section-title">'
    'Quick Investigation Actions'
    '</div>',
    unsafe_allow_html=True,
)

actions = result["investigation_actions"]

action_columns = st.columns(4)

for index, action in enumerate(actions):

    column = action_columns[
        index % 4
    ]

    with column:

        if st.button(
            action["label"],
            key=f"phase9_{action['id']}",
            use_container_width=True,
        ):

            st.info(
                f"Open: {action['target']}"
            )


# ============================================================
# INVESTIGATION WORKFLOW
# ============================================================

st.markdown(
    '<div class="section-title">'
    'Investigation Workflow'
    '</div>',
    unsafe_allow_html=True,
)

workflow = [
    "1. CASE INTAKE",
    "2. EVIDENCE PROCESSING",
    "3. ENTITY RECONSTRUCTION",
    "4. GRAPH ANALYSIS",
    "5. FINANCIAL ANALYSIS",
    "6. INFRASTRUCTURE CORRELATION",
    "7. EDGE-CASE REVIEW",
    "8. EVIDENCE EXPLANATION",
    "9. CASE BRIEF",
]

st.progress(
    9 / 9,
    text="Investigation pipeline initialized",
)

st.write(
    " → ".join(workflow)
)


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Chanakya-Graph | Phase 9 Investigation Command Center | "
    "AI-assisted investigation using evidence-linked analysis"
)

st.caption(
    "Analytical findings are investigative leads and should "
    "be validated against source evidence."
)