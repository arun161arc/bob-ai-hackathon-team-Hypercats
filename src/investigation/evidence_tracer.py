import os
import json


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

GRAPH_FILE = os.path.join(
    BASE_DIR,
    "output",
    "graph",
    "investigation_graph.json"
)


def load_graph():

    if not os.path.exists(
        GRAPH_FILE
    ):

        raise FileNotFoundError(
            f"Graph file not found:\n"
            f"{GRAPH_FILE}"
        )

    with open(
        GRAPH_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


def get_entity_evidence(entity_id):

    data = load_graph()

    for node in data.get(
        "nodes",
        []
    ):

        if node.get("id") == entity_id:

            return {
                "entity_id": entity_id,
                "entity_type": node.get(
                    "entity_type",
                    "UNKNOWN"
                ),
                "canonical_value": node.get(
                    "canonical_value",
                    ""
                ),
                "evidence_ids": node.get(
                    "evidence_ids",
                    []
                )
            }

    return None


def get_entity_connections(entity_id):

    data = load_graph()

    connections = []

    for edge in data.get(
        "edges",
        []
    ):

        source = edge.get(
            "source"
        )

        target = edge.get(
            "target"
        )

        if (
            source == entity_id
            or target == entity_id
        ):

            connections.append({
                "source": source,
                "target": target,
                "relationship": edge.get(
                    "relationship",
                    "UNKNOWN"
                ),
                "evidence_id": edge.get(
                    "evidence_id",
                    "N/A"
                ),
                "timestamp": edge.get(
                    "timestamp",
                    "N/A"
                ),
                "amount_inr": edge.get(
                    "amount_inr",
                    None
                ),
                "evidence_status": edge.get(
                    "evidence_status",
                    "UNKNOWN"
                )
            })

    return connections