from collections import defaultdict


def get_edges(graph):
    """Convert NetworkX MultiDiGraph edges into dictionaries."""
    edges = []

    for source, target, key, data in graph.edges(
        keys=True,
        data=True
    ):
        edge = dict(data)

        edge["source"] = source
        edge["target"] = target
        edge["key"] = key

        # Get readable node labels from the graph
        source_data = graph.nodes.get(source, {})
        target_data = graph.nodes.get(target, {})

        edge["source_label"] = (
            source_data.get("label")
            or source_data.get("name")
            or source_data.get("value")
            or str(source)
        )

        edge["target_label"] = (
            target_data.get("label")
            or target_data.get("name")
            or target_data.get("value")
            or str(target)
        )

        edges.append(edge)

    return edges


def find_entity(graph, query):
    """Find an entity using ID, label, name or value."""

    query = str(query).strip().lower()

    results = []

    for node_id, data in graph.nodes(data=True):

        values = [
            str(node_id),
            str(data.get("label", "")),
            str(data.get("name", "")),
            str(data.get("value", "")),
            str(data.get("entity_id", "")),
        ]

        if any(query in value.lower() for value in values):
            results.append({
                "entity_id": node_id,
                "label": data.get("label", node_id),
                "type": data.get("type", "UNKNOWN"),
                "properties": dict(data),
            })

    return results


def get_connections(graph, entity):
    """Return all connections for an entity."""

    entity_lower = entity.lower()

    matched_nodes = []

    for node_id, data in graph.nodes(data=True):

        values = [
            str(node_id),
            str(data.get("label", "")),
            str(data.get("name", "")),
            str(data.get("value", "")),
        ]

        if any(entity_lower in v.lower() for v in values):
            matched_nodes.append(node_id)

    connections = []

    for node_id in matched_nodes:

        for source, target, key, data in graph.edges(
            node_id,
            keys=True,
            data=True
        ):

            target_data = graph.nodes.get(target, {})

            connections.append({
                "source": source,
                "source_label": graph.nodes.get(source, {}).get(
                    "label",
                    source
                ),
                "target": target,
                "target_label": target_data.get(
                    "label",
                    target
                ),
                "relationship": data.get(
                    "relationship",
                    data.get("type", "UNKNOWN")
                ),
                "evidence_id": data.get("evidence_id"),
                "timestamp": data.get("timestamp"),
                "amount_inr": data.get(
                    "amount_inr",
                    data.get("amount")
                ),
            })

        # incoming edges
        for source, target, key, data in graph.in_edges(
            node_id,
            keys=True,
            data=True
        ):

            source_data = graph.nodes.get(source, {})

            connections.append({
                "source": source,
                "source_label": source_data.get(
                    "label",
                    source
                ),
                "target": target,
                "target_label": graph.nodes.get(
                    target,
                    {}
                ).get("label", target),
                "relationship": data.get(
                    "relationship",
                    data.get("type", "UNKNOWN")
                ),
                "evidence_id": data.get("evidence_id"),
                "timestamp": data.get("timestamp"),
                "amount_inr": data.get(
                    "amount_inr",
                    data.get("amount")
                ),
            })

    return connections


def transaction_edges(graph):
    """Return only financial transaction edges."""

    edges = get_edges(graph)

    transactions = []

    for edge in edges:

        relationship = str(
            edge.get("relationship", "")
        ).upper()

        if relationship == "TRANSFERRED_FUNDS":

            transactions.append(edge)

    return transactions


def account_matches(edge, account):
    """Check whether an account appears on either side of an edge."""

    account = account.lower().strip()

    source_label = str(
        edge.get("source_label", "")
    ).lower()

    target_label = str(
        edge.get("target_label", "")
    ).lower()

    source_id = str(
        edge.get("source", "")
    ).lower()

    target_id = str(
        edge.get("target", "")
    ).lower()

    return (
        account in source_label
        or account in target_label
        or account in source_id
        or account in target_id
    )


