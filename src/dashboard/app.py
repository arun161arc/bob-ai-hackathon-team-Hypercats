# ============================================================
# CHANAKYA-GRAPH
# Professional Cyber-Fraud Investigation Dashboard
#
# Dashboard replacement only.
# Preserves Phase 1–7 backend.
# ============================================================

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

import pandas as pd
import networkx as nx
import streamlit as st

# ------------------------------------------------------------
# PATH CONFIGURATION
# ------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = BASE_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

DATA_DIR = SRC_DIR / "data"
OUTPUT_DIR = SRC_DIR / "output"

GRAPH_DIR = OUTPUT_DIR / "graph"
ENTITY_DIR = OUTPUT_DIR / "entities"
MODEL_DIR = OUTPUT_DIR / "model"
INVESTIGATION_DIR = OUTPUT_DIR / "investigation"

GRAPH_FILE = GRAPH_DIR / "investigation_graph.json"
ANALYSIS_FILE = GRAPH_DIR / "graph_analysis.json"

PREDICTIONS_FILE = MODEL_DIR / "pattern_predictions.json"
TRAINING_FILE = MODEL_DIR / "training_data.csv"

EXPLANATIONS_FILE = INVESTIGATION_DIR / "finding_explanations.json"
CASE_BRIEF_FILE = INVESTIGATION_DIR / "case_brief.json"
CASE_BRIEF_TEXT = INVESTIGATION_DIR / "case_brief.txt"

ENTITIES_FILE = ENTITY_DIR / "canonical_entities.json"
MULTI_SOURCE_FILE = ENTITY_DIR / "multi_source_entities.json"

ACTIVE_CASE_FILE = DATA_DIR / "cases" / "active_case.json"

# ------------------------------------------------------------
# BACKEND IMPORTS
# ------------------------------------------------------------

try:
    from ingestion.case_manager import (
        create_case,
        get_active_case,
        activate_case,
        activate_demo_dataset,
    )
except Exception:
    create_case = None
    get_active_case = None
    activate_case = None
    activate_demo_dataset = None

try:
    from copilot.graph_query import load_graph
    from copilot.natural_language import process_question
except Exception:
    load_graph = None
    process_question = None


# ------------------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------------------

