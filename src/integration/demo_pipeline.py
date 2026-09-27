import json
import shutil
import subprocess
import sys
from pathlib import Path

from src.integration.case_state import (
    get_active_case_id,
    invalidate_old_results,
)


# ============================================================
# PATHS
# ============================================================

SRC_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = SRC_DIR.parent

DATA_DIR = SRC_DIR / "data"
CASES_DIR = DATA_DIR / "cases"

OUTPUT_DIR = SRC_DIR / "output"

ACTIVE_CASE_FILE = CASES_DIR / "active_case.json"


# ============================================================
# REQUIRED FINAL OUTPUTS
# ============================================================

REQUIRED_OUTPUTS = [
    OUTPUT_DIR / "graph" / "investigation_graph.json",
    OUTPUT_DIR / "graph" / "graph_analysis.json",

    OUTPUT_DIR / "investigation" / "command_center.json",
    OUTPUT_DIR / "investigation" / "evidence_ledger.json",
    OUTPUT_DIR / "investigation" / "investigation_timeline.json",
    OUTPUT_DIR / "investigation" / "edge_case_intelligence.json",
    OUTPUT_DIR / "investigation" / "final_case_brief.json",
    OUTPUT_DIR / "investigation" / "phase16_case_brief.json",
]


# ============================================================
# CURRENT WORKING DATA FILES
#
# These are the files expected by the current legacy modules.
# The case manager now creates:
#
# case/
#   normalized/
#       cdr_records.csv
#       upi_transactions.csv
#       complaints.csv
#       device_records.csv
#
# ============================================================

WORKING_DATA_FILES = {
    "cdr": SRC_DIR / "data" / "cdr_records.csv",
    "upi": SRC_DIR / "data" / "upi_transactions.csv",
    "complaints": SRC_DIR / "data" / "complaints.csv",
    "devices": SRC_DIR / "data" / "device_records.csv",
}


# ============================================================
# LOAD ACTIVE CASE
# ============================================================

