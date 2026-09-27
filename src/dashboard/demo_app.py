import io
import json
import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# IMPORT PROJECT MODULES
# ============================================================
from src.integration.demo_pipeline import run_complete_investigation
from src.ingestion.case_manager import create_case
from src.integration.demo_pipeline import run_complete_investigation
from src.integration.case_state import get_active_case_id


# ============================================================
# PATHS
# ============================================================

SRC_DIR = PROJECT_ROOT / "src"

DATA_DIR = SRC_DIR / "data"

CASES_DIR = DATA_DIR / "cases"

OUTPUT_DIR = SRC_DIR / "output"

GRAPH_OUTPUT_DIR = OUTPUT_DIR / "graph"

INVESTIGATION_OUTPUT_DIR = OUTPUT_DIR / "investigation"

ACTIVE_CASE_FILE = CASES_DIR / "active_case.json"


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Chanakya-Graph",
    page_icon="🕵️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 42px;
        font-weight: 800;
        margin-bottom: 0;
    }

    .subtitle {
        font-size: 17px;
        color: #777;
        margin-top: 0;
        margin-bottom: 25px;
    }

    .section-title {
        font-size: 25px;
        font-weight: 700;
        margin-top: 20px;
        margin-bottom: 12px;
    }

    .status-box {
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #ddd;
        margin-bottom: 10px;
    }

    .success-box {
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #28a745;
        background: rgba(40, 167, 69, 0.08);
    }

    .warning-box {
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #ffc107;
        background: rgba(255, 193, 7, 0.08);
    }

    .danger-box {
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #dc3545;
        background: rgba(220, 53, 69, 0.08);
    }

    div[data-testid="stMetric"] {
        border: 1px solid rgba(128,128,128,0.2);
        padding: 12px;
        border-radius: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

DEFAULT_STATE = {
    "case_created": False,
    "pipeline_completed": False,
    "active_case_id": None,
    "upload_signature": None,
    "pipeline_result": None,
}


for key, value in DEFAULT_STATE.items():

    if key not in st.session_state:

        st.session_state[key] = value


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def safe_load_json(path, default=None):

    if default is None:
        default = {}

    try:

        if not path.exists():
            return default

        with open(
            path,
            "r",
            encoding="utf-8",
        ) as file:

            return json.load(file)

    except Exception:

        return default


def safe_read_csv(path):

    try:

        if not path.exists():
            return None

        return pd.read_csv(path)

    except Exception:

        return None


def uploaded_file_bytes(uploaded_file):

    if uploaded_file is None:
        return None

    try:

        uploaded_file.seek(0)

        data = uploaded_file.getvalue()

        if not data:

            raise ValueError(
                f"Uploaded file '{uploaded_file.name}' is empty."
            )

        return data

    except Exception as error:

        raise ValueError(
            f"Could not read uploaded file "
            f"'{uploaded_file.name}': {error}"
        )


def make_fresh_uploaded_file(uploaded_file):

    data = uploaded_file_bytes(uploaded_file)

    fresh_file = io.BytesIO(data)

    fresh_file.name = uploaded_file.name

    return fresh_file


def read_preview(uploaded_file):

    try:

        data = uploaded_file_bytes(uploaded_file)

        return pd.read_csv(
            io.BytesIO(data)
        )

    except Exception as error:

        raise ValueError(
            f"Could not preview '{uploaded_file.name}': {error}"
        )


def get_file_signature(uploaded_file):

    if uploaded_file is None:
        return None

    try:

        data = uploaded_file_bytes(uploaded_file)

        return (
            uploaded_file.name,
            len(data),
            hash(data),
        )

    except Exception:

        return None


def get_all_upload_signatures(
    cdr_file,
    upi_file,
    complaints_file,
    devices_file,
):

    return (
        get_file_signature(cdr_file),
        get_file_signature(upi_file),
        get_file_signature(complaints_file),
        get_file_signature(devices_file),
    )


def reset_investigation_state():

    st.session_state["case_created"] = False

    st.session_state["pipeline_completed"] = False

    st.session_state["active_case_id"] = None

    st.session_state["pipeline_result"] = None


def get_case_directory():

    case_id = st.session_state.get(
        "active_case_id"
    )

    if not case_id:
        return None

    case_dir = CASES_DIR / case_id

    if not case_dir.exists():
        return None

    return case_dir


def output_exists(path):

    return path.exists()


# ============================================================
# ACTIVE CASE
# ============================================================

def load_active_case():

    case_id = None

    try:

        case_id = get_active_case_id()

    except Exception:

        pass

    if not case_id:

        case_data = safe_load_json(
            ACTIVE_CASE_FILE,
            {},
        )

        if isinstance(case_data, dict):

            case_id = (
                case_data.get("case_id")
                or case_data.get("id")
            )

    if case_id:

        st.session_state["active_case_id"] = case_id

    return case_id


# ============================================================
# PIPELINE OUTPUT STATUS
# ============================================================

def get_pipeline_outputs():

    outputs = {

        "graph":
            GRAPH_OUTPUT_DIR /
            "investigation_graph.json",

        "graph_analysis":
            GRAPH_OUTPUT_DIR /
            "graph_analysis.json",

        "command_center":
            INVESTIGATION_OUTPUT_DIR /
            "command_center.json",

        "evidence":
            INVESTIGATION_OUTPUT_DIR /
            "evidence_ledger.json",

        "timeline":
            INVESTIGATION_OUTPUT_DIR /
            "investigation_timeline.json",

        "edge_cases":
            INVESTIGATION_OUTPUT_DIR /
            "edge_case_intelligence.json",

        "final_brief":
            INVESTIGATION_OUTPUT_DIR /
            "final_case_brief.json",

        "phase16":
            INVESTIGATION_OUTPUT_DIR /
            "phase16_evidence_linked_case_brief.json",

    }

    return outputs


def pipeline_outputs_ready():

    outputs = get_pipeline_outputs()

    required = [
        outputs["graph"],
        outputs["graph_analysis"],
    ]

    return all(
        path.exists()
        for path in required
    )


# ============================================================
# VALIDATE UPLOAD
# ============================================================

def validate_uploaded_dataset(
    uploaded_file,
    evidence_type,
):

    required_columns = {

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

    if uploaded_file is None:

        return False, [
            "File not uploaded."
        ], None

    try:

        df = read_preview(uploaded_file)

    except Exception as error:

        return False, [
            str(error)
        ], None

    normalized_columns = [
        str(column)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("/", "_")
        for column in df.columns
    ]

    df.columns = normalized_columns

    required = required_columns[evidence_type]

    missing = [
        column
        for column in required
        if column not in df.columns
    ]

    if missing:

        return (
            False,
            [
                "Missing columns: "
                + ", ".join(missing)
            ],
            df,
        )

    if df.empty:

        return (
            False,
            ["Dataset contains no rows."],
            df,
        )

    return True, [], df


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">🕵️ Chanakya-Graph</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="subtitle">
    AI-Assisted Cyber-Fraud Investigation & Evidence Graph Platform
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("🔎 Investigation")

st.sidebar.markdown(
    "### Navigation"
)


pages = [
    "Case Intake",
    "Investigation Command Center",
    "Investigation Graph",
    "AI Findings",
    "Evidence Explorer",
    "Timeline",
    "Edge Case Intelligence",
    "Investigation Copilot",
    "Final Case Brief",
]


selected_page = st.sidebar.radio(
    "Open module",
    pages,
)


st.sidebar.divider()


# ============================================================
# ACTIVE CASE INFORMATION
# ============================================================

active_case_id = load_active_case()

if active_case_id:

    st.sidebar.success(
        f"Active Case\n\n{active_case_id}"
    )

else:

    st.sidebar.info(
        "No active case."
    )


# ============================================================
# CASE INTAKE
# ============================================================

if selected_page == "Case Intake":

    st.markdown(
        '<div class="section-title">📂 Case Intake</div>',
        unsafe_allow_html=True,
    )

    st.write(
        """
        Upload the four evidence sources required for the
        cyber-fraud investigation pipeline.
        """
    )

    st.info(
        """
        Demo data should be synthetic/mock investigation data.
        The platform links CDR, UPI, complaint and device evidence
        into a common investigation graph.
        """
    )

    # --------------------------------------------------------
    # CASE DETAILS
    # --------------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        case_name = st.text_input(
            "Case Name",
            value="Cyber Fraud Investigation",
        )

    with col2:

        case_description = st.text_input(
            "Case Description",
            value=(
                "Multi-source cyber-fraud investigation case"
            ),
        )

    st.divider()

    # --------------------------------------------------------
    # UPLOADERS
    # --------------------------------------------------------

    st.subheader("Evidence Sources")

    col1, col2 = st.columns(2)

    with col1:

        cdr_file = st.file_uploader(
            "📞 CDR Records",
            type=["csv"],
            key="cdr_uploader",
            help=(
                "Call Detail Records containing caller, "
                "called number, IMEI and tower information."
            ),
        )

        complaints_file = st.file_uploader(
            "🚨 Complaints",
            type=["csv"],
            key="complaints_uploader",
            help=(
                "Cyber-fraud complaints and victim information."
            ),
        )

    with col2:

        upi_file = st.file_uploader(
            "💰 UPI Transactions",
            type=["csv"],
            key="upi_uploader",
            help=(
                "UPI transaction records containing "
                "sender, receiver and amount."
            ),
        )

        devices_file = st.file_uploader(
            "📱 Device Records",
            type=["csv"],
            key="devices_uploader",
            help=(
                "Phone/IMEI/device observations."
            ),
        )

    # --------------------------------------------------------
    # FILE VALIDATION
    # --------------------------------------------------------

    files_ready = all(
        file is not None
        for file in [
            cdr_file,
            upi_file,
            complaints_file,
            devices_file,
        ]
    )

    if files_ready:

        st.divider()

        st.subheader(
            "Evidence Validation"
        )

        validation_data = [

            (
                "CDR",
                cdr_file,
                "cdr",
            ),

            (
                "UPI",
                upi_file,
                "upi",
            ),

            (
                "Complaints",
                complaints_file,
                "complaints",
            ),

            (
                "Devices",
                devices_file,
                "devices",
            ),

        ]

        validation_ok = True

        previews = {}

        for display_name, uploaded_file, evidence_type in validation_data:

            valid, errors, dataframe = (
                validate_uploaded_dataset(
                    uploaded_file,
                    evidence_type,
                )
            )

            previews[evidence_type] = dataframe

            if valid:

                st.success(
                    f"✅ {display_name}: "
                    f"{len(dataframe):,} records"
                )

            else:

                validation_ok = False

                st.error(
                    f"❌ {display_name}: "
                    + " | ".join(errors)
                )

        # ----------------------------------------------------
        # PREVIEW
        # ----------------------------------------------------

        if validation_ok:

            with st.expander(
                "👁️ Preview Uploaded Evidence",
                expanded=False,
            ):

                for evidence_type, dataframe in previews.items():

                    if dataframe is None:
                        continue

                    st.markdown(
                        f"**{evidence_type.upper()}**"
                    )

                    st.dataframe(
                        dataframe.head(10),
                        width="stretch",
                        hide_index=True,
                    )

        # ----------------------------------------------------
        # FILE CHANGE DETECTION
        # ----------------------------------------------------

        current_signature = (
            get_all_upload_signatures(
                cdr_file,
                upi_file,
                complaints_file,
                devices_file,
            )
        )

        previous_signature = (
            st.session_state.get(
                "upload_signature"
            )
        )

        if (
            previous_signature is not None
            and current_signature != previous_signature
        ):

            reset_investigation_state()

        st.session_state[
            "upload_signature"
        ] = current_signature

        # ----------------------------------------------------
        # PROCESS BUTTON
        # ----------------------------------------------------

        st.divider()

        process_button = st.button(
            "🚀 PROCESS INVESTIGATION",
            type="primary",
            width="stretch",
        )

        if process_button:

            try:

                # --------------------------------------------
                # FRESH FILE OBJECTS
                # --------------------------------------------

                uploaded_files = {

                    "cdr":
                        make_fresh_uploaded_file(
                            cdr_file
                        ),

                    "upi":
                        make_fresh_uploaded_file(
                            upi_file
                        ),

                    "complaints":
                        make_fresh_uploaded_file(
                            complaints_file
                        ),

                    "devices":
                        make_fresh_uploaded_file(
                            devices_file
                        ),

                }

                # --------------------------------------------
                # CREATE CASE
                # --------------------------------------------

                with st.spinner(
                    "Creating investigation case..."
                ):

                    case = create_case(
                        case_name,
                        case_description,
                        uploaded_files,
                    )

                # --------------------------------------------
                # SAVE CASE STATE
                # --------------------------------------------

                case_id = None

                if isinstance(case, dict):

                    case_id = (
                        case.get("case_id")
                        or case.get("id")
                    )

                elif isinstance(case, str):

                    case_id = case

                if case_id:

                    st.session_state[
                        "active_case_id"
                    ] = case_id

                else:

                    case_id = load_active_case()

                st.session_state[
                    "case_created"
                ] = True

                # --------------------------------------------
                # RUN COMPLETE PIPELINE
                # --------------------------------------------

                with st.spinner(
                    """
                    Running complete Chanakya-Graph
                    investigation pipeline...
                    """
                ):

                    result = (
                        run_complete_investigation()
                    )

                st.session_state[
                    "pipeline_result"
                ] = result

                # --------------------------------------------
                # VERIFY OUTPUT
                # --------------------------------------------

                if not pipeline_outputs_ready():

                    st.session_state[
                        "pipeline_completed"
                    ] = False

                    st.error(
                        """
                        Investigation pipeline did not
                        generate the required graph outputs.

                        Please check the terminal running
                        the Streamlit application.
                        """
                    )

                else:

                    st.session_state[
                        "pipeline_completed"
                    ] = True

                    st.success(
                        "✅ Investigation pipeline completed successfully."
                    )

                    st.balloons()

                    st.rerun()

            except Exception as error:

                st.session_state[
                    "pipeline_completed"
                ] = False

                st.error(
                    f"Case processing failed: {error}"
                )

                with st.expander(
                    "Technical Error Details"
                ):

                    st.exception(error)

    else:

        st.warning(
            "Upload all four evidence files before processing."
        )


# ============================================================
# COMMAND CENTER
# ============================================================

elif selected_page == "Investigation Command Center":

    st.markdown(
        '<div class="section-title">🎯 Investigation Command Center</div>',
        unsafe_allow_html=True,
    )

    command_center_path = (
        INVESTIGATION_OUTPUT_DIR /
        "command_center.json"
    )

    data = safe_load_json(
        command_center_path,
        {},
    )

    if not data:

        st.warning(
            "Command Center data is not available yet."
        )

        st.info(
            "Process a case from Case Intake first."
        )

    else:

        # ----------------------------------------------------
        # CASE
        # ----------------------------------------------------

        st.subheader("Case Status")

        case_id = (
            data.get("case_id")
            or st.session_state.get(
                "active_case_id"
            )
            or "UNKNOWN"
        )

        st.code(
            str(case_id)
        )

        # ----------------------------------------------------
        # EVIDENCE
        # ----------------------------------------------------

        evidence = (
            data.get("evidence")
            or data.get("evidence_summary")
            or {}
        )

        st.subheader("Evidence")

        cols = st.columns(5)

        evidence_values = [

            (
                "Total",
                evidence.get(
                    "total",
                    data.get(
                        "total_evidence",
                        0,
                    ),
                ),
            ),

            (
                "CDR",
                evidence.get(
                    "cdr",
                    data.get(
                        "cdr_records",
                        0,
                    ),
                ),
            ),

            (
                "UPI",
                evidence.get(
                    "upi",
                    data.get(
                        "upi_records",
                        0,
                    ),
                ),
            ),

            (
                "Complaints",
                evidence.get(
                    "complaints",
                    data.get(
                        "complaints",
                        0,
                    ),
                ),
            ),

            (
                "Devices",
                evidence.get(
                    "devices",
                    data.get(
                        "devices",
                        0,
                    ),
                ),
            ),

        ]

        for column, (label, value) in zip(
            cols,
            evidence_values,
        ):

            with column:

                st.metric(
                    label,
                    value,
                )

        # ----------------------------------------------------
        # FINANCIAL
        # ----------------------------------------------------

        financial = (
            data.get("financial_analysis")
            or data.get("financial")
            or {}
        )

        st.subheader(
            "Financial Analysis"
        )

        cols = st.columns(4)

        financial_values = [

            (
                "Transactions",
                financial.get(
                    "transactions",
                    data.get(
                        "transactions",
                        0,
                    ),
                ),
            ),

            (
                "Total Amount",
                financial.get(
                    "total_amount_inr",
                    data.get(
                        "total_amount_inr",
                        0,
                    ),
                ),
            ),

            (
                "Unique Senders",
                financial.get(
                    "unique_senders",
                    0,
                ),
            ),

            (
                "Unique Receivers",
                financial.get(
                    "unique_receivers",
                    0,
                ),
            ),

        ]

        for column, (label, value) in zip(
            cols,
            financial_values,
        ):

            with column:

                if "Amount" in label:

                    try:

                        display_value = (
                            f"INR {float(value):,.2f}"
                        )

                    except Exception:

                        display_value = str(value)

                else:

                    display_value = value

                st.metric(
                    label,
                    display_value,
                )

        # ----------------------------------------------------
        # ENTITIES
        # ----------------------------------------------------

        entities = (
            data.get("entities")
            or {}
        )

        st.subheader(
            "Entity Inventory"
        )

        entity_cols = st.columns(6)

        entity_values = [

            (
                "Phones",
                entities.get(
                    "phones",
                    0,
                ),
            ),

            (
                "Accounts",
                entities.get(
                    "accounts",
                    0,
                ),
            ),

            (
                "IMEIs",
                entities.get(
                    "imeis",
                    0,
                ),
            ),

            (
                "Towers",
                entities.get(
                    "towers",
                    0,
                ),
            ),

            (
                "Persons",
                entities.get(
                    "persons",
                    0,
                ),
            ),

            (
                "Transactions",
                entities.get(
                    "transactions",
                    0,
                ),
            ),

        ]

        for column, (label, value) in zip(
            entity_cols,
            entity_values,
        ):

            with column:

                st.metric(
                    label,
                    value,
                )

        # ----------------------------------------------------
        # FINDINGS
        # ----------------------------------------------------

        findings = data.get(
            "investigation_findings",
            [],
        )

        if findings:

            st.subheader(
                "Investigation Findings"
            )

            for finding in findings:

                if isinstance(
                    finding,
                    dict,
                ):

                    title = (
                        finding.get(
                            "title"
                        )
                        or finding.get(
                            "finding"
                        )
                        or "Finding"
                    )

                    description = (
                        finding.get(
                            "description"
                        )
                        or finding.get(
                            "details"
                        )
                        or ""
                    )

                    st.markdown(
                        f"**{title}**"
                    )

                    if description:

                        st.write(
                            description
                        )

                else:

                    st.write(
                        str(finding)
                    )


# ============================================================
# INVESTIGATION GRAPH
# ============================================================

elif selected_page == "Investigation Graph":

    st.markdown(
        '<div class="section-title">🕸️ Investigation Graph</div>',
        unsafe_allow_html=True,
    )

    graph_path = (
        GRAPH_OUTPUT_DIR /
        "investigation_graph.json"
    )

    graph_analysis_path = (
        GRAPH_OUTPUT_DIR /
        "graph_analysis.json"
    )

    graph_data = safe_load_json(
        graph_path,
        {},
    )

    graph_analysis = safe_load_json(
        graph_analysis_path,
        {},
    )

    if not graph_data:

        st.warning(
            "Investigation graph has not been generated."
        )

        st.info(
            "Run the investigation pipeline first."
        )

    else:

        nodes = graph_data.get(
            "nodes",
            [],
        )

        edges = graph_data.get(
            "edges",
            [],
        )

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "Graph Nodes",
                len(nodes),
            )

        with col2:

            st.metric(
                "Graph Edges",
                len(edges),
            )

        with col3:

            components = (
                graph_analysis.get(
                    "connected_components",
                    graph_analysis.get(
                        "components",
                        0,
                    ),
                )
            )

            st.metric(
                "Components",
                components,
            )

        # ----------------------------------------------------
        # PYVIS HTML
        # ----------------------------------------------------

        html_path = (
            SRC_DIR /
            "graph" /
            "investigation_graph.html"
        )

        if not html_path.exists():

            html_path = (
                GRAPH_OUTPUT_DIR /
                "investigation_graph.html"
            )

        if html_path.exists():

            try:

                html_content = (
                    html_path.read_text(
                        encoding="utf-8"
                    )
                )

                st.components.v1.html(
                    html_content,
                    height=700,
                    scrolling=True,
                )

            except Exception as error:

                st.error(
                    f"Could not render graph: {error}"
                )

        else:

            st.info(
                """
                Graph JSON exists, but the interactive
                HTML visualization was not found.
                """
            )

            with st.expander(
                "View Graph JSON"
            ):

                st.json(
                    graph_data
                )

        # ----------------------------------------------------
        # CONNECTION TABLE
        # ----------------------------------------------------

        st.subheader(
            "Graph Relationships"
        )

        relationship_rows = []

        for edge in edges:

            relationship_rows.append(
                {
                    "Source":
                        edge.get(
                            "source",
                            "",
                        ),

                    "Target":
                        edge.get(
                            "target",
                            "",
                        ),

                    "Relationship":
                        edge.get(
                            "relationship",
                            edge.get(
                                "type",
                                "",
                            ),
                        ),

                    "Evidence ID":
                        edge.get(
                            "evidence_id",
                            edge.get(
                                "record_id",
                                "",
                            ),
                        ),

                    "Timestamp":
                        edge.get(
                            "timestamp",
                            "",
                        ),
                }
            )

        if relationship_rows:

            st.dataframe(
                pd.DataFrame(
                    relationship_rows
                ),
                width="stretch",
                hide_index=True,
            )


