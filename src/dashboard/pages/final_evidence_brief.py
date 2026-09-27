import json
import sys
from pathlib import Path

import streamlit as st


# ============================================================
# PATH
# ============================================================

SRC_DIR = Path(__file__).resolve().parents[2]

OUTPUT_DIR = (
    SRC_DIR
    / "output"
    / "investigation"
)

PHASE16_JSON = (
    OUTPUT_DIR
    / "phase16_evidence_linked_case_brief.json"
)

PHASE16_TEXT = (
    OUTPUT_DIR
    / "phase16_evidence_linked_case_brief.txt"
)


# ============================================================
# PAGE
# ============================================================

st.set_page_config(
    page_title="Final Evidence-Linked Case Brief",
    page_icon="📋",
    layout="wide"
)


# ============================================================
# LOAD
# ============================================================

def load_json():

    if not PHASE16_JSON.exists():

        return None

    with open(
        PHASE16_JSON,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


report = load_json()


# ============================================================
# HEADER
# ============================================================

st.title(
    "📋 Final Evidence-Linked Case Brief"
)

st.caption(
    "Chanakya-Graph — Phase 16"
)

st.info(
    "DRAFT FOR HUMAN REVIEW — "
    "This report connects investigative findings "
    "to underlying evidence records. It does not "
    "make automated guilt or legal attribution decisions."
)


# ============================================================
# MISSING REPORT
# ============================================================

if not report:

    st.warning(
        "Phase 16 report has not been generated yet."
    )

    st.code(
        "python -m src.investigation.phase16_evidence_linked_brief",
        language="powershell"
    )

    st.stop()


# ============================================================
# CASE
# ============================================================

case = report.get(
    "case_information",
    {}
)

st.subheader(
    "📁 Case Information"
)

c1, c2, c3, c4 = st.columns(4)

with c1:

    st.metric(
        "Case ID",
        case.get(
            "case_id",
            "UNKNOWN"
        )
    )

with c2:

    st.metric(
        "Status",
        case.get(
            "case_status",
            "UNKNOWN"
        )
    )

with c3:

    st.metric(
        "Data Class",
        case.get(
            "data_class",
            "UNKNOWN"
        )
    )

with c4:

    st.metric(
        "Report",
        report.get(
            "report_status",
            "UNKNOWN"
        )
    )


st.divider()


# ============================================================
# EVIDENCE SUMMARY
# ============================================================

st.subheader(
    "🔐 Evidence Summary"
)

evidence = report.get(
    "evidence_summary",
    {}
)

c1, c2 = st.columns(2)

with c1:

    st.metric(
        "Evidence Records",
        evidence.get(
            "total_evidence_records",
            0
        )
    )

with c2:

    st.metric(
        "Linked Evidence",
        evidence.get(
            "linked_evidence_records",
            0
        )
    )


evidence_types = evidence.get(
    "evidence_by_type",
    {}
)

if evidence_types:

    st.write(
        "### Evidence by Type"
    )

    st.dataframe(
        [
            {
                "Evidence Type": key,
                "Records": value
            }
            for key, value
            in evidence_types.items()
        ],
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# TIMELINE
# ============================================================

st.divider()

st.subheader(
    "🕒 Investigation Timeline"
)

timeline = report.get(
    "timeline_summary",
    {}
)

c1, c2, c3 = st.columns(3)

with c1:

    st.metric(
        "Events",
        timeline.get(
            "event_count",
            0
        )
    )

with c2:

    st.metric(
        "First Event",
        timeline.get(
            "first_event",
            "N/A"
        )
    )

with c3:

    st.metric(
        "Last Event",
        timeline.get(
            "last_event",
            "N/A"
        )
    )


event_types = timeline.get(
    "event_types",
    {}
)

if event_types:

    st.dataframe(
        [
            {
                "Event Type": key,
                "Count": value
            }
            for key, value
            in event_types.items()
        ],
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# INVESTIGATION SUMMARY
# ============================================================

st.divider()

st.subheader(
    "🔎 Investigation Summary"
)

investigation = report.get(
    "investigation_summary",
    {}
)

entities = investigation.get(
    "entities",
    {}
)

connections = investigation.get(
    "connections",
    {}

)

financial = investigation.get(
    "financial",
    {}
)


if entities:

    st.write("### Entities")

    st.json(
        entities
    )


if connections:

    st.write("### Connections")

    st.json(
        connections
    )


if financial:

    st.write("### Financial Analysis")

    st.json(
        financial
    )


# ============================================================
# FINDINGS
# ============================================================

st.divider()

st.subheader(
    "🧠 Evidence-Linked Investigative Findings"
)

findings = report.get(
    "evidence_linked_findings",
    []
)

if not findings:

    st.info(
        "No evidence-linked findings available."
    )

else:

    for index, finding in enumerate(
        findings,
        start=1
    ):

        classification = finding.get(
            "classification",
            "ANALYTICAL INFERENCE"
        )

        if classification == "OBSERVED":

            box = st.success

        elif classification == "DERIVED":

            box = st.info

        else:

            box = st.warning

        box(
            f"{classification}"
        )

        st.markdown(
            f"### Finding {index}"
        )

        st.write(
            finding.get(
                "finding",
                ""
            )
        )

        evidence_ids = finding.get(
            "evidence_ids",
            []
        )

        if evidence_ids:

            st.write(
                "**Evidence IDs:**"
            )

            st.code(
                "\n".join(
                    str(x)
                    for x in evidence_ids
                )
            )

        linked = finding.get(
            "evidence",
            []
        )

        if linked:

            with st.expander(
                "🔗 Explain Evidence"
            ):

                rows = []

                for evidence_record in linked:

                    rows.append({
                        "Evidence ID":
                            evidence_record.get(
                                "evidence_id"
                            ),

                        "Type":
                            evidence_record.get(
                                "evidence_type"
                            ),

                        "Timestamp":
                            evidence_record.get(
                                "timestamp"
                            ),

                        "Status":
                            evidence_record.get(
                                "evidence_status"
                            ),

                        "Source":
                            evidence_record.get(
                                "data_source"
                            ),

                        "Amount":
                            evidence_record.get(
                                "amount_inr"
                            )
                    })

                st.dataframe(
                    rows,
                    use_container_width=True,
                    hide_index=True
                )


# ============================================================
# ACTIONS
# ============================================================

st.divider()

st.subheader(
    "🚨 Recommended Investigative Actions"
)

actions = report.get(
    "recommended_actions",
    []
)

for index, action in enumerate(
    actions,
    start=1
):

    if isinstance(action, dict):

        st.markdown(
            f"**{index}. "
            f"{action.get('action', '')}**"
        )

        if action.get("basis"):

            st.caption(
                f"Basis: {action.get('basis')}"
            )

    else:

        st.markdown(
            f"**{index}. {action}**"
        )


# ============================================================
# METHODOLOGY
# ============================================================

st.divider()

st.subheader(
    "📚 Evidence Classification"
)

methodology = report.get(
    "methodology",
    {}
)

for key, value in methodology.items():

    st.markdown(
        f"**{key}** — {value}"
    )


# ============================================================
# LIMITATIONS
# ============================================================

st.divider()

st.subheader(
    "⚠️ Limitations"
)

for limitation in report.get(
    "limitations",
    []
):

    st.write(
        f"• {limitation}"
    )


# ============================================================
# DOWNLOAD
# ============================================================

st.divider()

st.subheader(
    "📥 Export Final Case Brief"
)

col1, col2 = st.columns(2)

with col1:

    if PHASE16_TEXT.exists():

        with open(
            PHASE16_TEXT,
            "rb"
        ) as f:

            st.download_button(
                "📄 Download Text Report",
                data=f,
                file_name=(
                    "phase16_evidence_linked_case_brief.txt"
                ),
                mime="text/plain"
            )

with col2:

    with open(
        PHASE16_JSON,
        "rb"
    ) as f:

        st.download_button(
            "🗂️ Download JSON Report",
            data=f,
            file_name=(
                "phase16_evidence_linked_case_brief.json"
            ),
            mime="application/json"
        )