def load_active_case():
    """
    Load the active_case.json file created by case_manager.py.
    """

    if not ACTIVE_CASE_FILE.exists():
        return None

    try:
        with open(
            ACTIVE_CASE_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    except Exception:
        return None


# ============================================================
# GET ACTIVE CASE DIRECTORY
# ============================================================

def get_active_case_directory():
    """
    Return:

        src/data/cases/<CASE_ID>

    """

    active_case = load_active_case()

    if not active_case:
        return None

    case_id = active_case.get("case_id")

    if not case_id:
        return None

    case_dir = CASES_DIR / case_id

    if not case_dir.exists():
        return None

    return case_dir


# ============================================================
# CHECK ACTIVE CASE
# ============================================================

def check_active_case():
    """
    Verify that an active case exists and that its current
    normalized evidence files are present.
    """

    case_id = get_active_case_id()

    if not case_id:
        raise RuntimeError(
            "No active case is available. "
            "Upload and process all four evidence files first."
        )

    case_dir = CASES_DIR / case_id

    if not case_dir.exists():
        raise RuntimeError(
            f"Active case directory does not exist:\n{case_dir}"
        )

    # --------------------------------------------------------
    # CURRENT CASE STRUCTURE
    # --------------------------------------------------------

    normalized_dir = case_dir / "normalized"

    if not normalized_dir.exists():
        raise RuntimeError(
            "Normalized evidence directory does not exist:\n"
            f"{normalized_dir}"
        )

    required_files = [
        normalized_dir / "cdr_records.csv",
        normalized_dir / "upi_transactions.csv",
        normalized_dir / "complaints.csv",
        normalized_dir / "device_records.csv",
    ]

    missing = [
        str(path)
        for path in required_files
        if not path.exists()
    ]

    if missing:
        raise RuntimeError(
            "Missing normalized evidence files:\n"
            + "\n".join(missing)
        )

    # --------------------------------------------------------
    # CHECK THAT FILES ARE NOT EMPTY
    # --------------------------------------------------------

    empty_files = []

    for path in required_files:

        try:
            if path.stat().st_size == 0:
                empty_files.append(str(path))

        except Exception:
            empty_files.append(str(path))

    if empty_files:
        raise RuntimeError(
            "The following evidence files are empty:\n"
            + "\n".join(empty_files)
        )

    return case_id


# ============================================================
# ACTIVATE CURRENT CASE FOR EXISTING INVESTIGATION MODULES
# ============================================================

def activate_current_case_for_modules():
    """
    Copy the current case's normalized evidence files into
    src/data/.

    Existing investigation modules already expect the files
    inside src/data/, so this keeps those modules unchanged.
    """

    case_dir = get_active_case_directory()

    if case_dir is None:
        raise RuntimeError(
            "Active case directory could not be found."
        )

    normalized_dir = case_dir / "normalized"

    current_case_files = {
        "cdr": normalized_dir / "cdr_records.csv",
        "upi": normalized_dir / "upi_transactions.csv",
        "complaints": normalized_dir / "complaints.csv",
        "devices": normalized_dir / "device_records.csv",
    }

    for name, source in current_case_files.items():

        if not source.exists():
            raise FileNotFoundError(
                f"Missing normalized evidence file:\n{source}"
            )

        destination = WORKING_DATA_FILES[name]

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        shutil.copy2(
            source,
            destination,
        )

        print(
            f"Activated {name}: "
            f"{source.name}"
        )

    print()
    print(
        "CURRENT CASE ACTIVATED "
        "FOR INVESTIGATION MODULES"
    )


# ============================================================
# CLEAR PREVIOUS OUTPUTS
# ============================================================

def clear_previous_outputs():
    """
    Remove old generated investigation outputs.

    This prevents the new case from accidentally using
    results belonging to a previous case.
    """

    directories = [
        OUTPUT_DIR / "entities",
        OUTPUT_DIR / "graph",
        OUTPUT_DIR / "model",
        OUTPUT_DIR / "investigation",
    ]

    for directory in directories:

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        for item in directory.iterdir():

            try:

                if item.is_dir():
                    shutil.rmtree(item)

                else:
                    item.unlink()

            except Exception as exc:

                print(
                    f"WARNING: Could not remove "
                    f"{item}: {exc}"
                )

    print(
        "OLD INVESTIGATION OUTPUTS CLEARED"
    )


# ============================================================
# RUN PYTHON MODULE
# ============================================================

def run_module(module_name):
    """
    Run an investigation module using:

        python -m <module>

    """

    print()
    print("=" * 70)
    print(
        f"RUNNING MODULE: {module_name}"
    )
    print("=" * 70)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            module_name,
        ],
        cwd=str(PROJECT_DIR),
        capture_output=True,
        text=True,
    )

    if result.stdout:
        print(result.stdout)

    if result.stderr:
        print(result.stderr)

    if result.returncode != 0:

        raise RuntimeError(
            f"Module failed: {module_name}\n\n"
            f"Return code: {result.returncode}\n\n"
            f"STDOUT:\n"
            f"{result.stdout}\n\n"
            f"STDERR:\n"
            f"{result.stderr}"
        )

    print(
        f"{module_name} COMPLETED"
    )

    return True


# ============================================================
# STAMP CASE ID INTO OUTPUTS
# ============================================================

def stamp_output_case_id():
    """
    Add the active case ID to JSON-object outputs.

    Timeline may be a JSON list, so lists are deliberately
    left unchanged.
    """

    case_id = get_active_case_id()

    if not case_id:
        raise RuntimeError(
            "Cannot stamp outputs because "
            "active case ID is missing."
        )

    for output_file in REQUIRED_OUTPUTS:

        if not output_file.exists():
            continue

        try:

            with open(
                output_file,
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)

            # ------------------------------------------------
            # JSON OBJECT
            # ------------------------------------------------

            if isinstance(data, dict):

                data["case_id"] = case_id

                with open(
                    output_file,
                    "w",
                    encoding="utf-8",
                ) as file:

                    json.dump(
                        data,
                        file,
                        indent=2,
                        ensure_ascii=False,
                        default=str,
                    )

            # ------------------------------------------------
            # JSON LIST
            #
            # Example:
            # investigation_timeline.json
            #
            # Leave it unchanged.
            # ------------------------------------------------

            elif isinstance(data, list):

                print(
                    f"Preserving list output: "
                    f"{output_file.name}"
                )

        except Exception as exc:

            print(
                f"WARNING: Could not stamp "
                f"{output_file}: {exc}"
            )