# ============================================================
# AI FINDINGS
# ============================================================

elif selected_page == "AI Findings":

    st.markdown(
        '<div class="section-title">🤖 AI Investigation Findings</div>',
        unsafe_allow_html=True,
    )

    predictions_path = (
        SRC_DIR /
        "output" /
        "model" /
        "predictions.json"
    )

    explanations_path = (
        INVESTIGATION_OUTPUT_DIR /
        "finding_explanations.json"
    )

    predictions = safe_load_json(
        predictions_path,
        [],
    )

    explanations = safe_load_json(
        explanations_path,
        [],
    )

    if not predictions:

        st.warning(
            "AI model predictions are not available."
        )

    else:

        if isinstance(
            predictions,
            dict,
        ):

            if "predictions" in predictions:

                predictions = predictions[
                    "predictions"
                ]

            else:

                predictions = [
                    predictions
                ]

        st.metric(
            "Predictions",
            len(predictions),
        )

        st.divider()

        for index, prediction in enumerate(
            predictions[:100]
        ):

            if not isinstance(
                prediction,
                dict,
            ):

                continue

            entity = (
                prediction.get(
                    "entity_id"
                )
                or prediction.get(
                    "entity"
                )
                or "Unknown Entity"
            )

            pattern = (
                prediction.get(
                    "prediction"
                )
                or prediction.get(
                    "pattern"
                )
                or prediction.get(
                    "predicted_class"
                )
                or "UNKNOWN"
            )

            confidence = (
                prediction.get(
                    "confidence"
                )
            )

            if confidence is not None:

                try:

                    confidence_display = (
                        f"{float(confidence) * 100:.2f}%"
                    )

                except Exception:

                    confidence_display = str(
                        confidence
                    )

            else:

                confidence_display = "N/A"

            with st.expander(
                f"{entity} — {pattern} — {confidence_display}"
            ):

                st.json(
                    prediction
                )


