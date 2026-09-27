import sys
from pathlib import Path

import streamlit as st
import pandas as pd


SRC_DIR = Path(__file__).resolve().parents[2]

if str(SRC_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(SRC_DIR)
    )


from investigation.evidence_explorer import (
    build_evidence_ledger,
    evidence_summary,
    search_evidence,
    filter_evidence,
    get_evidence_by_id,
)


st.set_page_config(
    page_title="Chanakya-Graph | Evidence Explorer",
    page_icon="🔎",
    layout="wide",
)


st.title(
    "🔎 Evidence Explorer"
)

st.caption(
    "Evidence-linked investigation and provenance explorer"
)


# ============================================================
# LOAD EVIDENCE
# ============================================================

ledger = build_evidence_ledger()

summary = evidence_summary(
    ledger
)


# ============================================================
# SUMMARY
# ============================================================

st.subheader(
    "Evidence Overview"
)

c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.metric(
        "Total Evidence",
        summary["total"]
    )

with c2:
    st.metric(
        "CDR",
        summary["CDR"]
    )

with c3:
    st.metric(
        "UPI",
        summary["UPI"]
    )

with c4:
    st.metric(
        "Complaints",
        summary["COMPLAINT"]
    )

with c5:
    st.metric(
        "Devices",
        summary["DEVICE"]
    )


st.divider()


# ============================================================
# SEARCH / FILTER
# ============================================================

st.subheader(
    "Search Evidence"
)

col1, col2, col3 = st.columns(
    [2, 1, 1]
)

with col1:

    search_query = st.text_input(
        "Search",
        placeholder=(
            "Evidence ID, phone, account, IMEI, "
            "tower, transaction ID..."
        )
    )

with col2:

    evidence_type = st.selectbox(
        "Evidence Type",
        [
            "ALL",
            "CDR",
            "UPI",
            "COMPLAINT",
            "DEVICE",
        ]
    )

with col3:

    evidence_status = st.selectbox(
        "Status",
        [
            "ALL",
            "OBSERVED",
        ]
    )


results = ledger

if evidence_type != "ALL":

    results = filter_evidence(
        results,
        evidence_type=evidence_type
    )


if evidence_status != "ALL":

    results = filter_evidence(
        results,
        status=evidence_status
    )


if search_query:

    results = search_evidence(
        results,
        search_query
    )


st.write(
    f"Showing **{len(results)}** evidence record(s)"
)


# ============================================================
# EVIDENCE TABLE
# ============================================================

if results:

    table_data = []

    for evidence in results[:500]:

        table_data.append({
            "Evidence ID":
                evidence.get(
                    "evidence_id",
                    ""
                ),

            "Type":
                evidence.get(
                    "evidence_type",
                    ""
                ),

            "Timestamp":
                evidence.get(
                    "timestamp",
                    ""
                ),

            "Status":
                evidence.get(
                    "evidence_status",
                    ""
                ),

            "Amount":
                evidence.get(
                    "amount_inr",
                    ""
                ),

            "Source":
                evidence.get(
                    "data_source",
                    ""
                ),
        })

    df = pd.DataFrame(
        table_data
    )

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

else:

    st.info(
        "No evidence records matched the current filters."
    )


# ============================================================
# EVIDENCE DETAILS
# ============================================================

st.divider()

st.subheader(
    "Evidence Details"
)

if results:

    evidence_ids = [
        item.get(
            "evidence_id",
            ""
        )
        for item in results
        if item.get(
            "evidence_id"
        )
    ]

    selected_id = st.selectbox(
        "Select Evidence ID",
        evidence_ids
    )

    selected = get_evidence_by_id(
        ledger,
        selected_id
    )

    if selected:

        c1, c2, c3 = st.columns(3)

        with c1:

            st.markdown(
                "**Evidence ID**"
            )

            st.code(
                selected.get(
                    "evidence_id",
                    ""
                )
            )

        with c2:

            st.markdown(
                "**Evidence Type**"
            )

            st.write(
                selected.get(
                    "evidence_type",
                    ""
                )
            )

        with c3:

            st.markdown(
                "**Evidence Status**"
            )

            st.write(
                selected.get(
                    "evidence_status",
                    ""
                )
            )


        st.markdown(
            "**Timestamp**"
        )

        st.write(
            selected.get(
                "timestamp",
                ""
            )
        )


        amount = selected.get(
            "amount_inr",
            ""
        )

        if amount:

            st.markdown(
                "**Transaction Amount**"
            )

            st.write(
                f"INR {amount}"
            )


        st.markdown(
            "**Data Source**"
        )

        st.write(
            selected.get(
                "data_source",
                "UNKNOWN"
            )
        )


        st.markdown(
            "### Original Evidence Record"
        )

        record = selected.get(
            "record",
            {}
        )

        record_df = pd.DataFrame(
            [
                {
                    "Field": key,
                    "Value": value,
                }
                for key, value
                in record.items()
            ]
        )

        st.dataframe(
            record_df,
            use_container_width=True,
            hide_index=True
        )


        # ====================================================
        # PROVENANCE
        # ====================================================

        st.markdown(
            "### Evidence Provenance"
        )

        st.info(
            "This record is classified as OBSERVED because "
            "it originates directly from the processed "
            "case evidence. Analytical conclusions should "
            "not be treated as raw evidence."
        )


else:

    st.info(
        "Search for an evidence record to inspect "
        "its provenance."
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Chanakya-Graph | Evidence Explorer | "
    "Evidence is presented with provenance and "
    "does not by itself establish wrongdoing."
)