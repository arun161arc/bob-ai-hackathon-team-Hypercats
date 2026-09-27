import json
import networkx as nx


FEATURE_NAMES = [
    "degree",
    "in_degree",
    "out_degree",
    "betweenness",
    "call_count",
    "fund_transfer_count",
    "total_received",
    "total_sent",
    "unique_senders",
    "unique_receivers",
    "shared_devices",
    "shared_towers",
    "phone_connections",
    "account_connections",
    "transaction_velocity",
    "max_transfer_amount"
]


def load_graph(graph_file):

    with open(
        graph_file,
        "r",
        encoding="utf-8"
    ) as f:
        data = json.load(f)

    graph = nx.node_link_graph(
        data,
        directed=True,
        multigraph=True,
        edges="edges"
    )

    return graph


def extract_features(graph):

    features = {}

    if graph.number_of_nodes() == 0:
        return features

    betweenness = nx.betweenness_centrality(
        graph
    )

    for node, data in graph.nodes(data=True):

        entity_type = data.get(
            "entity_type",
            "UNKNOWN"
        )

        degree = graph.degree(node)
        in_degree = graph.in_degree(node)
        out_degree = graph.out_degree(node)

        call_count = 0
        fund_transfer_count = 0

        total_received = 0.0
        total_sent = 0.0

        unique_senders = set()
        unique_receivers = set()

        shared_devices = set()
        shared_towers = set()

        phone_connections = 0
        account_connections = 0

        amounts = []

        for source, target, edge_data in graph.in_edges(
            node,
            data=True
        ):

            relationship = edge_data.get(
                "relationship",
                ""
            )

            if relationship == "TRANSFERRED_FUNDS":

                fund_transfer_count += 1

                amount = edge_data.get(
                    "amount_inr",
                    0
                )

                try:
                    amount = float(amount)
                except (ValueError, TypeError):
                    amount = 0.0

                total_received += amount
                amounts.append(amount)

                unique_senders.add(source)

            if relationship == "CALLED":

                call_count += 1

        for source, target, edge_data in graph.out_edges(
            node,
            data=True
        ):

            relationship = edge_data.get(
                "relationship",
                ""
            )

            if relationship == "TRANSFERRED_FUNDS":

                fund_transfer_count += 1

                amount = edge_data.get(
                    "amount_inr",
                    0
                )

                try:
                    amount = float(amount)
                except (ValueError, TypeError):
                    amount = 0.0

                total_sent += amount
                amounts.append(amount)

                unique_receivers.add(target)

            if relationship == "CALLED":

                call_count += 1

        for neighbor in graph.neighbors(node):

            neighbor_type = graph.nodes[
                neighbor
            ].get(
                "entity_type",
                ""
            )

            if neighbor_type == "IMEI":
                shared_devices.add(neighbor)

            elif neighbor_type == "TOWER":
                shared_towers.add(neighbor)

            elif neighbor_type == "PHONE":
                phone_connections += 1

            elif neighbor_type == "BANK_ACCOUNT":
                account_connections += 1

        transaction_velocity = (
            fund_transfer_count
            / max(degree, 1)
        )

        max_transfer_amount = (
            max(amounts)
            if amounts
            else 0.0
        )

        features[node] = {
            "degree": degree,
            "in_degree": in_degree,
            "out_degree": out_degree,
            "betweenness": betweenness.get(
                node,
                0.0
            ),
            "call_count": call_count,
            "fund_transfer_count":
                fund_transfer_count,
            "total_received":
                total_received,
            "total_sent":
                total_sent,
            "unique_senders":
                len(unique_senders),
            "unique_receivers":
                len(unique_receivers),
            "shared_devices":
                len(shared_devices),
            "shared_towers":
                len(shared_towers),
            "phone_connections":
                phone_connections,
            "account_connections":
                account_connections,
            "transaction_velocity":
                transaction_velocity,
            "max_transfer_amount":
                max_transfer_amount,
            "entity_type":
                entity_type
        }

    return features