# ============================================================
# EVIDENCE EXPLORER
# ============================================================

elif selected_page == "Evidence Explorer":

    st.markdown(
        '<div class="section-title">📑 Evidence Explorer</div>',
        unsafe_allow_html=True,
    )

    evidence_path = (
        INVESTIGATION_OUTPUT_DIR /
        "evidence_ledger.json"
    )

    evidence_data = safe_load_json(
        evidence_path,
        {},
    )

    if not evidence_data:

        st.warning(
            "Evidence ledger is not available."
        )

    else:

        if isinstance(
            evidence_data,
            dict,
        ):

            records = (
                evidence_data.get(
                    "records",
                    evidence_data.get(
                        "evidence",
                        [],
                    ),
                )
            )

        else:

            records = evidence_data

        if not isinstance(
            records,
            list,
        ):

            records = []

        st.metric(
            "Evidence Records",
            len(records),
        )

        if records:

            evidence_rows = []

            for record in records:

                if not isinstance(
                    record,
                    dict,
                ):

                    continue

                evidence_rows.append(
                    {
                        "Evidence ID":
                            record.get(
                                "evidence_id",
                                record.get(
                                    "record_id",
                                    "",
                                ),
                            ),

                        "Type":
                            record.get(
                                "evidence_type",
                                record.get(
                                    "type",
                                    "",
                                ),
                            ),

                        "Status":
                            record.get(
                                "evidence_status",
                                "OBSERVED",
                            ),

                        "Timestamp":
                            record.get(
                                "timestamp",
                                "",
                            ),

                        "Source":
                            record.get(
                                "source",
                                record.get(
                                    "data_source",
                                    "",
                                ),
                            ),
                    }
                )

            if evidence_rows:

                st.dataframe(
                    pd.DataFrame(
                        evidence_rows
                    ),
                    width="stretch",
                    hide_index=True,
                )


