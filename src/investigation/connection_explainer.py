import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

GRAPH_PATH = PROJECT_ROOT / "src" / "output" / "graph" / "investigation_graph.json"


def load_graph():
    with open(GRAPH_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_value(value):
    return str(value).strip().lower()


def find_entity(graph_data, query):
    """
    Resolve a human-readable value such as:
        +919800000101
        356789012345678
        ACC-MULE-201

    to the canonical graph node ID.
    """

    query_normalized = normalize_value(query)

    nodes = graph_data.get("nodes", [])

    for node in nodes:
        node_id = str(
            node.get("id", node.get("node_id", ""))
        )

        if normalize_value(node_id) == query_normalized:
            return node

        properties = node.get("properties", {})
        if not isinstance(properties, dict):
            properties = {}

        candidates = [
            node.get("label"),
            node.get("name"),
            node.get("value"),
            properties.get("value"),
            properties.get("phone"),
            properties.get("phone_number"),
            properties.get("account"),
            properties.get("account_number"),
            properties.get("imei"),
            properties.get("tower_id"),
        ]

        for candidate in candidates:
            if candidate is not None:
                if normalize_value(candidate) == query_normalized:
                    return node

    return None


def explain_connection(source_query, target_query):
    graph_data = load_graph()

    source_node = find_entity(graph_data, source_query)

    if source_node is None:
        raise ValueError(
            f"Source entity not found: {source_query}"
        )

    target_node = find_entity(graph_data, target_query)

    if target_node is None:
        raise ValueError(
            f"Target entity not found: {target_query}"
        )

    source_id = str(
        source_node.get("id", source_node.get("node_id"))
    )

    target_id = str(
        target_node.get("id", target_node.get("node_id"))
    )

    edges = graph_data.get("edges", [])

    matching_edges = []

    for edge in edges:
        edge_source = str(
            edge.get("source", edge.get("from", ""))
        )

        edge_target = str(
            edge.get("target", edge.get("to", ""))
        )

        if (
            edge_source == source_id
            and edge_target == target_id
        ):
            matching_edges.append(edge)

    if not matching_edges:
        raise ValueError(
            f"No connection found between "
            f"{source_query} -> {target_query}"
        )

    explanations = []

    for edge in matching_edges:

        relationship = edge.get(
            "relationship",
            edge.get("type", "UNKNOWN")
        )

        evidence_id = edge.get(
            "evidence_id",
            edge.get("record_id", "UNKNOWN")
        )

        timestamp = edge.get(
            "timestamp",
            "UNKNOWN"
        )

        evidence_status = edge.get(
            "evidence_status",
            "OBSERVED"
        )

        amount = edge.get(
            "amount_inr",
            edge.get("amount")
        )

        properties = edge.get(
            "properties",
            {}
        )

        explanation = {
            "source": source_id,
            "source_label": source_node.get(
                "label",
                source_query
            ),
            "source_type": source_node.get(
                "type",
                "UNKNOWN"
            ),
            "target": target_id,
            "target_label": target_node.get(
                "label",
                target_query
            ),
            "target_type": target_node.get(
                "type",
                "UNKNOWN"
            ),
            "relationship": relationship,
            "evidence_id": evidence_id,
            "timestamp": timestamp,
            "evidence_status": evidence_status,
            "amount_inr": amount,
            "properties": properties,
            "human_explanation": (
                f"{source_query} is connected to "
                f"{target_query} through the "
                f"{relationship} relationship. "
                f"This connection is supported by "
                f"evidence record {evidence_id}."
            ),
        }

        explanations.append(explanation)

    return explanations