# ============================================================
# VALIDATE OUTPUTS
# ============================================================

def validate_outputs():

    case_id = get_active_case_id()

    if not case_id:
        raise RuntimeError(
            "Active case ID is missing "
            "during output validation."
        )

    # --------------------------------------------------------
    # CHECK FILE EXISTENCE
    # --------------------------------------------------------

    missing = []

    for output_file in REQUIRED_OUTPUTS:

        if not output_file.exists():
            missing.append(
                str(output_file)
            )

    if missing:

        raise RuntimeError(
            "Required investigation outputs are missing:\n"
            + "\n".join(missing)
        )

    # --------------------------------------------------------
    # CHECK JSON VALIDITY
    # --------------------------------------------------------

    invalid_json_outputs = []

    invalid_case_outputs = []

    for output_file in REQUIRED_OUTPUTS:

        try:

            with open(
                output_file,
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)

            # ------------------------------------------------
            # JSON OBJECT
            # ------------------------------------------------

            if isinstance(data, dict):

                output_case_id = data.get(
                    "case_id"
                )

                if output_case_id != case_id:

                    invalid_case_outputs.append(
                        f"{output_file} "
                        f"-> case_id={output_case_id}"
                    )

            # ------------------------------------------------
            # JSON LIST
            #
            # Timeline is allowed to be a list.
            # ------------------------------------------------

            elif isinstance(data, list):

                print(
                    f"Validated JSON list: "
                    f"{output_file.name}"
                )

            else:

                invalid_json_outputs.append(
                    f"{output_file} "
                    f"does not contain a JSON "
                    f"object or list"
                )

        except Exception as exc:

            invalid_json_outputs.append(
                f"{output_file} -> {exc}"
            )

    # --------------------------------------------------------
    # INVALID JSON
    # --------------------------------------------------------

    if invalid_json_outputs:

        raise RuntimeError(
            "Invalid JSON outputs:\n"
            + "\n".join(
                invalid_json_outputs
            )
        )

    # --------------------------------------------------------
    # WRONG CASE ID
    # --------------------------------------------------------

    if invalid_case_outputs:

        raise RuntimeError(
            "Output case ID validation failed:\n"
            + "\n".join(
                invalid_case_outputs
            )
        )

    print(
        "ALL OUTPUTS VALIDATED"
    )

    print(
        f"CASE ID: {case_id}"
    )

    return True


# ============================================================
# COMPLETE INVESTIGATION PIPELINE
# ============================================================