# ============================================================
# TIMELINE
# ============================================================

elif selected_page == "Timeline":

    st.markdown(
        '<div class="section-title">🕒 Investigation Timeline</div>',
        unsafe_allow_html=True,
    )

    timeline_path = (
        INVESTIGATION_OUTPUT_DIR /
        "investigation_timeline.json"
    )

    timeline = safe_load_json(
        timeline_path,
        {},
    )

    if not timeline:

        st.warning(
            "Investigation timeline is not available."
        )

    else:

        events = (
            timeline.get(
                "events",
                timeline
                if isinstance(
                    timeline,
                    list,
                )
                else [],
            )
        )

        if not isinstance(
            events,
            list,
        ):

            events = []

        st.metric(
            "Timeline Events",
            len(events),
        )

        timeline_rows = []

        for event in events:

            if not isinstance(
                event,
                dict,
            ):

                continue

            timeline_rows.append(
                {
                    "Timestamp":
                        event.get(
                            "timestamp",
                            "",
                        ),

                    "Type":
                        event.get(
                            "event_type",
                            event.get(
                                "type",
                                "",
                            ),
                        ),

                    "Source":
                        event.get(
                            "source",
                            "",
                        ),

                    "Target":
                        event.get(
                            "target",
                            "",
                        ),

                    "Evidence":
                        event.get(
                            "evidence_id",
                            "",
                        ),

                    "Description":
                        event.get(
                            "description",
                            "",
                        ),
                }
            )

        if timeline_rows:

            timeline_df = pd.DataFrame(
                timeline_rows
            )

            st.dataframe(
                timeline_df,
                width="stretch",
                hide_index=True,
            )


