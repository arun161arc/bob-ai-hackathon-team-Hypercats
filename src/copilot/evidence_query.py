import json


GRAPH_PATH = "src/output/graph/investigation_graph.json"


def load_graph_data():

    with open(
        GRAPH_PATH,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


def find_evidence(evidence_id):

    data = load_graph_data()

    results = []

    for link in data.get("links", []):

        if link.get("evidence_id") == evidence_id:

            results.append({
                "source": link.get("source"),
                "target": link.get("target"),
                "relationship":
                    link.get("relationship"),
                "evidence_id":
                    link.get("evidence_id"),
                "timestamp":
                    link.get("timestamp"),
                "amount":
                    link.get("amount"),
                "evidence_status":
                    link.get(
                        "evidence_status",
                        "OBSERVED"
                    )
            })

    return results


def explain_connection(
    source,
    target
):

    data = load_graph_data()

    results = []

    for link in data.get("links", []):

        if (
            link.get("source") == source
            and
            link.get("target") == target
        ):

            results.append({
                "source": source,
                "target": target,
                "relationship":
                    link.get("relationship"),
                "evidence_id":
                    link.get("evidence_id"),
                "timestamp":
                    link.get("timestamp"),
                "amount":
                    link.get("amount"),
                "evidence_status":
                    link.get(
                        "evidence_status",
                        "OBSERVED"
                    )
            })

    return results