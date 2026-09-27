import json
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime


BASE_DIR = Path(__file__).resolve().parents[1]

GRAPH_PATH = (
    BASE_DIR
    / "output"
    / "graph"
    / "investigation_graph.json"
)

UPI_PATH = BASE_DIR / "data" / "upi_transactions.csv"
COMPLAINT_PATH = BASE_DIR / "data" / "complaints.csv"
CDR_PATH = BASE_DIR / "data" / "cdr_records.csv"
DEVICE_PATH = BASE_DIR / "data" / "device_records.csv"


def load_graph():
    import networkx as nx

    with open(GRAPH_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    graph = nx.MultiDiGraph()

    for node in data.get("nodes", []):
        node_id = node.get("id") or node.get("entity_id")

        if node_id:
            graph.add_node(node_id, **node)

    for edge in data.get("edges", []):
        source = edge.get("source")
        target = edge.get("target")

        if source and target:
            graph.add_edge(
                source,
                target,
                **edge
            )

    return graph


def normalize_text(value):
    if value is None:
        return ""

    return str(value).strip().lower()


def get_node(graph, entity_id):
    if entity_id not in graph:
        return None

    return {
        "entity_id": entity_id,
        **dict(graph.nodes[entity_id])
    }


def find_entity(graph, query):
    query = normalize_text(query)

    results = []

    for node_id, attrs in graph.nodes(data=True):

        values = [
            str(node_id),
            str(attrs.get("label", "")),
            str(attrs.get("entity_id", "")),
            str(attrs.get("value", "")),
            str(attrs.get("entity_type", "")),
            str(attrs.get("type", ""))
        ]

        if any(query in normalize_text(v) for v in values):
            results.append({
                "entity_id": node_id,
                "entity_type": attrs.get(
                    "entity_type",
                    attrs.get("type", "UNKNOWN")
                ),
                "label": attrs.get(
                    "label",
                    attrs.get("value", node_id)
                ),
                "evidence_ids": attrs.get(
                    "evidence_ids",
                    []
                ),
                "source_types": attrs.get(
                    "source_types",
                    []
                )
            })

    return results


def get_connections(graph, entity_id):

    if entity_id not in graph:
        return []

    connections = []

    for target in graph.successors(entity_id):

        for _, edge_data in graph[entity_id][target].items():

            connections.append({
                "source": entity_id,
                "target": target,
                "target_label": graph.nodes[target].get(
                    "label",
                    target
                ),
                "target_type": graph.nodes[target].get(
                    "entity_type",
                    graph.nodes[target].get("type", "UNKNOWN")
                ),
                "relationship": edge_data.get(
                    "relationship",
                    edge_data.get("type", "UNKNOWN")
                ),
                "evidence_id": edge_data.get(
                    "evidence_id"
                ),
                "timestamp": edge_data.get(
                    "timestamp"
                ),
                "amount_inr": edge_data.get(
                    "amount_inr"
                )
            })

    for source in graph.predecessors(entity_id):

        for _, edge_data in graph[source][entity_id].items():

            connections.append({
                "source": source,
                "source_label": graph.nodes[source].get(
                    "label",
                    source
                ),
                "source_type": graph.nodes[source].get(
                    "entity_type",
                    graph.nodes[source].get("type", "UNKNOWN")
                ),
                "target": entity_id,
                "relationship": edge_data.get(
                    "relationship",
                    edge_data.get("type", "UNKNOWN")
                ),
                "evidence_id": edge_data.get(
                    "evidence_id"
                ),
                "timestamp": edge_data.get(
                    "timestamp"
                ),
                "amount_inr": edge_data.get(
                    "amount_inr"
                )
            })

    return connections


def shared_devices(graph):

    device_to_phones = defaultdict(set)

    for node_id, attrs in graph.nodes(data=True):

        entity_type = str(
            attrs.get(
                "entity_type",
                attrs.get("type", "")
            )
        ).upper()

        if entity_type != "IMEI":
            continue

        for neighbor in graph.neighbors(node_id):

            neighbor_type = str(
                graph.nodes[neighbor].get(
                    "entity_type",
                    graph.nodes[neighbor].get("type", "")
                )
            ).upper()

            if neighbor_type == "PHONE":
                device_to_phones[node_id].add(neighbor)

    results = []

    for imei, phones in device_to_phones.items():

        if len(phones) > 1:

            results.append({
                "device": imei,
                "phone_count": len(phones),
                "phones": list(phones)
            })

    return results


def shared_towers(graph):

    tower_to_phones = defaultdict(set)

    for node_id, attrs in graph.nodes(data=True):

        entity_type = str(
            attrs.get(
                "entity_type",
                attrs.get("type", "")
            )
        ).upper()

        if entity_type != "TOWER":
            continue

        for neighbor in graph.neighbors(node_id):

            neighbor_type = str(
                graph.nodes[neighbor].get(
                    "entity_type",
                    graph.nodes[neighbor].get("type", "")
                )
            ).upper()

            if neighbor_type == "PHONE":
                tower_to_phones[node_id].add(neighbor)

    results = []

    for tower, phones in tower_to_phones.items():

        if len(phones) > 1:

            results.append({
                "tower": tower,
                "phone_count": len(phones),
                "phones": list(phones)
            })

    return results


def load_csv(path):

    import pandas as pd

    if not path.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(
            path,
            dtype=str
        )
    except Exception:
        return pd.DataFrame()


def load_upi():
    return load_csv(UPI_PATH)


def load_complaints():
    return load_csv(COMPLAINT_PATH)


def load_cdr():
    return load_csv(CDR_PATH)


def load_devices():
    return load_csv(DEVICE_PATH)


def transaction_analysis(account=None):

    df = load_upi()

    if df.empty:
        return {
            "transactions": [],
            "count": 0,
            "total_amount": 0
        }

    if account:

        account = str(account).strip()

        mask = (
            df["sender_account"].astype(str).eq(account)
            |
            df["receiver_account"].astype(str).eq(account)
        )

        df = df[mask].copy()

    if df.empty:
        return {
            "transactions": [],
            "count": 0,
            "total_amount": 0
        }

    df["amount_numeric"] = (
        df["amount_inr"]
        .astype(str)
        .str.replace(",", "", regex=False)
        .astype(float)
    )

    transactions = []

    for _, row in df.iterrows():

        transactions.append({
            "transaction_id": row.get(
                "transaction_id"
            ),
            "timestamp": row.get(
                "timestamp"
            ),
            "sender": row.get(
                "sender_account"
            ),
            "receiver": row.get(
                "receiver_account"
            ),
            "amount_inr": float(
                row.get("amount_numeric", 0)
            ),
            "status": row.get(
                "transaction_status"
            ),
            "reference_id": row.get(
                "reference_id"
            ),
            "case_id": row.get(
                "case_id"
            ),
            "data_source": row.get(
                "data_source"
            )
        })

    transactions.sort(
        key=lambda x: str(x["timestamp"])
    )

    return {
        "transactions": transactions,
        "count": len(transactions),
        "total_amount": sum(
            x["amount_inr"]
            for x in transactions
        )
    }


def transaction_timeline(account=None):

    result = transaction_analysis(account)

    transactions = result["transactions"]

    if not transactions:
        return {
            "count": 0,
            "first_transaction": None,
            "last_transaction": None,
            "timeline": []
        }

    return {
        "count": len(transactions),
        "first_transaction": transactions[0],
        "last_transaction": transactions[-1],
        "timeline": transactions
    }


def unique_recipients(account):

    result = transaction_analysis(account)

    recipients = sorted(
        set(
            x["receiver"]
            for x in result["transactions"]
            if x["receiver"] != account
        )
    )

    return recipients


def largest_transaction(account=None):

    result = transaction_analysis(account)

    if not result["transactions"]:
        return None

    return max(
        result["transactions"],
        key=lambda x: x["amount_inr"]
    )


def complaint_for_account(account):

    df = load_complaints()

    if df.empty:
        return None

    if "victim_account" not in df.columns:
        return None

    matches = df[
        df["victim_account"]
        .astype(str)
        .eq(str(account))
    ]

    if matches.empty:
        return None

    row = matches.iloc[0]

    return {
        "complaint_id": row.get(
            "complaint_id"
        ),
        "timestamp": row.get(
            "complaint_timestamp"
        ),
        "victim_name": row.get(
            "victim_name"
        ),
        "victim_phone": row.get(
            "victim_phone"
        ),
        "victim_account": row.get(
            "victim_account"
        ),
        "reported_amount_inr": row.get(
            "reported_amount_inr"
        ),
        "category": row.get(
            "fraud_category"
        ),
        "description": row.get(
            "complaint_description"
        ),
        "data_source": row.get(
            "data_source"
        )
    }


def detection_delay(account):

    timeline = transaction_timeline(account)

    complaint = complaint_for_account(account)

    if not timeline["last_transaction"] or not complaint:
        return None

    try:

        last_time = datetime.fromisoformat(
            str(
                timeline["last_transaction"][
                    "timestamp"
                ]
            )
        )

        complaint_time = datetime.fromisoformat(
            str(
                complaint["timestamp"]
            )
        )

        delta = complaint_time - last_time

        return {
            "seconds": delta.total_seconds(),
            "hours": round(
                delta.total_seconds() / 3600,
                2
            ),
            "days": round(
                delta.total_seconds() / 86400,
                2
            )
        }

    except Exception:
        return None


def cumulative_loss(account):

    result = transaction_analysis(account)

    complaint = complaint_for_account(account)

    transactions = result["transactions"]

    outgoing = [
        x for x in transactions
        if str(x["sender"]) == str(account)
    ]

    total = sum(
        x["amount_inr"]
        for x in outgoing
    )

    return {
        "transaction_count": len(outgoing),
        "total_amount": total,
        "recipients": sorted(
            set(
                x["receiver"]
                for x in outgoing
            )
        ),
        "complaint": complaint,
        "detection_delay": detection_delay(
            account
        )
    }


def high_value_transactions(
    threshold=50000
):

    result = transaction_analysis()

    return [
        x
        for x in result["transactions"]
        if x["amount_inr"] >= threshold
    ]


def top_connected_entities(graph, limit=10):

    ranked = sorted(
        graph.degree(),
        key=lambda x: x[1],
        reverse=True
    )

    results = []

    for entity_id, degree in ranked[:limit]:

        attrs = graph.nodes[entity_id]

        results.append({
            "entity_id": entity_id,
            "label": attrs.get(
                "label",
                entity_id
            ),
            "entity_type": attrs.get(
                "entity_type",
                attrs.get("type", "UNKNOWN")
            ),
            "connections": degree
        })

    return results


def shortest_path(graph, source_query, target_query):

    sources = find_entity(
        graph,
        source_query
    )

    targets = find_entity(
        graph,
        target_query
    )

    if not sources or not targets:
        return None

    source = sources[0]["entity_id"]
    target = targets[0]["entity_id"]

    try:

        import networkx as nx

        path = nx.shortest_path(
            graph,
            source=source,
            target=target
        )

        return path

    except Exception:
        return None


def graph_summary(graph):

    import networkx as nx

    return {
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "connected_components": nx.number_weakly_connected_components(
            graph
        )
    }