# ============================================================
# EDGE CASE INTELLIGENCE
# ============================================================

elif selected_page == "Edge Case Intelligence":

    st.markdown(
        '<div class="section-title">⚠️ Edge Case Intelligence</div>',
        unsafe_allow_html=True,
    )

    edge_case_path = (
        INVESTIGATION_OUTPUT_DIR /
        "edge_case_intelligence.json"
    )

    edge_cases = safe_load_json(
        edge_case_path,
        {},
    )

    if not edge_cases:

        st.warning(
            "Edge case analysis is not available."
        )

    else:

        findings = (
            edge_cases.get(
                "findings",
                edge_cases.get(
                    "edge_cases",
                    [],
                ),
            )
        )

        if not isinstance(
            findings,
            list,
        ):

            findings = []

        st.metric(
            "Detected Edge Cases",
            len(findings),
        )

        for finding in findings:

            if not isinstance(
                finding,
                dict,
            ):

                st.write(
                    str(finding)
                )

                continue

            title = (
                finding.get(
                    "title"
                )
                or finding.get(
                    "type"
                )
                or finding.get(
                    "finding"
                )
                or "Edge Case"
            )

            description = (
                finding.get(
                    "description"
                )
                or finding.get(
                    "details"
                )
                or ""
            )

            with st.expander(
                str(title)
            ):

                if description:

                    st.write(
                        description
                    )

                st.json(
                    finding
                )