def cumulative_loss(graph, account=None):
    """
    Calculate cumulative outgoing transfers.

    If account is supplied, only transactions involving
    that account are considered.
    """

    transactions = transaction_edges(graph)

    if account:
        transactions = [
            edge
            for edge in transactions
            if account_matches(edge, account)
        ]

    total = 0.0
    recipients = set()

    transaction_data = []

    for edge in transactions:

        amount = edge.get("amount_inr")

        try:
            amount = float(amount)
        except (TypeError, ValueError):
            continue

        total += amount

        target = edge.get(
            "target_label",
            edge.get("target")
        )

        source = edge.get(
            "source_label",
            edge.get("source")
        )

        recipients.add(str(target))

        transaction_data.append({
            "transaction_id": edge.get(
                "transaction_id",
                edge.get("evidence_id")
            ),
            "timestamp": edge.get("timestamp"),
            "sender": source,
            "receiver": target,
            "amount_inr": amount,
            "evidence_id": edge.get("evidence_id"),
        })

    return {
        "transaction_count": len(transaction_data),
        "total_amount_inr": total,
        "unique_recipients": len(recipients),
        "recipients": sorted(recipients),
        "transactions": transaction_data,
    }


def process_question(graph_data, question):

    question = question.strip()
    q = question.lower()

    # ---------------------------------------------------------
    # GRAPH SUMMARY
    # ---------------------------------------------------------

    if (
        "how many entities" in q
        or "graph summary" in q
        or "how many nodes" in q
    ):

        return {
            "type": "GRAPH_SUMMARY",
            "message": (
                f"The investigation graph contains "
                f"{graph_data.number_of_nodes()} entities "
                f"and "
                f"{graph_data.number_of_edges()} relationships."
            ),
            "data": {
                "nodes": graph_data.number_of_nodes(),
                "edges": graph_data.number_of_edges(),
                "connected_components": (
                    __import__("networkx")
                    .number_connected_components(
                        graph_data.to_undirected()
                    )
                ),
            },
        }

    # ---------------------------------------------------------
    # CUMULATIVE LOSS
    # ---------------------------------------------------------

    if (
        "cumulative loss" in q
        or "total loss" in q
        or "total amount" in q
    ):

        account = None

        # Look for an account mentioned in the question
        for node_id, data in graph_data.nodes(data=True):

            possible_values = [
                str(node_id),
                str(data.get("label", "")),
                str(data.get("name", "")),
                str(data.get("value", "")),
            ]

            if any(
                value.lower() in q
                for value in possible_values
                if len(value) > 5
            ):
                account = data.get(
                    "label",
                    node_id
                )
                break

        result = cumulative_loss(
            graph_data,
            account
        )

        return {
            "type": "CUMULATIVE_TRANSACTION_ANALYSIS",
            "message": (
                f"{result['transaction_count']} transaction(s) "
                f"totalling INR "
                f"{result['total_amount_inr']:,.2f}."
            ),
            "data": result,
        }

    # ---------------------------------------------------------
    # TRANSACTIONS
    # ---------------------------------------------------------

    if (
        "transaction" in q
        or "transfers" in q
        or "money flow" in q
    ):

        account = None

        for node_id, data in graph_data.nodes(data=True):

            possible_values = [
                str(node_id),
                str(data.get("label", "")),
                str(data.get("name", "")),
                str(data.get("value", "")),
            ]

            for value in possible_values:

                if len(value) > 5 and value.lower() in q:
                    account = value
                    break

            if account:
                break

        transactions = transaction_edges(
            graph_data
        )

        if account:
            transactions = [
                e
                for e in transactions
                if account_matches(e, account)
            ]

        data = []

        for edge in transactions:

            amount = edge.get("amount_inr")

            try:
                amount = float(amount)
            except (TypeError, ValueError):
                amount = 0

            data.append({
                "transaction_id": edge.get(
                    "transaction_id",
                    edge.get("evidence_id")
                ),
                "timestamp": edge.get("timestamp"),
                "sender": edge.get("source_label"),
                "receiver": edge.get("target_label"),
                "amount_inr": amount,
                "evidence_id": edge.get("evidence_id"),
            })

        return {
            "type": "TRANSACTION_SEARCH",
            "message": (
                f"Found {len(data)} transaction(s)."
            ),
            "data": data,
        }

    # ---------------------------------------------------------
    # LARGEST TRANSACTION
    # ---------------------------------------------------------

    if (
        "largest transaction" in q
        or "biggest transaction" in q
        or "highest transaction" in q
    ):

        transactions = transaction_edges(
            graph_data
        )

        parsed = []

        for edge in transactions:

            try:
                amount = float(
                    edge.get("amount_inr", 0)
                )
            except (TypeError, ValueError):
                continue

            parsed.append(
                (
                    amount,
                    edge
                )
            )

        if not parsed:

            return {
                "type": "LARGEST_TRANSACTION",
                "message": "No valid financial transactions found.",
                "data": {},
            }

        amount, edge = max(
            parsed,
            key=lambda x: x[0]
        )

        result = {
            "transaction_id": edge.get(
                "transaction_id",
                edge.get("evidence_id")
            ),
            "timestamp": edge.get("timestamp"),
            "sender": edge.get("source_label"),
            "receiver": edge.get("target_label"),
            "amount_inr": amount,
            "evidence_id": edge.get("evidence_id"),
        }

        return {
            "type": "LARGEST_TRANSACTION",
            "message": (
                f"Largest transaction: INR "
                f"{amount:,.2f}"
            ),
            "data": result,
        }

    # ---------------------------------------------------------
    # WHO RECEIVED MONEY
    # ---------------------------------------------------------

    if (
        "who received" in q
        or "recipients" in q
        or "who got the money" in q
    ):

        transactions = transaction_edges(
            graph_data
        )

        recipients = defaultdict(float)

        for edge in transactions:

            try:
                amount = float(
                    edge.get("amount_inr", 0)
                )
            except (TypeError, ValueError):
                continue

            receiver = edge.get(
                "target_label",
                edge.get("target")
            )

            recipients[receiver] += amount

        result = [
            {
                "recipient": recipient,
                "total_received_inr": amount,
            }
            for recipient, amount
            in sorted(
                recipients.items(),
                key=lambda x: x[1],
                reverse=True
            )
        ]

        return {
            "type": "RECIPIENT_ANALYSIS",
            "message": (
                f"Identified {len(result)} "
                f"recipient entities."
            ),
            "data": result,
        }

    # ---------------------------------------------------------
    # SHARED DEVICES
    # ---------------------------------------------------------

    if "shared device" in q:

        results = []

        for node_id, data in graph_data.nodes(
            data=True
        ):

            if str(
                data.get("type", "")
            ).upper() == "IMEI":

                connections = list(
                    graph_data.neighbors(node_id)
                )

                if len(connections) > 1:

                    results.append({
                        "imei": data.get(
                            "label",
                            node_id
                        ),
                        "connected_entities": len(
                            connections
                        ),
                    })

        return {
            "type": "SHARED_DEVICE_ANALYSIS",
            "message": (
                f"Found {len(results)} "
                f"shared-device relationships."
            ),
            "data": results,
        }

    # ---------------------------------------------------------
    # SHARED TOWERS
    # ---------------------------------------------------------

    if "shared tower" in q:

        results = []

        for node_id, data in graph_data.nodes(
            data=True
        ):

            if str(
                data.get("type", "")
            ).upper() == "TOWER":

                connections = list(
                    graph_data.neighbors(node_id)
                )

                if len(connections) > 1:

                    results.append({
                        "tower": data.get(
                            "label",
                            node_id
                        ),
                        "connected_entities": len(
                            connections
                        ),
                    })

        return {
            "type": "SHARED_TOWER_ANALYSIS",
            "message": (
                f"Found {len(results)} "
                f"shared-tower relationships."
            ),
            "data": results,
        }

    # ---------------------------------------------------------
    # FIND ENTITY
    # ---------------------------------------------------------

    if (
        q.startswith("find ")
        or q.startswith("search ")
        or q.startswith("lookup ")
        or q.startswith("show entity")
    ):

        search_term = (
            question
            .replace("Find ", "")
            .replace("find ", "")
            .replace("Search ", "")
            .replace("search ", "")
            .replace("Lookup ", "")
            .replace("lookup ", "")
            .strip()
        )

        results = find_entity(
            graph_data,
            search_term
        )

        return {
            "type": "ENTITY_SEARCH",
            "message": (
                f"Found {len(results)} matching "
                f"entity/entities."
            ),
            "data": results,
        }

    # ---------------------------------------------------------
    # CONNECTIONS
    # ---------------------------------------------------------

    if "connections" in q:

        search_term = (
            question
            .replace("Show connections for", "")
            .replace("show connections for", "")
            .strip()
        )

        results = get_connections(
            graph_data,
            search_term
        )

        return {
            "type": "CONNECTION_ANALYSIS",
            "message": (
                f"Found {len(results)} connections."
            ),
            "data": results,
        }

    # ---------------------------------------------------------
    # FALLBACK
    # ---------------------------------------------------------

    return {
        "type": "UNKNOWN",
        "message": (
            "I could not map that question to an "
            "investigation query."
        ),
        "data": [],
    }