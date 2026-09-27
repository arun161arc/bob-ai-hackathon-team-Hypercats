import networkx as nx


class GraphAnalyzer:

    def __init__(self, graph):

        self.graph = graph

    # -----------------------------------------------------
    # DEGREE CENTRALITY
    # -----------------------------------------------------

    def degree_centrality(self):

        return nx.degree_centrality(
            self.graph
        )

    # -----------------------------------------------------
    # BETWEENNESS
    # -----------------------------------------------------

    def betweenness_centrality(self):

        return nx.betweenness_centrality(
            self.graph
        )

    # -----------------------------------------------------
    # TOP N NODES
    # -----------------------------------------------------

    def top_nodes(
        self,
        centrality,
        n=10
    ):

        return sorted(
            centrality.items(),
            key=lambda item: item[1],
            reverse=True
        )[:n]

    # -----------------------------------------------------
    # RELATIONSHIP COUNTS
    # -----------------------------------------------------

    def relationship_counts(self):

        counts = {}

        for _, _, data in (
            self.graph.edges(
                data=True
            )
        ):

            relationship = data.get(
                "relationship",
                "UNKNOWN"
            )

            counts[
                relationship
            ] = (
                counts.get(
                    relationship,
                    0
                ) + 1
            )

        return counts

    # -----------------------------------------------------
    # MULTI-SOURCE NODES
    # -----------------------------------------------------

    def multi_source_nodes(self):

        result = []

        for node, data in (
            self.graph.nodes(
                data=True
            )
        ):

            sources = data.get(
                "source_types",
                []
            )

            if len(sources) > 1:

                result.append({
                    "entity_id": node,
                    "entity_type":
                        data.get(
                            "entity_type"
                        ),
                    "label":
                        data.get(
                            "label"
                        ),
                    "source_types":
                        sources
                })

        return result

    # -----------------------------------------------------
    # CONNECTED COMPONENTS
    # -----------------------------------------------------

    def connected_components(self):

        undirected = self.graph.to_undirected()

        return [
            list(component)
            for component in
            nx.connected_components(
                undirected
            )
        ]