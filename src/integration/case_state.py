import hashlib
import json
from pathlib import Path

import streamlit as st


# ============================================================
# PATHS
# ============================================================

SRC_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = SRC_DIR / "data"
CASES_DIR = DATA_DIR / "cases"
OUTPUT_DIR = SRC_DIR / "output"

STATE_FILE = CASES_DIR / "ui_case_state.json"
ACTIVE_CASE_FILE = CASES_DIR / "active_case.json"


# ============================================================
# RESULT FILES
# ============================================================

RESULT_FILES = [
    OUTPUT_DIR / "graph" / "investigation_graph.json",

    OUTPUT_DIR / "graph" / "graph_analysis.json",

    OUTPUT_DIR / "model" / "predictions.json",

    OUTPUT_DIR / "investigation" / "command_center.json",

    OUTPUT_DIR / "investigation" / "evidence_ledger.json",

    OUTPUT_DIR / "investigation" / "investigation_timeline.json",

    OUTPUT_DIR / "investigation" / "edge_case_intelligence.json",

    OUTPUT_DIR / "investigation" / "final_case_brief.json",

    OUTPUT_DIR / "investigation" / "final_case_brief.txt",

    OUTPUT_DIR / "investigation" /
    "phase16_evidence_linked_case_brief.json",

    OUTPUT_DIR / "investigation" /
    "phase16_evidence_linked_case_brief.txt",
]


# ============================================================
# DIRECTORIES
# ============================================================

def ensure_directories():
    CASES_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# SESSION STATE
# ============================================================

def initialize_session_state():

    defaults = {
        "case_state": "NO_CASE",
        "current_case_id": None,
        "uploaded_signature": None,
        "processing": False,
        "processing_error": None,
    }

    for key, value in defaults.items():

        if key not in st.session_state:
            st.session_state[key] = value


# ============================================================
# FILE HASH
# ============================================================

def uploaded_file_hash(uploaded_file):

    if uploaded_file is None:
        return None

    uploaded_file.seek(0)

    content = uploaded_file.read()

    uploaded_file.seek(0)

    return hashlib.sha256(content).hexdigest()


# ============================================================
# UPLOAD SIGNATURE
# ============================================================

def build_upload_signature(files):

    signature_data = {}

    for key, uploaded_file in files.items():

        if uploaded_file is None:
            signature_data[key] = None

        else:
            signature_data[key] = {
                "name": uploaded_file.name,
                "hash": uploaded_file_hash(uploaded_file),
                "size": uploaded_file.size,
            }

    raw = json.dumps(
        signature_data,
        sort_keys=True
    )

    return hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()


# ============================================================
# ACTIVE CASE
# ============================================================

def get_active_case():

    if not ACTIVE_CASE_FILE.exists():
        return {}

    try:

        with open(
            ACTIVE_CASE_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except Exception:

        return {}


def get_active_case_id():

    case = get_active_case()

    return (
        case.get("case_id")
        or case.get("active_case_id")
    )


# ============================================================
# STATE FILE
# ============================================================

def load_state():

    if not STATE_FILE.exists():
        return {}

    try:

        with open(
            STATE_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except Exception:

        return {}


def save_state(state):

    ensure_directories()

    with open(
        STATE_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            state,
            f,
            indent=2,
            ensure_ascii=False,
            default=str
        )


# ============================================================
# INVALIDATE OLD RESULTS
# ============================================================

def invalidate_old_results():

    for path in RESULT_FILES:

        try:

            if path.exists():
                path.unlink()

        except Exception as exc:

            print(
                f"WARNING: Could not remove {path}: {exc}"
            )


# ============================================================
# SET PENDING
# ============================================================

def set_pending(signature=None):

    initialize_session_state()

    st.session_state.case_state = "PENDING"

    st.session_state.current_case_id = None

    st.session_state.uploaded_signature = signature

    st.session_state.processing = False

    st.session_state.processing_error = None

    invalidate_old_results()

    save_state(
        {
            "state": "PENDING",
            "case_id": None,
            "upload_signature": signature,
        }
    )


# ============================================================
# SET PROCESSING
# ============================================================

def set_processing():

    initialize_session_state()

    st.session_state.case_state = "PROCESSING"

    st.session_state.processing = True

    st.session_state.processing_error = None

    save_state(
        {
            "state": "PROCESSING",
            "case_id": None,
            "upload_signature":
                st.session_state.uploaded_signature,
        }
    )


# ============================================================
# SET READY
# ============================================================

def set_ready(case_id, signature=None):

    initialize_session_state()

    st.session_state.case_state = "READY"

    st.session_state.current_case_id = case_id

    st.session_state.uploaded_signature = (
        signature
        or st.session_state.uploaded_signature
    )

    st.session_state.processing = False

    st.session_state.processing_error = None

    save_state(
        {
            "state": "READY",
            "case_id": case_id,
            "upload_signature":
                st.session_state.uploaded_signature,
        }
    )


# ============================================================
# SET FAILED
# ============================================================

def set_failed(error_message):

    initialize_session_state()

    st.session_state.case_state = "FAILED"

    st.session_state.current_case_id = None

    st.session_state.processing = False

    st.session_state.processing_error = str(
        error_message
    )

    save_state(
        {
            "state": "FAILED",
            "case_id": None,
            "upload_signature":
                st.session_state.uploaded_signature,
            "error": str(error_message),
        }
    )


# ============================================================
# REGISTER UPLOADS
# ============================================================

def register_uploads(files):

    initialize_session_state()

    signature = build_upload_signature(files)

    complete = all(
        uploaded_file is not None
        for uploaded_file in files.values()
    )

    if not complete:

        return {
            "complete": False,
            "signature": signature,
            "changed": False,
        }

    old_signature = (
        st.session_state.uploaded_signature
    )

    changed = (
        old_signature is not None
        and old_signature != signature
    )

    if changed:

        set_pending(signature)

    elif old_signature is None:

        st.session_state.uploaded_signature = signature

        st.session_state.case_state = "PENDING"

        save_state(
            {
                "state": "PENDING",
                "case_id": None,
                "upload_signature": signature,
            }
        )

    return {
        "complete": True,
        "signature": signature,
        "changed": changed,
    }


# ============================================================
# RESULT CASE ID
# ============================================================

def read_result_case_id(path):

    path = Path(path)

    if not path.exists():
        return None

    try:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        if not isinstance(data, dict):
            return None

        if "case_id" in data:
            return data["case_id"]

        case_information = data.get(
            "case_information",
            {}
        )

        if isinstance(case_information, dict):

            return case_information.get(
                "case_id"
            )

        return None

    except Exception:

        return None


# ============================================================
# RESULT VALIDATION
# ============================================================

def result_belongs_to_current_case(path):

    current_case_id = get_active_case_id()

    if not current_case_id:
        return False

    result_case_id = read_result_case_id(path)

    return (
        result_case_id == current_case_id
    )


# ============================================================
# REQUIRE READY CASE
# ============================================================

def require_ready_case():

    initialize_session_state()

    case_id = get_active_case_id()

    ready = (
        st.session_state.case_state == "READY"
        and case_id is not None
        and case_id ==
        st.session_state.current_case_id
    )

    if not ready:

        st.warning(
            "Upload and process a case first."
        )

        st.stop()

    return case_id


# ============================================================
# CURRENT STATE
# ============================================================

def get_ui_state():

    initialize_session_state()

    return {
        "state":
            st.session_state.case_state,

        "case_id":
            st.session_state.current_case_id,

        "signature":
            st.session_state.uploaded_signature,

        "processing":
            st.session_state.processing,

        "error":
            st.session_state.processing_error,
    }