# ============================================================
# INVESTIGATION COPILOT
# ============================================================

elif selected_page == "Investigation Copilot":

    st.markdown(
        '<div class="section-title">🧠 Investigation Copilot</div>',
        unsafe_allow_html=True,
    )

    st.write(
        """
        Ask questions about the investigation graph.
        The Copilot uses the structured investigation data
        rather than inventing evidence.
        """
    )

    question = st.text_input(
        "Ask an investigation question",
        placeholder=(
            "Why is +919900000101 connected to "
            "+919900000201?"
        ),
    )

    if st.button(
        "🔍 ASK COPILOT",
        type="primary",
        width="stretch",
    ):

        if not question.strip():

            st.warning(
                "Enter a question first."
            )

        else:

            try:

                from src.copilot.natural_language import (
                    process_question
                )

                result = process_question(
                    question
                )

                st.subheader(
                    "Copilot Response"
                )

                if isinstance(
                    result,
                    dict,
                ):

                    answer = (
                        result.get(
                            "answer"
                        )
                        or result.get(
                            "response"
                        )
                        or result.get(
                            "explanation"
                        )
                    )

                    if answer:

                        st.write(
                            answer
                        )

                    else:

                        st.json(
                            result
                        )

                else:

                    st.write(
                        result
                    )

            except Exception as error:

                st.error(
                    f"Copilot error: {error}"
                )

                with st.expander(
                    "Technical Details"
                ):

                    st.exception(
                        error
                    )