def run_complete_investigation():

    print()
    print("=" * 80)
    print("CHANAKYA-GRAPH")
    print("COMPLETE INVESTIGATION PIPELINE")
    print("=" * 80)

    # ========================================================
    # STEP 1
    # ========================================================

    print()
    print(
        "[1/14] CHECKING ACTIVE CASE"
    )

    case_id = check_active_case()

    print(
        f"ACTIVE CASE: {case_id}"
    )

    # ========================================================
    # STEP 2
    # ========================================================

    print()
    print(
        "[2/14] INVALIDATING OLD RESULTS"
    )

    invalidate_old_results()

    # ========================================================
    # STEP 3
    # ========================================================

    print()
    print(
        "[3/14] CLEARING OLD OUTPUT FILES"
    )

    clear_previous_outputs()

    # ========================================================
    # STEP 4
    # ========================================================

    print()
    print(
        "[4/14] ACTIVATING CURRENT CASE"
    )

    activate_current_case_for_modules()

    # ========================================================
    # STEP 5
    # ENTITY EXTRACTION
    # ========================================================

    print()
    print(
        "[5/14] ENTITY EXTRACTION "
        "AND RESOLUTION"
    )

    run_module(
        "src.entity.run_phase2"
    )

    # ========================================================
    # STEP 6
    # GRAPH
    # ========================================================

    print()
    print(
        "[6/14] INVESTIGATION GRAPH"
    )

    run_module(
        "src.graph.run_phase3"
    )

    # IMPORTANT:
    # Immediately verify graph output before continuing.
    # This catches the Phase 2/Phase 3 dependency problem
    # instead of allowing later modules to produce empty data.

    graph_file = (
        OUTPUT_DIR
        / "graph"
        / "investigation_graph.json"
    )

    graph_analysis_file = (
        OUTPUT_DIR
        / "graph"
        / "graph_analysis.json"
    )

    if not graph_file.exists():
        raise RuntimeError(
            "Phase 3 completed without creating:\n"
            f"{graph_file}\n\n"
            "Phase 2 entity output may be missing or "
            "Phase 3 may have failed."
        )

    if not graph_analysis_file.exists():
        raise RuntimeError(
            "Phase 3 completed without creating:\n"
            f"{graph_analysis_file}"
        )

    # ========================================================
    # STEP 7
    # ML / FRAUD PATTERN ANALYSIS
    # ========================================================

    print()
    print(
        "[7/14] FRAUD PATTERN ANALYSIS"
    )

    run_module(
        "src.model.run_phase4"
    )

    # ========================================================
    # STEP 8
    # COMMAND CENTER
    # ========================================================

    print()
    print(
        "[8/14] INVESTIGATION COMMAND CENTER"
    )

    run_module(
        "src.investigation.command_center"
    )

    # ========================================================
    # STEP 9
    # EVIDENCE EXPLORER
    # ========================================================

    print()
    print(
        "[9/14] EVIDENCE EXPLORER"
    )

    run_module(
        "src.investigation.evidence_explorer"
    )

    # ========================================================
    # STEP 10
    # TIMELINE
    # ========================================================

    print()
    print(
        "[10/14] INVESTIGATION TIMELINE"
    )

    run_module(
        "src.investigation.timeline"
    )

    # ========================================================
    # STEP 11
    # EDGE CASE INTELLIGENCE
    # ========================================================

    print()
    print(
        "[11/14] EDGE CASE INTELLIGENCE"
    )

    run_module(
        "src.investigation.edge_case_intelligence"
    )

    # ========================================================
    # STEP 12
    # FINAL CASE BRIEF
    # ========================================================

    print()
    print(
        "[12/14] FINAL CASE BRIEF"
    )

    run_module(
        "src.investigation.final_case_brief"
    )

    # ========================================================
    # STEP 13
    # PHASE 16
    # ========================================================

    print()
    print(
        "[13/14] PHASE 16 — "
        "EVIDENCE-LINKED CASE BRIEF"
    )

    run_module(
        "src.investigation.phase16_evidence_linked_brief"
    )

    # ========================================================
    # STEP 14
    # VALIDATE EVERYTHING
    # ========================================================

    print()
    print(
        "[14/14] VALIDATING INVESTIGATION OUTPUTS"
    )

    stamp_output_case_id()

    validate_outputs()

    # ========================================================
    # SUCCESS
    # ========================================================

    print()
    print("=" * 80)
    print("CHANAKYA-GRAPH")
    print("COMPLETE INVESTIGATION PIPELINE SUCCESSFUL")
    print("=" * 80)

    print(
        f"CASE ID: {case_id}"
    )

    print()
    print(
        "AVAILABLE MODULES:"
    )

    print("  ✓ Command Center")
    print("  ✓ Investigation Graph")
    print("  ✓ Focused Investigation")
    print("  ✓ Evidence Explorer")
    print("  ✓ Timeline")
    print("  ✓ Investigation Copilot")
    print("  ✓ Edge Case Intelligence")
    print("  ✓ Final Evidence Brief")
    print("  ✓ Phase 16 Evidence-Linked Brief")

    print("=" * 80)

    return {
        "success": True,
        "case_id": case_id,
        "outputs": [
            str(path)
            for path in REQUIRED_OUTPUTS
        ],
    }


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    try:

        result = run_complete_investigation()

        print()

        print(
            json.dumps(
                result,
                indent=2,
                ensure_ascii=False,
            )
        )

    except Exception as exc:

        print()
        print("=" * 80)
        print(
            "COMPLETE INVESTIGATION PIPELINE FAILED"
        )
        print("=" * 80)

        print(str(exc))

        print("=" * 80)

        raise