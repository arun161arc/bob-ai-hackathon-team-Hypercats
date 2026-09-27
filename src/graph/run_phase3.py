import json
import os
import sys


CURRENT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

SRC_DIR = os.path.dirname(
    CURRENT_DIR
)

if SRC_DIR not in sys.path:
    sys.path.insert(
        0,
        SRC_DIR
    )


from graph.graph_builder import (
    InvestigationGraphBuilder,
    load_csv
)

from graph.graph_analyzer import (
    GraphAnalyzer
)


# ---------------------------------------------------------
# PATHS
# ---------------------------------------------------------

DATA_DIR = os.path.join(
    SRC_DIR,
    "data"
)

ENTITY_DIR = os.path.join(
    SRC_DIR,
    "output",
    "entities"
)

GRAPH_DIR = os.path.join(
    SRC_DIR,
    "output",
    "graph"
)

os.makedirs(
    GRAPH_DIR,
    exist_ok=True
)


# ---------------------------------------------------------
# FILES
# ---------------------------------------------------------

CANONICAL_ENTITIES = os.path.join(
    ENTITY_DIR,
    "canonical_entities.json"
)

FILES = {

    "CDR":
        "cdr_records.csv",

    "UPI":
        "upi_transactions.csv",

    "COMPLAINT":
        "complaints.csv",

    "DEVICE":
        "device_records.csv"
}


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():

    print()
    print("=" * 70)
    print(
        "CHANAKYA-GRAPH — PHASE 3"
    )
    print(
        "INVESTIGATION GRAPH CONSTRUCTION"
    )
    print("=" * 70)

    # -----------------------------------------------------
    # CHECK PHASE 2
    # -----------------------------------------------------

    if not os.path.exists(
        CANONICAL_ENTITIES
    ):

        print()
        print(
            "[ERROR] Phase 2 output not found."
        )

        print(
            f"Expected:"
        )

        print(
            CANONICAL_ENTITIES
        )

        print()
        print(
            "Run Phase 2 first:"
        )

        print(
            "python src/entity/run_phase2.py"
        )

        return

    # -----------------------------------------------------
    # CREATE GRAPH
    # -----------------------------------------------------

    builder = InvestigationGraphBuilder()

    print()
    print(
        "[1/5] Loading canonical entities..."
    )

    builder.load_entities(
        CANONICAL_ENTITIES
    )

    print(
        f"      Nodes loaded: "
        f"{builder.graph.number_of_nodes()}"
    )

    # -----------------------------------------------------
    # PROCESS EVIDENCE
    # -----------------------------------------------------

    print()
    print(
        "[2/5] Building relationships..."
    )

    for evidence_type, filename in (
        FILES.items()
    ):

        path = os.path.join(
            DATA_DIR,
            filename
        )

        if not os.path.exists(path):

            print(
                f"      [WARNING] Missing "
                f"{filename}"
            )

            continue

        records = load_csv(
            path
        )

        print(
            f"      {evidence_type}: "
            f"{len(records)} records"
        )

        if evidence_type == "CDR":

            builder.process_cdr(
                records
            )

        elif evidence_type == "UPI":

            builder.process_upi(
                records
            )

        elif evidence_type == "DEVICE":

            builder.process_device(
                records
            )

        elif evidence_type == "COMPLAINT":

            builder.process_complaints(
                records
            )

    # -----------------------------------------------------
    # SAVE GRAPH
    # -----------------------------------------------------

    print()
    print(
        "[3/5] Saving investigation graph..."
    )

    graph_file = os.path.join(
        GRAPH_DIR,
        "investigation_graph.json"
    )

    builder.save_graph(
        graph_file
    )

    # -----------------------------------------------------
    # ANALYSIS
    # -----------------------------------------------------

    print()
    print(
        "[4/5] Running graph analysis..."
    )

    analyzer = GraphAnalyzer(
        builder.graph
    )

    degree = (
        analyzer.degree_centrality()
    )

    betweenness = (
        analyzer.betweenness_centrality()
    )

    summary = builder.summary()

    analysis = {

        "graph_summary":
            summary,

        "top_degree_nodes":
            analyzer.top_nodes(
                degree,
                10
            ),

        "top_betweenness_nodes":
            analyzer.top_nodes(
                betweenness,
                10
            ),

        "relationship_counts":
            analyzer.relationship_counts(),

        "multi_source_nodes":
            analyzer.multi_source_nodes(),

        "connected_components":
            len(
                analyzer.connected_components()
            )
    }

    analysis_file = os.path.join(
        GRAPH_DIR,
        "graph_analysis.json"
    )

    with open(
        analysis_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            analysis,
            file,
            indent=4,
            ensure_ascii=False
        )

    # -----------------------------------------------------
    # FINAL OUTPUT
    # -----------------------------------------------------

    print()
    print(
        "[5/5] Phase 3 completed."
    )

    print()
    print("=" * 70)
    print(
        "GRAPH SUMMARY"
    )
    print("=" * 70)

    print(
        f"Nodes : "
        f"{summary['nodes']}"
    )

    print(
        f"Edges : "
        f"{summary['edges']}"
    )

    print()
    print(
        "RELATIONSHIPS"
    )

    for relationship, count in (
        summary[
            "relationship_counts"
        ].items()
    ):

        print(
            f"{relationship:<30}"
            f": {count}"
        )

    print()
    print(
        "TOP CONNECTED ENTITIES"
    )

    for node, score in (
        analysis[
            "top_degree_nodes"
        ]
    ):

        data = builder.graph.nodes[
            node
        ]

        print(
            f"{data.get('entity_type'):<15}"
            f"{data.get('label'):<25}"
            f"{score:.4f}"
        )

    print()
    print(
        "OUTPUT FILES"
    )

    print(
        graph_file
    )

    print(
        analysis_file
    )

    print()
    print("=" * 70)
    print(
        "PHASE 3 GRAPH CONSTRUCTION SUCCESSFUL"
    )
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()