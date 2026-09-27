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


from investigation.timeline import (
    build_timeline,
    timeline_summary,
    search_timeline,
    filter_timeline,
    financial_timeline,
)


st.set_page_config(
    page_title="Chanakya-Graph | Timeline",
    page_icon="🕒",
    layout="wide",
)


st.title(
    "🕒 Investigation Timeline"
)

st.caption(
    "Chronological reconstruction of calls, "
    "transactions, complaints and device observations"
)


# ============================================================
# LOAD
# ============================================================

timeline = build_timeline()

summary = timeline_summary(
    timeline
)


# ============================================================
# SUMMARY
# ============================================================

st.subheader(
    "Timeline Overview"
)

c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.metric(
        "Total Events",
        summary["total_events"]
    )

with c2:
    st.metric(
        "Calls",
        summary["calls"]
    )

with c3:
    st.metric(
        "Transactions",
        summary["transactions"]
    )

with c4:
    st.metric(
        "Complaints",
        summary["complaints"]
    )

with c5:
    st.metric(
        "Device Events",
        summary["device_observations"]
    )


st.divider()


# ============================================================
# CASE PERIOD
# ============================================================

c1, c2, c3 = st.columns(3)

with c1:

    st.markdown(
        "**First Observed Event**"
    )

    st.write(
        summary["first_event"]
        or "Not available"
    )

with c2:

    st.markdown(
        "**Last Observed Event**"
    )

    st.write(
        summary["last_event"]
        or "Not available"
    )

with c3:

    st.markdown(
        "**Total Transaction Value**"
    )

    st.write(
        f"INR {summary['total_transaction_amount']:,.2f}"
    )


st.divider()


# ============================================================
# FILTERS
# ============================================================

st.subheader(
    "Timeline Filters"
)

col1, col2 = st.columns(
    [2, 1]
)

with col1:

    query = st.text_input(
        "Search Timeline",
        placeholder=(
            "Phone, account, IMEI, "
            "transaction ID, Evidence ID..."
        )
    )

with col2:

    event_type = st.selectbox(
        "Event Type",
        [
            "ALL",
            "CALL",
            "TRANSACTION",
            "COMPLAINT",
            "DEVICE_OBSERVATION",
        ]
    )


filtered = filter_timeline(
    timeline,
    event_type
)

if query:

    filtered = search_timeline(
        filtered,
        query
    )


st.write(
    f"Showing **{len(filtered)}** event(s)"
)


# ============================================================
# TIMELINE TABLE
# ============================================================

if filtered:

    rows = []

    for event in filtered:

        amount = event.get(
            "amount_inr",
            ""
        )

        try:

            if amount != "":
                amount = f"INR {float(amount):,.2f}"

        except (
            TypeError,
            ValueError
        ):
            pass

        rows.append({

            "Timestamp":
                event.get(
                    "timestamp",
                    ""
                ),

            "Type":
                event.get(
                    "event_type",
                    ""
                ),

            "Evidence ID":
                event.get(
                    "evidence_id",
                    ""
                ),

            "Actor":
                event.get(
                    "actor",
                    ""
                ),

            "Target":
                event.get(
                    "target",
                    ""
                ),

            "Amount":
                amount,

            "Description":
                event.get(
                    "description",
                    ""
                ),

            "Status":
                event.get(
                    "evidence_status",
                    ""
                ),
        })

    timeline_df = pd.DataFrame(
        rows
    )

    st.dataframe(
        timeline_df,
        use_container_width=True,
        hide_index=True
    )

else:

    st.info(
        "No timeline events match the selected filters."
    )


# ============================================================
# EVENT DETAILS
# ============================================================

st.divider()

st.subheader(
    "Event Details"
)

if filtered:

    event_ids = [
        event.get(
            "event_id",
            ""
        )
        for event in filtered
    ]

    selected_event_id = st.selectbox(
        "Select Event",
        event_ids
    )

    selected_event = next(
        (
            event
            for event in filtered
            if event.get(
                "event_id"
            ) == selected_event_id
        ),
        None
    )

    if selected_event:

        c1, c2, c3, c4 = st.columns(4)

        with c1:

            st.markdown(
                "**Event Type**"
            )

            st.write(
                selected_event.get(
                    "event_type",
                    ""
                )
            )

        with c2:

            st.markdown(
                "**Evidence ID**"
            )

            st.code(
                selected_event.get(
                    "evidence_id",
                    ""
                )
            )

        with c3:

            st.markdown(
                "**Timestamp**"
            )

            st.write(
                selected_event.get(
                    "timestamp",
                    ""
                )
            )

        with c4:

            st.markdown(
                "**Status**"
            )

            st.write(
                selected_event.get(
                    "evidence_status",
                    ""
                )
            )


        st.markdown(
            "### Event Description"
        )

        st.info(
            selected_event.get(
                "description",
                ""
            )
        )


        st.markdown(
            "### Event Details"
        )

        details = selected_event.get(
            "details",
            {}
        )

        detail_df = pd.DataFrame([
            {
                "Field": key,
                "Value": value,
            }
            for key, value
            in details.items()
        ])

        st.dataframe(
            detail_df,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# FINANCIAL TIMELINE
# ============================================================

st.divider()

st.subheader(
    "💰 Financial Timeline"
)

financial = financial_timeline(
    timeline
)

if financial:

    financial_df = pd.DataFrame(
        financial
    )

    financial_df = financial_df.rename(
        columns={
            "timestamp": "Timestamp",
            "transaction_id": "Transaction ID",
            "sender": "Sender",
            "receiver": "Receiver",
            "amount_inr": "Amount (INR)",
            "cumulative_amount_inr":
                "Cumulative Amount (INR)",
            "evidence_id": "Evidence ID",
        }
    )

    st.dataframe(
        financial_df,
        use_container_width=True,
        hide_index=True
    )

else:

    st.info(
        "No financial transactions found."
    )


# ============================================================
# EXPORT
# ============================================================

st.divider()

st.subheader(
    "Export Timeline"
)

if filtered:

    export_rows = []

    for event in filtered:

        export_rows.append({
            "timestamp":
                event.get(
                    "timestamp",
                    ""
                ),

            "event_type":
                event.get(
                    "event_type",
                    ""
                ),

            "evidence_type":
                event.get(
                    "evidence_type",
                    ""
                ),

            "evidence_id":
                event.get(
                    "evidence_id",
                    ""
                ),

            "actor":
                event.get(
                    "actor",
                    ""
                ),

            "target":
                event.get(
                    "target",
                    ""
                ),

            "amount_inr":
                event.get(
                    "amount_inr",
                    ""
                ),

            "description":
                event.get(
                    "description",
                    ""
                ),

            "evidence_status":
                event.get(
                    "evidence_status",
                    ""
                ),
        })

    export_df = pd.DataFrame(
        export_rows
    )

    csv_data = export_df.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        "⬇️ Download Timeline CSV",
        data=csv_data,
        file_name=(
            "chanakya_investigation_timeline.csv"
        ),
        mime="text/csv",
    )


st.divider()

st.caption(
    "Chanakya-Graph | Investigation Timeline | "
    "Timeline events are evidence records and "
    "should be interpreted with their provenance."
)