# ============================================================
# FINAL CASE BRIEF
# ============================================================

elif selected_page == "Final Case Brief":

    st.markdown(
        '<div class="section-title">📄 Final Case Brief</div>',
        unsafe_allow_html=True,
    )

    phase16_path = (
        INVESTIGATION_OUTPUT_DIR /
        "phase16_evidence_linked_case_brief.json"
    )

    final_path = (
        INVESTIGATION_OUTPUT_DIR /
        "final_case_brief.json"
    )

    phase16 = safe_load_json(
        phase16_path,
        {},
    )

    final_brief = safe_load_json(
        final_path,
        {},
    )

    brief = (
        phase16
        if phase16
        else final_brief
    )

    if not brief:

        st.warning(
            "Final case brief is not available."
        )

        st.info(
            "Complete the investigation pipeline first."
        )

    else:

        # ----------------------------------------------------
        # CASE INFORMATION
        # ----------------------------------------------------

        case_id = (
            brief.get(
                "case_id"
            )
            or st.session_state.get(
                "active_case_id"
            )
            or "UNKNOWN"
        )

        st.subheader(
            "Case Information"
        )

        st.code(
            str(case_id)
        )

        # ----------------------------------------------------
        # SUMMARY
        # ----------------------------------------------------

        summary = (
            brief.get(
                "executive_summary"
            )
            or brief.get(
                "summary"
            )
            or brief.get(
                "case_summary"
            )
        )

        if summary:

            st.subheader(
                "Executive Summary"
            )

            st.write(
                summary
            )

        # ----------------------------------------------------
        # FINDINGS
        # ----------------------------------------------------

        findings = (
            brief.get(
                "findings",
                []
            )
        )

        if findings:

            st.subheader(
                "Investigation Findings"
            )

            if isinstance(
                findings,
                list,
            ):

                for finding in findings:

                    if isinstance(
                        finding,
                        dict,
                    ):

                        title = (
                            finding.get(
                                "title"
                            )
                            or finding.get(
                                "finding"
                            )
                            or "Finding"
                        )

                        description = (
                            finding.get(
                                "description"
                            )
                            or finding.get(
                                "details"
                            )
                            or ""
                        )

                        st.markdown(
                            f"### {title}"
                        )

                        if description:

                            st.write(
                                description
                            )

                    else:

                        st.write(
                            str(finding)
                        )

            else:

                st.write(
                    findings
                )

        # ----------------------------------------------------
        # RECOMMENDED ACTIONS
        # ----------------------------------------------------

        actions = (
            brief.get(
                "recommended_actions",
                brief.get(
                    "actions",
                    [],
                ),
            )
        )

        if actions:

            st.subheader(
                "Recommended Investigation Actions"
            )

            if isinstance(
                actions,
                list,
            ):

                for action in actions:

                    st.markdown(
                        f"- {action}"
                    )

            else:

                st.write(
                    actions
                )

        # ----------------------------------------------------
        # EVIDENCE
        # ----------------------------------------------------

        evidence = (
            brief.get(
                "evidence",
                []
            )
        )

        if evidence:

            st.subheader(
                "Evidence References"
            )

            if isinstance(
                evidence,
                list,
            ):

                for item in evidence:

                    if isinstance(
                        item,
                        dict,
                    ):

                        evidence_id = (
                            item.get(
                                "evidence_id",
                                item.get(
                                    "record_id",
                                    "UNKNOWN",
                                ),
                            )
                        )

                        st.markdown(
                            f"**Evidence ID:** "
                            f"`{evidence_id}`"
                        )

                        st.json(
                            item
                        )

                    else:

                        st.write(
                            item
                        )

        # ----------------------------------------------------
        # DOWNLOAD JSON
        # ----------------------------------------------------

        json_bytes = json.dumps(
            brief,
            indent=2,
            ensure_ascii=False,
        ).encode(
            "utf-8"
        )

        st.download_button(
            label="⬇️ Download Case Brief JSON",
            data=json_bytes,
            file_name="chanakya_case_brief.json",
            mime="application/json",
            width="stretch",
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    """
    Chanakya-Graph | AI-assisted cyber-fraud investigation platform |
    Synthetic/demo evidence only | Observed evidence is separated
    from analytical inference.
    """
)