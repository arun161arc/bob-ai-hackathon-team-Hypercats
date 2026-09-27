from __future__ import annotations

import json
from pathlib import Path
from collections import defaultdict, deque


# =========================================================
# PATH
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

GRAPH_PATH = (
    PROJECT_ROOT
    / "src"
    / "output"
    / "graph"
    / "investigation_graph.json"
)


# =========================================================
# LOAD GRAPH
# =========================================================

def load_graph_data():

    if not GRAPH_PATH.exists():
        raise FileNotFoundError(
            f"Graph file not found:\n{GRAPH_PATH}"
        )

    with open(
        GRAPH_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# =========================================================
# GET NODES
# =========================================================

def get_nodes(graph_data):

    raw_nodes = graph_data.get(
        "nodes",
        []
    )

    nodes = []

    for node in raw_nodes:

        if not isinstance(node, dict):
            continue

        node_id = (
            node.get("id")
            or node.get("entity_id")
            or node.get("key")
        )

        if node_id is None:
            continue

        label = (
            node.get("label")
            or node.get("value")
            or node.get("name")
            or node_id
        )

        entity_type = (
            node.get("entity_type")
            or node.get("type")
            or "UNKNOWN"
        )

        nodes.append(
            {
                "id": str(node_id),
                "label": str(label),
                "entity_type": str(entity_type),
                "properties": node.get(
                    "properties",
                    {}
                )
            }
        )

    return nodes


# =========================================================
# GET EDGES
# =========================================================

def get_edges(graph_data):

    raw_edges = graph_data.get(
        "edges"
    )

    if raw_edges is None:

        raw_edges = graph_data.get(
            "links",
            []
        )

    edges = []

    for index, edge in enumerate(
        raw_edges
    ):

        if not isinstance(edge, dict):
            continue

        source = edge.get(
            "source"
        )

        target = edge.get(
            "target"
        )

        if source is None or target is None:
            continue

        edges.append(
            {
                "edge_id": str(
                    edge.get("id")
                    or edge.get("edge_id")
                    or f"EDGE-{index + 1:06d}"
                ),

                "source": str(source),

                "target": str(target),

                "relationship": str(
                    edge.get("relationship")
                    or edge.get("type")
                    or "RELATED"
                ),

                "evidence_id": edge.get(
                    "evidence_id"
                ),

                "timestamp": edge.get(
                    "timestamp"
                ),

                "evidence_status": edge.get(
                    "evidence_status",
                    "OBSERVED"
                ),

                "amount_inr": edge.get(
                    "amount_inr",
                    edge.get(
                        "amount",
                        ""
                    )
                ),

                "properties": edge.get(
                    "properties",
                    {}
                )
            }
        )

    return edges


# =========================================================
# BUILD INDEX
# =========================================================

def build_indexes(graph_data):

    nodes = get_nodes(
        graph_data
    )

    edges = get_edges(
        graph_data
    )

    node_map = {
        node["id"]: node
        for node in nodes
    }

    adjacency = defaultdict(list)

    for edge in edges:

        source = edge["source"]
        target = edge["target"]

        adjacency[source].append(
            {
                "neighbor": target,
                "edge": edge
            }
        )

        adjacency[target].append(
            {
                "neighbor": source,
                "edge": edge
            }
        )

    return (
        nodes,
        edges,
        node_map,
        adjacency
    )


# =========================================================
# SEARCH ENTITIES
# =========================================================

def search_entities(
    graph_data,
    query,
    limit=30
):

    nodes = get_nodes(
        graph_data
    )

    query = (
        query or ""
    ).strip().lower()

    if not query:

        return nodes[:limit]

    matches = []

    for node in nodes:

        searchable = " ".join(
            [
                node["id"],
                node["label"],
                node["entity_type"]
            ]
        ).lower()

        if query in searchable:

            matches.append(
                node
            )

        if len(matches) >= limit:
            break

    return matches


# =========================================================
# FOCUSED NETWORK
# =========================================================

def get_focused_network(
    graph_data,
    center_id,
    depth=1,
    max_nodes=50,
    entity_type_filter=None
):

    (
        nodes,
        edges,
        node_map,
        adjacency
    ) = build_indexes(
        graph_data
    )

    center_id = str(
        center_id
    )

    if center_id not in node_map:

        return [], []

    allowed_types = (
        set(entity_type_filter)
        if entity_type_filter
        else None
    )

    visited = {
        center_id
    }

    queue = deque(
        [
            (
                center_id,
                0
            )
        ]
    )

    selected_edge_keys = set()

    # -----------------------------------------------------
    # BREADTH-FIRST SEARCH
    # -----------------------------------------------------

    while queue:

        current, current_depth = (
            queue.popleft()
        )

        if current_depth >= depth:
            continue

        neighbours = adjacency.get(
            current,
            []
        )

        for item in neighbours:

            neighbour = item[
                "neighbor"
            ]

            edge = item[
                "edge"
            ]

            neighbour_node = node_map.get(
                neighbour
            )

            if neighbour_node is None:
                continue

            # -------------------------------------------------
            # ENTITY FILTER
            # -------------------------------------------------

            if allowed_types:

                if (
                    neighbour_node[
                        "entity_type"
                    ]
                    not in allowed_types
                ):

                    continue

            # -------------------------------------------------
            # EDGE KEY
            # -------------------------------------------------

            edge_key = (
                edge["source"],
                edge["target"],
                edge["relationship"],
                edge.get("evidence_id")
            )

            selected_edge_keys.add(
                edge_key
            )

            # -------------------------------------------------
            # ADD NODE
            # -------------------------------------------------

            if neighbour not in visited:

                if len(visited) < max_nodes:

                    visited.add(
                        neighbour
                    )

                    queue.append(
                        (
                            neighbour,
                            current_depth + 1
                        )
                    )

    # =====================================================
    # NODES
    # =====================================================

    focused_nodes = [
        node_map[node_id]
        for node_id in visited
        if node_id in node_map
    ]

    # =====================================================
    # EDGES
    # =====================================================

    focused_edges = []

    for edge in edges:

        if (
            edge["source"] not in visited
            or
            edge["target"] not in visited
        ):
            continue

        edge_key = (
            edge["source"],
            edge["target"],
            edge["relationship"],
            edge.get("evidence_id")
        )

        if edge_key not in selected_edge_keys:
            continue

        focused_edges.append(
            edge
        )

    # =====================================================
    # KEEP FOCUS CONNECTIONS FIRST
    # =====================================================

    center_edges = []

    other_edges = []

    for edge in focused_edges:

        if (
            edge["source"] == center_id
            or
            edge["target"] == center_id
        ):

            center_edges.append(
                edge
            )

        else:

            other_edges.append(
                edge
            )

    # =====================================================
    # EDGE LIMIT
    # =====================================================

    max_edges = max(
        40,
        max_nodes * 3
    )

    focused_edges = (
        center_edges
        + other_edges
    )[:max_edges]

    return (
        focused_nodes,
        focused_edges
    )