st.set_page_config(
    page_title="Chanakya-Graph | Cyber Fraud Investigation",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
<style>

:root {
    --bg: #07111f;
    --panel: #0d1b2a;
    --panel2: #101f31;
    --border: #24364a;
    --text: #e7eef7;
    --muted: #8fa3b8;
    --blue: #4da3ff;
    --green: #39d98a;
    --orange: #ffb454;
    --red: #ff6b6b;
    --purple: #a78bfa;
}

.stApp {
    background:
        radial-gradient(
            circle at 10% 0%,
            rgba(36, 99, 151, 0.18),
            transparent 35%
        ),
        linear-gradient(
            135deg,
            #07111f 0%,
            #081321 55%,
            #06101c 100%
        );
    color: var(--text);
}

section[data-testid="stSidebar"] {
    background: #07111f;
    border-right: 1px solid var(--border);
}

section[data-testid="stSidebar"] * {
    color: #dce7f2;
}

.block-container {
    padding-top: 1.5rem;
    padding-bottom: 3rem;
    max-width: 1500px;
}

h1, h2, h3 {
    letter-spacing: -0.02em;
}

.hero {
    padding: 24px 28px;
    border: 1px solid #29435e;
    border-radius: 18px;
    background:
        linear-gradient(
            135deg,
            rgba(19, 43, 67, 0.95),
            rgba(8, 22, 37, 0.96)
        );
    box-shadow: 0 14px 45px rgba(0,0,0,0.22);
    margin-bottom: 22px;
}

.hero-title {
    font-size: 31px;
    font-weight: 750;
    margin-bottom: 5px;
}

.hero-subtitle {
    color: #91a8bf;
    font-size: 15px;
}

.badge {
    display: inline-block;
    padding: 5px 11px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 700;
    margin-right: 6px;
    border: 1px solid #31506d;
    background: #0b1b2c;
    color: #a8c8e8;
}

.badge-green {
    border-color: #226c4a;
    color: #63e6a5;
    background: rgba(35, 123, 83, 0.12);
}

.badge-orange {
    border-color: #73512c;
    color: #ffc56d;
    background: rgba(180, 116, 36, 0.12);
}

.badge-red {
    border-color: #713d43;
    color: #ff9292;
    background: rgba(155, 52, 62, 0.12);
}

.badge-purple {
    border-color: #554078;
    color: #c7b3ff;
    background: rgba(104, 74, 163, 0.12);
}

.metric-card {
    border: 1px solid var(--border);
    background: rgba(13, 27, 42, 0.88);
    border-radius: 15px;
    padding: 17px;
    min-height: 110px;
}

.metric-label {
    color: var(--muted);
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

.metric-value {
    color: #f3f7fb;
    font-size: 27px;
    font-weight: 750;
    margin-top: 5px;
}

.metric-note {
    color: #7f95aa;
    font-size: 11px;
    margin-top: 4px;
}

.panel {
    border: 1px solid var(--border);
    background: rgba(13, 27, 42, 0.78);
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 18px;
}

.panel-title {
    font-size: 18px;
    font-weight: 700;
    margin-bottom: 4px;
}

.panel-subtitle {
    color: var(--muted);
    font-size: 13px;
    margin-bottom: 15px;
}

.stage {
    border: 1px solid var(--border);
    background: #0b1928;
    border-radius: 13px;
    padding: 13px;
    min-height: 105px;
}

.stage-number {
    font-size: 11px;
    color: #6f8da8;
    font-weight: 700;
}

.stage-title {
    font-size: 14px;
    font-weight: 700;
    margin-top: 3px;
}

.stage-desc {
    color: #8096aa;
    font-size: 11px;
    margin-top: 4px;
}

.finding {
    border-left: 4px solid #4da3ff;
    background: #0c1b2a;
    border-radius: 9px;
    padding: 13px 16px;
    margin-bottom: 10px;
}

.finding-green {
    border-left-color: #39d98a;
}

.finding-orange {
    border-left-color: #ffb454;
}

.finding-red {
    border-left-color: #ff6b6b;
}

.finding-title {
    font-weight: 700;
    font-size: 14px;
}

.finding-text {
    color: #9bb0c3;
    font-size: 12px;
    margin-top: 4px;
}

.evidence-id {
    font-family: monospace;
    color: #75b9ff;
}

.observed {
    color: #63e6a5;
}

.derived {
    color: #ffc56d;
}

.inference {
    color: #c4a7ff;
}

.workflow {
    display: flex;
    align-items: center;
    gap: 7px;
    overflow-x: auto;
    padding: 5px 0 17px 0;
}

.workflow-step {
    border: 1px solid #29435e;
    background: #0b1928;
    padding: 8px 11px;
    border-radius: 8px;
    white-space: nowrap;
    font-size: 11px;
    color: #a9bfd4;
}

.workflow-arrow {
    color: #486b88;
}

div[data-testid="stMetric"] {
    background: rgba(13, 27, 42, 0.75);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 12px;
}

div[data-testid="stMetricLabel"] {
    color: #8ea4b9;
}

button[kind="primary"] {
    border-radius: 9px;
}

.stDataFrame {
    border: 1px solid var(--border);
    border-radius: 10px;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# GENERIC HELPERS
# ============================================================

def safe_read_json(path):
    """Read JSON without crashing the dashboard."""
    try:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as exc:
        return {
            "_error": str(exc)
        }

    return {}


def safe_read_text(path):
    try:
        if path.exists():
            return path.read_text(encoding="utf-8")
    except Exception:
        pass

    return ""


def safe_read_csv(path, **kwargs):
    try:
        if path.exists():
            return pd.read_csv(path, **kwargs)
    except Exception:
        pass

    return pd.DataFrame()


def format_inr(value):
    try:
        return f"INR {float(value):,.0f}"
    except Exception:
        return "INR 0"


def format_number(value):
    try:
        return f"{int(value):,}"
    except Exception:
        return "0"


def file_exists(path):
    return path.exists()


def metric_card(label, value, note=""):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def panel_start(title, subtitle=""):
    st.markdown(
        f"""
        <div class="panel">
            <div class="panel-title">{title}</div>
            <div class="panel-subtitle">{subtitle}</div>
        """,
        unsafe_allow_html=True,
    )


def panel_end():
    st.markdown("</div>", unsafe_allow_html=True)


def badge(text, kind=""):
    cls = "badge"

    if kind:
        cls += f" badge-{kind}"

    return f'<span class="{cls}">{text}</span>'


def evidence_label(status):
    status = str(status).upper()

    if status == "OBSERVED":
        return badge("OBSERVED", "green")

    if status == "DERIVED":
        return badge("DERIVED", "orange")

    if "INFERENCE" in status:
        return badge("ANALYTICAL INFERENCE", "purple")

    return badge(status)


# ============================================================
# CASE INFORMATION
# ============================================================

def load_active_case():
    if get_active_case:
        try:
            case = get_active_case()

            if case:
                return case
        except Exception:
            pass

    return safe_read_json(ACTIVE_CASE_FILE)


def current_case_id():
    case = load_active_case()

    if isinstance(case, dict):
        return (
            case.get("case_id")
            or case.get("id")
            or "DEMO-CYB-2026-0001"
        )

    return "DEMO-CYB-2026-0001"


def current_case_title():
    case = load_active_case()

    if isinstance(case, dict):
        return (
            case.get("case_title")
            or case.get("title")
            or "Cyber-Fraud Investigation"
        )

    return "Cyber-Fraud Investigation"


# ============================================================
# BACKEND DATA
# ============================================================

def load_analysis():
    return safe_read_json(ANALYSIS_FILE)


def load_predictions():
    return safe_read_json(PREDICTIONS_FILE)


def load_explanations():
    return safe_read_json(EXPLANATIONS_FILE)


def load_case_brief():
    return safe_read_json(CASE_BRIEF_FILE)


def load_graph_json():
    return safe_read_json(GRAPH_FILE)


def load_entities():
    return safe_read_json(ENTITIES_FILE)


def load_multi_source_entities():
    return safe_read_json(MULTI_SOURCE_FILE)


# ============================================================
# GRAPH HELPERS
# ============================================================

def graph_to_networkx():
    data = load_graph_json()

    graph = nx.MultiDiGraph()

    if not isinstance(data, dict):
        return graph

    nodes = data.get("nodes", [])

    if isinstance(nodes, dict):
        nodes = [
            {"id": node_id, **attrs}
            for node_id, attrs in nodes.items()
        ]

    for node in nodes:
        if not isinstance(node, dict):
            continue

        node_id = node.get("id")

        if node_id is None:
            node_id = node.get("entity_id")

        if node_id is None:
            continue

        attrs = dict(node)
        attrs.pop("id", None)

        graph.add_node(node_id, **attrs)

    edges = data.get("edges", [])

    for edge in edges:
        if not isinstance(edge, dict):
            continue

        source = (
            edge.get("source")
            or edge.get("from")
        )

        target = (
            edge.get("target")
            or edge.get("to")
        )

        if source is None or target is None:
            continue

        attrs = dict(edge)

        attrs.pop("source", None)
        attrs.pop("target", None)

        graph.add_edge(
            source,
            target,
            **attrs
        )

    return graph


def node_display_name(graph, node_id):
    if node_id not in graph:
        return str(node_id)

    attrs = graph.nodes[node_id]

    return (
        attrs.get("value")
        or attrs.get("name")
        or attrs.get("entity_value")
        or node_id
    )


def node_type(graph, node_id):
    if node_id not in graph:
        return "UNKNOWN"

    attrs = graph.nodes[node_id]

    return (
        attrs.get("entity_type")
        or attrs.get("type")
        or "UNKNOWN"
    )


def graph_summary_from_networkx(graph):
    if graph.number_of_nodes() == 0:
        return {
            "nodes": 0,
            "edges": 0,
            "components": 0,
        }

    undirected = graph.to_undirected()

    return {
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "components": nx.number_connected_components(undirected),
    }


# ============================================================
# TRANSACTION HELPERS
# ============================================================

def load_transactions():
    return safe_read_csv(
        DATA_DIR / "upi_transactions.csv",
        dtype=str
    )


def load_cdr():
    return safe_read_csv(
        DATA_DIR / "cdr_records.csv",
        dtype=str
    )


def load_devices():
    return safe_read_csv(
        DATA_DIR / "device_records.csv",
        dtype=str
    )


def load_complaints():
    return safe_read_csv(
        DATA_DIR / "complaints.csv",
        dtype=str
    )


def transaction_amount_column(df):
    for col in [
        "amount_inr",
        "amount",
        "transaction_amount"
    ]:
        if col in df.columns:
            return col

    return None


# ============================================================
# BACKEND PROCESSING
# ============================================================

def run_backend_script(script_relative):
    """
    Execute an existing Phase 1–7 backend script.

    The backend itself remains untouched.
    """

    script_path = SRC_DIR / script_relative

    if not script_path.exists():
        return False, f"Backend script not found: {script_path}"

    try:
        result = subprocess.run(
            [
                sys.executable,
                str(script_path)
            ],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            timeout=300,
        )

        output = (
            result.stdout
            + "\n"
            + result.stderr
        )

        if result.returncode == 0:
            return True, output

        return False, output

    except Exception as exc:
        return False, str(exc)


def run_investigation_pipeline():

    stages = [
        (
            "Phase 2 — Entity extraction and resolution",
            "entity/run_phase2.py"
        ),
        (
            "Phase 3 — Investigation graph construction",
            "graph/run_phase3.py"
        ),
        (
            "Phase 4 — Fraud-pattern evaluation",
            "model/run_phase4.py"
        ),
        (
            "Phase 5 — Investigation intelligence and case brief",
            "investigation/run_phase5.py"
        ),
    ]

    results = []

    progress = st.progress(0)

    for index, (name, script) in enumerate(stages):

        st.write(f"**{name}**")

        with st.spinner("Processing evidence..."):
            success, output = run_backend_script(script)

        results.append(
            {
                "stage": name,
                "success": success,
                "output": output,
            }
        )

        if success:
            st.success("Completed")
        else:
            st.error("Failed")
            st.code(output[-4000:])

            break

        progress.progress(
            int(((index + 1) / len(stages)) * 100)
        )

    return results


# ============================================================
# SIDEBAR
# ============================================================

def render_sidebar():

    st.sidebar.markdown(
        """
        <div style="
            font-size:22px;
            font-weight:800;
            margin-bottom:2px;
        ">
            🔎 Chanakya-Graph
        </div>

        <div style="
            color:#8097ad;
            font-size:12px;
            margin-bottom:18px;
        ">
            Cyber-Fraud Investigation Workstation
        </div>
        """,
        unsafe_allow_html=True,
    )

    case_id = current_case_id()

    st.sidebar.markdown(
        f"""
        <div class="panel" style="padding:13px;">
            <div class="metric-label">ACTIVE CASE</div>
            <div style="
                font-family:monospace;
                font-size:12px;
                margin-top:6px;
                color:#79baff;
            ">
                {case_id}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    pages = [
        "Command Center",
        "Case Intake",
        "Evidence Processing",
        "Investigation Graph",
        "Mule Evaluation",
        "Potential Coordination Node",
        "IMEI Investigation",
        "Location / Tower Investigation",
        "Edge Case Analysis",
        "Explain Connection",
        "Investigation Copilot",
        "Timeline",
        "Evidence Explorer",
        "Final Case Brief",
    ]

    page = st.sidebar.radio(
        "INVESTIGATION MODULES",
        pages,
        index=0,
    )

    st.sidebar.markdown("---")

    st.sidebar.caption(
        "Evidence classification"
    )

    st.sidebar.markdown(
        badge("OBSERVED", "green")
        + badge("DERIVED", "orange")
        + badge("ANALYTICAL INFERENCE", "purple"),
        unsafe_allow_html=True,
    )

    st.sidebar.markdown("---")

    st.sidebar.caption(
        "Synthetic/demo evidence should be clearly distinguished from operational evidence."
    )

    return page


# ============================================================
# HEADER
# ============================================================

def render_header():

    case_id = current_case_id()

    st.markdown(
        f"""
        <div class="hero">

            <div class="hero-title">
                🔎 Chanakya-Graph
            </div>

            <div class="hero-subtitle">
                AI-assisted cyber-fraud investigation and
                evidence-linked network analysis
            </div>

            <div style="margin-top:14px;">
                {badge("ACTIVE INVESTIGATION", "green")}
                {badge("CASE " + str(case_id))}
                {badge("EVIDENCE-LINKED")}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# WORKFLOW
# ============================================================

def render_workflow():

    steps = [
        "UPLOAD",
        "RECONSTRUCT",
        "INVESTIGATE",
        "EXPLAIN",
        "PIVOT",
        "VALIDATE",
        "REPORT",
    ]

    html = '<div class="workflow">'

    for i, step in enumerate(steps):

        html += (
            f'<div class="workflow-step">{step}</div>'
        )

        if i < len(steps) - 1:
            html += (
                '<div class="workflow-arrow">→</div>'
            )

    html += "</div>"

    st.markdown(
        html,
        unsafe_allow_html=True
    )


# ============================================================
# COMMAND CENTER
# ============================================================

def page_command_center():

    st.header("Investigation Command Center")

    st.caption(
        "Operational overview of the evidence graph, transaction activity, "
        "device correlations and analytical findings."
    )

    render_workflow()

    graph = graph_to_networkx()

    summary = graph_summary_from_networkx(graph)

    tx = load_transactions()
    cdr = load_cdr()
    devices = load_devices()
    complaints = load_complaints()

    amount_col = transaction_amount_column(tx)

    total_amount = 0

    if amount_col:
        total_amount = pd.to_numeric(
            tx[amount_col],
            errors="coerce"
        ).fillna(0).sum()

    cols = st.columns(6)

    with cols[0]:
        metric_card(
            "Graph entities",
            format_number(summary["nodes"]),
            "Normalized entities"
        )

    with cols[1]:
        metric_card(
            "Relationships",
            format_number(summary["edges"]),
            "Observed graph edges"
        )

    with cols[2]:
        metric_card(
            "Transactions",
            format_number(len(tx)),
            "UPI evidence"
        )

    with cols[3]:
        metric_card(
            "Transaction value",
            format_inr(total_amount),
            "Observed UPI amount"
        )

    with cols[4]:
        metric_card(
            "Call records",
            format_number(len(cdr)),
            "Telephone evidence"
        )

    with cols[5]:
        metric_card(
            "Device records",
            format_number(len(devices)),
            "IMEI/device evidence"
        )

    st.markdown("")

    left, right = st.columns([1.4, 1])

    with left:

        panel_start(
            "Investigation status",
            "Current evidence reconstruction state"
        )

        stages = [
            ("Evidence ingestion", True),
            ("Entity extraction", file_exists(ENTITIES_FILE)),
            ("Entity resolution", file_exists(ENTITIES_FILE)),
            ("Graph construction", file_exists(GRAPH_FILE)),
            ("Pattern evaluation", file_exists(PREDICTIONS_FILE)),
            ("Finding generation", file_exists(EXPLANATIONS_FILE)),
            ("Case brief", file_exists(CASE_BRIEF_FILE)),
        ]

        for name, complete in stages:

            if complete:
                status = badge("COMPLETE", "green")
            else:
                status = badge("PENDING", "orange")

            st.markdown(
                f"""
                <div style="
                    padding:8px 0;
                    border-bottom:1px solid #1d3042;
                ">
                    <b>{name}</b>
                    <span style="float:right;">
                        {status}
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        panel_end()

    with right:

        panel_start(
            "Evidence posture",
            "What the system can currently establish"
        )

        st.markdown(
            f"""
            {badge("OBSERVED", "green")}
            Directly recorded evidence from supplied files.
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            f"""
            {badge("DERIVED", "orange")}
            Relationships calculated from supplied evidence.
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            f"""
            {badge("ANALYTICAL INFERENCE", "purple")}
            Pattern interpretation requiring investigator validation.
            """,
            unsafe_allow_html=True
        )

        panel_end()

    st.subheader("Current investigation signals")

    predictions = load_predictions()

    if isinstance(predictions, dict):
        records = (
            predictions.get("predictions")
            or predictions.get("results")
            or predictions.get("data")
            or []
        )
    elif isinstance(predictions, list):
        records = predictions
    else:
        records = []

    if records:

        pred_df = pd.DataFrame(records)

        st.dataframe(
            pred_df.head(20),
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "No pattern prediction output is currently available. "
            "Run Evidence Processing after loading a case."
        )


# ============================================================
# CASE INTAKE
# ============================================================

def page_case_intake():

    st.header("Case Intake")

    st.caption(
        "Register a case and supply the evidence files used for reconstruction."
    )

    panel_start(
        "Evidence submission",
        "Upload telephone, transaction, complaint and device records."
    )

    case_title = st.text_input(
        "Case title",
        value="Cyber-Fraud Investigation"
    )

    st.markdown(
        "### Required evidence categories"
    )

    c1, c2 = st.columns(2)

    with c1:

        cdr_file = st.file_uploader(
            "Telephone / CDR records",
            type=["csv"],
            key="cdr_upload",
            help="Expected fields include caller, called, timestamp, IMEI and tower."
        )

        upi_file = st.file_uploader(
            "Bank / UPI transaction records",
            type=["csv"],
            key="upi_upload",
            help="Expected fields include sender account, receiver account, amount and timestamp."
        )

    with c2:

        complaint_file = st.file_uploader(
            "Complaint records",
            type=["csv"],
            key="complaint_upload",
        )

        device_file = st.file_uploader(
            "Device / IMEI records",
            type=["csv"],
            key="device_upload",
            help="Expected fields include phone number, IMEI and tower."
        )

    panel_end()

    st.markdown("")

    if st.button(
        "📥 Register New Investigation Case",
        type="primary",
        use_container_width=True
    ):

        if create_case is None:
            st.error(
                "Case manager could not be imported."
            )
            return

        uploads = {}

        if cdr_file:
            uploads["cdr"] = cdr_file

        if upi_file:
            uploads["upi"] = upi_file

        if complaint_file:
            uploads["complaints"] = complaint_file

        if device_file:
            uploads["devices"] = device_file

        if not uploads:
            st.warning(
                "Upload at least one evidence file."
            )
            return

        try:

            with st.spinner(
                "Registering evidence and creating case..."
            ):

                case = create_case(
                    uploads,
                    case_title=case_title
                )

            st.success(
                "Investigation case registered successfully."
            )

            st.json(case)

            st.info(
                "Next step: open Evidence Processing."
            )

        except TypeError:

            try:

                case = create_case(
                    uploads
                )

                st.success(
                    "Investigation case registered."
                )

                st.json(case)

            except Exception as exc:
                st.error(
                    f"Unable to create case: {exc}"
                )

        except Exception as exc:

            st.error(
                f"Unable to create case: {exc}"
            )

    st.markdown("---")

    panel_start(
        "Synthetic demonstration dataset",
        "Use this mode when demonstrating the system without operational evidence."
    )

    st.warning(
        "The demonstration dataset is synthetic. "
        "It must not be presented as real police, banking or telecom evidence."
    )

    if st.button(
        "Load / Reset Synthetic Demo Case",
        use_container_width=True
    ):

        if activate_demo_dataset is None:
            st.error(
                "Demo dataset manager could not be imported."
            )
            return

        try:

            with st.spinner(
                "Activating synthetic demonstration case..."
            ):

                result = activate_demo_dataset()

            st.success(
                "Synthetic demonstration case activated."
            )

            if result is not None:
                st.json(result)

        except Exception as exc:

            st.error(
                f"Unable to activate demo case: {exc}"
            )

    panel_end()


# ============================================================
# EVIDENCE PROCESSING
# ============================================================

def page_evidence_processing():

    st.header("Evidence Processing")

    st.caption(
        "Run the existing Phase 2–5 investigation pipeline over the active case."
    )

    stages = [
        (
            "01",
            "Evidence ingestion",
            "Read and standardize supplied evidence."
        ),
        (
            "02",
            "Entity extraction",
            "Extract phone numbers, accounts, IMEI, towers and references."
        ),
        (
            "03",
            "Entity resolution",
            "Canonicalize repeated identifiers across evidence sources."
        ),
        (
            "04",
            "Graph construction",
            "Build evidence-linked communication and transaction relationships."
        ),
        (
            "05",
            "Pattern evaluation",
            "Evaluate controlled fraud-pattern features."
        ),
        (
            "06",
            "Investigation intelligence",
            "Generate evidence-linked findings and case brief."
        ),
    ]

    cols = st.columns(3)

    for i, (number, title, description) in enumerate(stages):

        with cols[i % 3]:

            st.markdown(
                f"""
                <div class="stage">
                    <div class="stage-number">STAGE {number}</div>
                    <div class="stage-title">{title}</div>
                    <div class="stage-desc">{description}</div>
                </div>
                <br>
                """,
                unsafe_allow_html=True,
            )

    if st.button(
        "▶ Run Investigation Reconstruction",
        type="primary",
        use_container_width=True
    ):

        results = run_investigation_pipeline()

        if results and all(
            item["success"]
            for item in results
        ):

            st.success(
                "Investigation reconstruction completed."
            )

            st.balloons()

    st.markdown("---")

    panel_start(
        "Current backend outputs",
        "These files are generated by the existing Phase 1–7 backend."
    )

    output_rows = [
        ("Normalized entities", ENTITIES_FILE),
        ("Multi-source entities", MULTI_SOURCE_FILE),
        ("Investigation graph", GRAPH_FILE),
        ("Graph analysis", ANALYSIS_FILE),
        ("Pattern predictions", PREDICTIONS_FILE),
        ("Finding explanations", EXPLANATIONS_FILE),
        ("Case brief", CASE_BRIEF_FILE),
    ]

    rows = []

    for name, path in output_rows:

        rows.append(
            {
                "Output": name,
                "Status": (
                    "AVAILABLE"
                    if path.exists()
                    else "NOT AVAILABLE"
                ),
                "Path": str(path.relative_to(BASE_DIR)),
            }
        )

    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True
    )

    panel_end()


# ============================================================
# INVESTIGATION GRAPH
# ============================================================

def page_graph():

    st.header("Investigation Graph")

    st.caption(
        "Explore the evidence-linked network reconstructed from the active case."
    )

    graph = graph_to_networkx()

    summary = graph_summary_from_networkx(graph)

    cols = st.columns(4)

    with cols[0]:
        metric_card(
            "Entities",
            format_number(summary["nodes"])
        )

    with cols[1]:
        metric_card(
            "Relationships",
            format_number(summary["edges"])
        )

    with cols[2]:
        metric_card(
            "Components",
            format_number(summary["components"])
        )

    with cols[3]:
        metric_card(
            "Graph type",
            "MultiDiGraph",
            "Directed evidence graph"
        )

    if graph.number_of_nodes() == 0:
        st.warning(
            "Investigation graph is not available yet. "
            "Run Evidence Processing."
        )
        return

    st.markdown("")

    panel_start(
        "Graph explorer",
        "Use entity search to focus the investigation."
    )

    search = st.text_input(
        "Search entity",
        placeholder="Phone, account, IMEI, tower or entity ID"
    )

    selected_nodes = []

    if search:

        query = search.lower()

        for node_id in graph.nodes:

            label = node_display_name(
                graph,
                node_id
            )

            if (
                query in str(node_id).lower()
                or query in str(label).lower()
            ):
                selected_nodes.append(node_id)

    if selected_nodes:

        st.success(
            f"{len(selected_nodes)} matching entities found."
        )

        selected = selected_nodes[0]

        st.markdown(
            f"""
            **Selected entity:** `{node_display_name(graph, selected)}`
            """
        )

        neighbors = list(
            graph.successors(selected)
        ) + list(
            graph.predecessors(selected)
        )

        neighbors = list(
            dict.fromkeys(neighbors)
        )

        rows = []

        for neighbor in neighbors[:100]:

            direction = (
                "OUTGOING"
                if graph.has_edge(selected, neighbor)
                else "INCOMING"
            )

            rows.append(
                {
                    "Direction": direction,
                    "Entity": node_display_name(
                        graph,
                        neighbor
                    ),
                    "Type": node_type(
                        graph,
                        neighbor
                    ),
                }
            )

        if rows:

            st.dataframe(
                pd.DataFrame(rows),
                use_container_width=True,
                hide_index=True,
            )

    panel_end()

    # --------------------------------------------------------
    # EXISTING PYVIS VISUALIZATION
    # --------------------------------------------------------

    html_file = GRAPH_DIR / "investigation_graph.html"

    if html_file.exists():

        st.markdown(
            "### Network visualization"
        )

        st.info(
            "For large graphs, use the entity search above to identify "
            "a relevant investigation pivot before interpreting connections."
        )

        try:

            from streamlit.components.v1 import iframe

            iframe(
                str(
                    html_file.resolve().as_uri()
                ),
                height=720,
                scrolling=True,
            )

        except Exception as exc:

            st.error(
                f"Unable to render graph visualization: {exc}"
            )

            st.code(
                str(html_file)
            )

    else:

        st.warning(
            "PyVis graph HTML is not available. "
            "Run the Phase 3 graph visualization script if required."
        )


# ============================================================
# MULE EVALUATION
# ============================================================

def page_mule_evaluation():

    st.header("Mule Evaluation")

    st.caption(
        "Evaluate account and communication patterns using the existing Phase 4 model."
    )

    predictions = load_predictions()

    if isinstance(predictions, dict):

        records = (
            predictions.get("predictions")
            or predictions.get("results")
            or predictions.get("data")
            or []
        )

    elif isinstance(predictions, list):

        records = predictions

    else:

        records = []

    if not records:

        st.warning(
            "No pattern predictions are available. "
            "Run Evidence Processing first."
        )
        return

    df = pd.DataFrame(records)

    st.subheader("Pattern evaluation output")

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("---")

    st.subheader(
        "Investigator interpretation"
    )

    st.markdown(
        """
        The model output is an analytical aid. A predicted pattern does not,
        by itself, establish that an account holder knowingly participated in
        fraud.

        Investigator validation should consider:

        - transaction chronology
        - communication relationships
        - device reuse
        - tower/location evidence
        - account ownership
        - complaint records
        - conflicting or missing evidence
        - legitimate explanations for shared infrastructure
        """
    )

    panel_start(
        "Evidence classification",
        "Separate what was recorded from what was derived."
    )

    st.markdown(
        f"""
        {evidence_label("OBSERVED")}
        Transaction, telephone, device and complaint records.

        <br>

        {evidence_label("DERIVED")}
        Network relationships and statistical features.

        <br>

        {evidence_label("ANALYTICAL INFERENCE")}
        Fraud-pattern interpretation requiring investigator review.
        """,
        unsafe_allow_html=True
    )

    panel_end()


# ============================================================
# POTENTIAL COORDINATION NODE
# ============================================================

def page_coordination_node():

    st.header("Potential Coordination / Consolidation Node")

    st.caption(
        "Identify highly connected entities as investigation pivots. "
        "This view does not determine guilt or automatically designate a kingpin."
    )

    graph = graph_to_networkx()

    if graph.number_of_nodes() == 0:

        st.warning(
            "Graph unavailable."
        )

        return

    degree_values = dict(
        graph.degree()
    )

    top_nodes = sorted(
        degree_values.items(),
        key=lambda x: x[1],
        reverse=True
    )[:25]

    rows = []

    for node_id, degree in top_nodes:

        rows.append(
            {
                "Entity": node_display_name(
                    graph,
                    node_id
                ),
                "Type": node_type(
                    graph,
                    node_id
                ),
                "Connections": degree,
                "Entity ID": node_id,
            }
        )

    df = pd.DataFrame(rows)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown(
        """
        ### How to interpret this view

        High connectivity can indicate that an entity is useful for further
        investigation. Depending on the evidence, it may represent a shared
        device, communication hub, transaction consolidation point, legitimate
        service relationship, or another structural feature.

        The system therefore presents these entities as **potential
        coordination/consolidation nodes**, not as automatically identified
        offenders.
        """
    )

    if not df.empty:

        selected_label = st.selectbox(
            "Select an investigation pivot",
            df["Entity"].tolist()
        )

        selected_row = df[
            df["Entity"] == selected_label
        ].iloc[0]

        node_id = selected_row["Entity ID"]

        st.markdown(
            f"""
            <div class="finding">
                <div class="finding-title">
                    Investigation pivot
                </div>

                <div class="finding-text">
                    Entity: <b>{selected_label}</b><br>
                    Type: <b>{selected_row["Type"]}</b><br>
                    Connections: <b>{selected_row["Connections"]}</b><br>
                    Classification:
                    {badge("ANALYTICAL INFERENCE", "purple")}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        neighbors = list(
            graph.neighbors(node_id)
        )

        st.write(
            f"Connected entities: {len(neighbors)}"
        )

        if neighbors:

            neighbor_rows = []

            for n in neighbors[:100]:

                neighbor_rows.append(
                    {
                        "Entity": node_display_name(
                            graph,
                            n
                        ),
                        "Type": node_type(
                            graph,
                            n
                        ),
                        "Entity ID": n,
                    }
                )

            st.dataframe(
                pd.DataFrame(neighbor_rows),
                use_container_width=True,
                hide_index=True,
            )


# ============================================================
# IMEI INVESTIGATION
# ============================================================

def page_imei():

    st.header("IMEI Investigation")

    st.caption(
        "Trace device identifiers across phone and evidence records."
    )

    devices = load_devices()

    if devices.empty:

        st.warning(
            "No device records are currently available."
        )

        return

    required = [
        col
        for col in [
            "phone_number",
            "imei",
            "device_type",
            "tower_id",
            "first_seen",
            "last_seen",
        ]
        if col in devices.columns
    ]

    if not required:

        st.warning(
            "Device schema could not be recognized."
        )

        return

    imei_counts = (
        devices
        .groupby("imei", dropna=False)
        .agg(
            phone_count=(
                "phone_number",
                "nunique"
            ),
            record_count=(
                "imei",
                "size"
            ),
        )
        .reset_index()
        .sort_values(
            "phone_count",
            ascending=False
        )
    )

    st.subheader(
        "IMEIs associated with multiple phone numbers"
    )

    shared = imei_counts[
        imei_counts["phone_count"] > 1
    ]

    if shared.empty:

        st.info(
            "No shared IMEI across multiple phone numbers was detected "
            "in the current device dataset."
        )

    else:

        st.dataframe(
            shared,
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("---")

    selected_imei = st.text_input(
        "Investigate IMEI",
        placeholder="Enter IMEI"
    )

    if selected_imei:

        selected_imei = selected_imei.strip()

        result = devices[
            devices["imei"].astype(str)
            == selected_imei
        ]

        if result.empty:

            st.warning(
                "No device record found for this IMEI."
            )

        else:

            st.success(
                f"{len(result)} evidence records found."
            )

            st.dataframe(
                result[
                    required
                ],
                use_container_width=True,
                hide_index=True,
            )

            st.markdown(
                f"""
                {evidence_label("OBSERVED")}
                The table above shows records directly associated
                with the supplied IMEI.
                """,
                unsafe_allow_html=True,
            )


# ============================================================
# LOCATION / TOWER
# ============================================================

def page_location():

    st.header("Location / Tower Investigation")

    st.caption(
        "Use tower identifiers as evidence-linked infrastructure pivots."
    )

    devices = load_devices()
    cdr = load_cdr()

    tower_frames = []

    if "tower_id" in devices.columns:

        tower_frames.append(
            devices[
                [
                    c
                    for c in [
                        "tower_id",
                        "phone_number",
                        "imei",
                        "first_seen",
                        "last_seen",
                    ]
                    if c in devices.columns
                ]
            ].copy()
        )

    if "tower_id" in cdr.columns:

        tower_frames.append(
            cdr[
                [
                    c
                    for c in [
                        "tower_id",
                        "caller",
                        "called",
                        "imei",
                        "timestamp",
                    ]
                    if c in cdr.columns
                ]
            ].copy()
        )

    if not tower_frames:

        st.warning(
            "No tower information is available."
        )

        return

    all_towers = pd.concat(
        tower_frames,
        ignore_index=True
    )

    if "tower_id" not in all_towers.columns:

        st.warning(
            "Tower identifier could not be resolved."
        )

        return

    tower_counts = (
        all_towers
        .groupby("tower_id", dropna=False)
        .size()
        .reset_index(name="evidence_records")
        .sort_values(
            "evidence_records",
            ascending=False
        )
    )

    st.subheader(
        "Tower evidence distribution"
    )

    st.dataframe(
        tower_counts.head(50),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("---")

    selected_tower = st.selectbox(
        "Select tower",
        tower_counts["tower_id"].astype(str).tolist()
    )

    if selected_tower:

        result = all_towers[
            all_towers["tower_id"].astype(str)
            == str(selected_tower)
        ]

        st.subheader(
            f"Evidence for tower {selected_tower}"
        )

        st.dataframe(
            result,
            use_container_width=True,
            hide_index=True,
        )

        st.info(
            "Tower co-occurrence is an investigative pivot. "
            "It does not independently establish that two people "
            "were together or involved in the same offence."
        )


# ============================================================
# EDGE CASE ANALYSIS
# ============================================================

def page_edge_cases():

    st.header("Edge Case Analysis")

    st.caption(
        "Stress-test the investigation against alternative explanations "
        "and incomplete evidence."
    )

    edge_cases = [
        (
            "Burned / inactive SIM",
            "A phone number may stop appearing while the device or related account remains active.",
            "Pivot through IMEI, account and historical evidence."
        ),
        (
            "Closed account",
            "A transaction destination may no longer be operational.",
            "Preserve historical transactions and ownership evidence."
        ),
        (
            "Shared device",
            "Multiple phone numbers may appear against one device identifier.",
            "Determine whether reuse is suspicious, legitimate or unresolved."
        ),
        (
            "Shared tower",
            "Multiple entities may appear through the same tower.",
            "Treat tower overlap as contextual evidence, not direct association."
        ),
        (
            "Disposable identity",
            "A short-lived identifier can create a false endpoint.",
            "Follow infrastructure and transaction pivots."
        ),
        (
            "Innocent mule / mixed network",
            "A transaction relationship may have a legitimate explanation.",
            "Check ownership, communications, chronology and context."
        ),
        (
            "Missing evidence",
            "Absence of a record should not be interpreted as absence of an event.",
            "Mark the relationship as unresolved."
        ),
        (
            "Conflicting records",
            "Different sources can contain inconsistent timestamps or identifiers.",
            "Preserve both sources and flag the conflict."
        ),
        (
            "Graph explosion",
            "Large datasets can produce thousands of weak relationships.",
            "Focus on evidence-backed pivots and temporal windows."
        ),
        (
            "Multiple fraud patterns",
            "One investigation can contain more than one structural pattern.",
            "Compare patterns rather than forcing a single classification."
        ),
    ]

    rows = []

    for title, issue, response in edge_cases:

        rows.append(
            {
                "Edge case": title,
                "Risk": issue,
                "Investigation response": response,
            }
        )

    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("---")

    st.subheader(
        "Current dataset checks"
    )

    tx = load_transactions()
    cdr = load_cdr()
    devices = load_devices()
    complaints = load_complaints()

    checks = []

    # Missing transaction amounts
    amount_col = transaction_amount_column(tx)

    if amount_col:

        missing_amount = tx[
            amount_col
        ].isna().sum()

        checks.append(
            {
                "Check": "Missing transaction amounts",
                "Count": int(missing_amount),
                "Status": (
                    "REVIEW"
                    if missing_amount
                    else "PASS"
                ),
            }
        )

    # Missing IMEI
    if "imei" in devices.columns:

        missing_imei = (
            devices["imei"]
            .isna()
            .sum()
        )

        checks.append(
            {
                "Check": "Missing IMEI values",
                "Count": int(missing_imei),
                "Status": (
                    "REVIEW"
                    if missing_imei
                    else "PASS"
                ),
            }
        )

    # Missing towers
    for source_name, df in [
        ("CDR", cdr),
        ("Device", devices)
    ]:

        if "tower_id" in df.columns:

            missing_tower = (
                df["tower_id"]
                .isna()
                .sum()
            )

            checks.append(
                {
                    "Check": f"Missing tower values ({source_name})",
                    "Count": int(missing_tower),
                    "Status": (
                        "REVIEW"
                        if missing_tower
                        else "PASS"
                    ),
                }
            )

    # Empty complaints
    checks.append(
        {
            "Check": "Complaint records available",
            "Count": len(complaints),
            "Status": (
                "PASS"
                if len(complaints)
                else "REVIEW"
            ),
        }
    )

    if checks:

        st.dataframe(
            pd.DataFrame(checks),
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# EXPLAIN CONNECTION
# ============================================================

def page_explain_connection():

    st.header("Explain This Connection")

    st.caption(
        "Every important relationship should be traceable back to evidence."
    )

    graph = graph_to_networkx()

    if graph.number_of_nodes() == 0:

        st.warning(
            "Graph is not available."
        )

        return

    all_labels = []

    for node_id in graph.nodes:

        all_labels.append(
            {
                "label": str(
                    node_display_name(
                        graph,
                        node_id
                    )
                ),
                "id": node_id,
            }
        )

    labels = sorted(
        all_labels,
        key=lambda x: x["label"]
    )

    source_label = st.selectbox(
        "Source entity",
        [
            item["label"]
            for item in labels
        ],
        key="explain_source"
    )

    source_id = next(
        item["id"]
        for item in labels
        if item["label"] == source_label
    )

    neighbors = list(
        graph.successors(source_id)
    )

    if not neighbors:

        st.info(
            "No outgoing connections were found."
        )

        return

    target_options = []

    for node_id in neighbors:

        target_options.append(
            {
                "label": node_display_name(
                    graph,
                    node_id
                ),
                "id": node_id,
            }
        )

    target_label = st.selectbox(
        "Target entity",
        [
            item["label"]
            for item in target_options
        ],
        key="explain_target"
    )

    target_id = next(
        item["id"]
        for item in target_options
        if item["label"] == target_label
    )

    relationship_options = []

    if graph.has_edge(
        source_id,
        target_id
    ):

        edge_data = graph.get_edge_data(
            source_id,
            target_id
        )

        if edge_data:

            for key, attrs in edge_data.items():

                relationship_options.append(
                    (
                        key,
                        attrs
                    )
                )

    if not relationship_options:

        st.warning(
            "No relationship details found."
        )

        return

    relationship_index = st.selectbox(
        "Relationship",
        list(
            range(
                len(relationship_options)
            )
        ),
        format_func=lambda x:
        str(
            relationship_options[x][1].get(
                "relationship",
                relationship_options[x][0]
            )
        )
    )

    _, attrs = relationship_options[
        relationship_index
    ]

    st.markdown("---")

    relationship = attrs.get(
        "relationship",
        "UNKNOWN"
    )

    evidence_id = attrs.get(
        "evidence_id",
        "UNKNOWN"
    )

    timestamp = attrs.get(
        "timestamp",
        "UNKNOWN"
    )

    status = attrs.get(
        "evidence_status",
        "OBSERVED"
    )

    st.markdown(
        f"""
        <div class="finding finding-green">

            <div class="finding-title">
                {node_display_name(graph, source_id)}
                →
                {node_display_name(graph, target_id)}
            </div>

            <div class="finding-text">

                Relationship:
                <b>{relationship}</b>
                <br>

                Evidence ID:
                <span class="evidence-id">
                    {evidence_id}
                </span>
                <br>

                Timestamp:
                <b>{timestamp}</b>
                <br>

                Status:
                {evidence_label(status)}

            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader(
        "Evidence properties"
    )

    st.json(
        attrs
    )

    st.info(
        "This panel explains the recorded graph relationship. "
        "It should be used to distinguish direct evidence from analytical interpretation."
    )


# ============================================================
# INVESTIGATION COPILOT
# ============================================================

def page_copilot():

    st.header("Investigation Copilot")

    st.caption(
        "Natural-language access to the existing evidence graph and investigation queries."
    )

    if load_graph is None or process_question is None:

        st.error(
            "Copilot backend could not be imported."
        )

        return

    try:

        graph = load_graph()

    except Exception as exc:

        st.error(
            f"Unable to load investigation graph: {exc}"
        )

        return

    if not graph:

        st.warning(
            "No investigation graph is available."
        )

        return

    st.markdown(
        """
        Ask questions such as:

        - How many entities are in the graph?
        - Show cumulative loss
        - Show transactions for ACC-MULTIDAY-VICTIM-001
        - Who received the money?
        - What was the largest transaction?
        - Show complaint information
        - Show detection delay
        - Show shared devices
        - Show shared towers
        - Show high value transactions
        - Find +919800000101
        - Show connections for +919800000101
        """,
    )

    question = st.text_input(
        "Investigation question",
        placeholder="Ask about the current investigation..."
    )

    if st.button(
        "🔎 Investigate",
        type="primary"
    ):

        if not question.strip():

            st.warning(
                "Enter an investigation question."
            )

            return

        try:

            result = process_question(
                graph,
                question
            )

            if not isinstance(result, dict):

                st.write(result)
                return

            category = result.get(
                "type",
                result.get(
                    "category",
                    "INVESTIGATION_RESULT"
                )
            )

            st.markdown(
                f"""
                {badge(str(category), "blue")}
                """,
                unsafe_allow_html=True
            )

            answer = result.get(
                "answer"
            )

            if answer:

                st.markdown(
                    f"""
                    <div class="finding">
                        <div class="finding-title">
                            Investigation result
                        </div>
                        <div class="finding-text">
                            {answer}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            data = result.get(
                "data"
            )

            if isinstance(data, dict):

                st.json(data)

            elif isinstance(data, list):

                if data:

                    st.dataframe(
                        pd.DataFrame(data),
                        use_container_width=True,
                        hide_index=True,
                    )

            elif data is not None:

                st.write(data)

        except Exception as exc:

            st.error(
                f"Copilot query failed: {exc}"
            )


# ============================================================
# TIMELINE
# ============================================================

def page_timeline():

    st.header("Investigation Timeline")

    st.caption(
        "Reconstruct events chronologically across the available evidence sources."
    )

    tx = load_transactions()
    cdr = load_cdr()
    complaints = load_complaints()

    timeline = []

    if not tx.empty and "timestamp" in tx.columns:

        for _, row in tx.iterrows():

            timeline.append(
                {
                    "Timestamp": row.get(
                        "timestamp",
                        ""
                    ),
                    "Source": "UPI",
                    "Event": "TRANSFERRED_FUNDS",
                    "Evidence ID": row.get(
                        "transaction_id",
                        ""
                    ),
                    "Details": (
                        f'{row.get("sender_account", "")} → '
                        f'{row.get("receiver_account", "")} '
                        f'INR {row.get("amount_inr", "")}'
                    ),
                }
            )

    if not cdr.empty and "timestamp" in cdr.columns:

        for _, row in cdr.iterrows():

            timeline.append(
                {
                    "Timestamp": row.get(
                        "timestamp",
                        ""
                    ),
                    "Source": "CDR",
                    "Event": "CALL",
                    "Evidence ID": row.get(
                        "record_id",
                        ""
                    ),
                    "Details": (
                        f'{row.get("caller", "")} → '
                        f'{row.get("called", "")}'
                    ),
                }
            )

    if (
        not complaints.empty
        and "complaint_timestamp"
        in complaints.columns
    ):

        for _, row in complaints.iterrows():

            timeline.append(
                {
                    "Timestamp": row.get(
                        "complaint_timestamp",
                        ""
                    ),
                    "Source": "COMPLAINT",
                    "Event": "COMPLAINT_REPORTED",
                    "Evidence ID": row.get(
                        "complaint_id",
                        ""
                    ),
                    "Details": (
                        f'Victim: {row.get("victim_name", "")}; '
                        f'Amount: {row.get("reported_amount_inr", "")}'
                    ),
                }
            )

    if not timeline:

        st.info(
            "No timeline evidence is available."
        )

        return

    timeline_df = pd.DataFrame(
        timeline
    )

    timeline_df["TimestampSort"] = pd.to_datetime(
        timeline_df["Timestamp"],
        errors="coerce"
    )

    timeline_df = (
        timeline_df
        .sort_values(
            "TimestampSort"
        )
        .drop(
            columns=["TimestampSort"]
        )
    )

    st.dataframe(
        timeline_df,
        use_container_width=True,
        hide_index=True,
    )

    st.download_button(
        "Download timeline CSV",
        timeline_df.to_csv(
            index=False
        ),
        file_name="investigation_timeline.csv",
        mime="text/csv"
    )


# ============================================================
# EVIDENCE EXPLORER
# ============================================================

def page_evidence():

    st.header("Evidence Explorer")

    st.caption(
        "Inspect the raw structured evidence that supports the graph."
    )

    tabs = st.tabs(
        [
            "UPI Transactions",
            "CDR",
            "Devices",
            "Complaints",
        ]
    )

    with tabs[0]:

        df = load_transactions()

        st.metric(
            "Transaction records",
            len(df)
        )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
        )

    with tabs[1]:

        df = load_cdr()

        st.metric(
            "CDR records",
            len(df)
        )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
        )

    with tabs[2]:

        df = load_devices()

        st.metric(
            "Device records",
            len(df)
        )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
        )

    with tabs[3]:

        df = load_complaints()

        st.metric(
            "Complaint records",
            len(df)
        )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# FINAL CASE BRIEF
# ============================================================

def page_case_brief():

    st.header("Final Case Brief")

    st.caption(
        "Evidence-linked investigation summary generated by the existing backend."
    )

    brief = load_case_brief()

    if brief:

        if isinstance(brief, dict):

            st.json(
                brief
            )

        elif isinstance(brief, list):

            st.dataframe(
                pd.DataFrame(brief),
                use_container_width=True,
                hide_index=True,
            )

    else:

        st.warning(
            "Structured case brief is not available."
        )

    text = safe_read_text(
        CASE_BRIEF_TEXT
    )

    if text:

        st.markdown("---")

        st.subheader(
            "Readable case brief"
        )

        st.text_area(
            "Case brief",
            value=text,
            height=600,
        )

        st.download_button(
            "Download Case Brief",
            data=text,
            file_name="chanakya_graph_case_brief.txt",
            mime="text/plain",
        )

    st.markdown("---")

    panel_start(
        "Investigator validation checklist",
        "Before relying on an analytical finding, validate the underlying evidence."
    )

    checklist = [
        "Confirm source file and evidence ID.",
        "Confirm timestamp and chronology.",
        "Confirm identifier normalization.",
        "Check whether the relationship is OBSERVED or DERIVED.",
        "Review alternative explanations.",
        "Review missing or conflicting records.",
        "Validate account/device ownership independently.",
        "Avoid treating model output as proof of wrongdoing.",
    ]

    for item in checklist:

        st.checkbox(
            item,
            key=f"brief_check_{item}"
        )

    panel_end()


# ============================================================
# PAGE ROUTER
# ============================================================

def main():

    render_header()

    page = render_sidebar()

    if page == "Command Center":

        page_command_center()

    elif page == "Case Intake":

        page_case_intake()

    elif page == "Evidence Processing":

        page_evidence_processing()

    elif page == "Investigation Graph":

        page_graph()

    elif page == "Mule Evaluation":

        page_mule_evaluation()

    elif page == "Potential Coordination Node":

        page_coordination_node()

    elif page == "IMEI Investigation":

        page_imei()

    elif page == "Location / Tower Investigation":

        page_location()

    elif page == "Edge Case Analysis":

        page_edge_cases()

    elif page == "Explain Connection":

        page_explain_connection()

    elif page == "Investigation Copilot":

        page_copilot()

    elif page == "Timeline":

        page_timeline()

    elif page == "Evidence Explorer":

        page_evidence()

    elif page == "Final Case Brief":

        page_case_brief()

    else:

        page_command_center()


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":
    main()