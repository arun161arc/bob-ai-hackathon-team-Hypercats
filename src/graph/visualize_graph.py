import json
import os
import webbrowser

from pyvis.network import Network


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

OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "output",
    "graph",
    "investigation_graph.html"
)


def main():

    print("=" * 60)
    print("CHANAKYA-GRAPH — VISUAL INVESTIGATION GRAPH")
    print("=" * 60)

    if not os.path.exists(GRAPH_FILE):

        print("\nERROR: Graph file not found:")
        print(GRAPH_FILE)

        print("\nRun Phase 3 first:")
        print("python src/graph/run_phase3.py")

        return

    print("\nLoading graph...")

    with open(
        GRAPH_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    nodes = data.get("nodes", [])
    edges = data.get("edges", [])

    print(f"Nodes found: {len(nodes)}")
    print(f"Edges found: {len(edges)}")

    net = Network(
        height="850px",
        width="100%",
        bgcolor="#111827",
        font_color="white",
        directed=True
    )

    net.set_options("""
    {
      "nodes": {
        "shape": "dot",
        "size": 22,
        "font": {
          "size": 14,
          "face": "Arial",
          "color": "white"
        },
        "borderWidth": 2
      },

      "edges": {
        "arrows": {
          "to": {
            "enabled": true,
            "scaleFactor": 0.7
          }
        },
        "font": {
          "size": 11,
          "color": "white",
          "strokeWidth": 0
        },
        "smooth": {
          "type": "curvedCW"
        }
      },

      "physics": {
        "enabled": true,
        "solver": "forceAtlas2Based",
        "forceAtlas2Based": {
          "gravitationalConstant": -80,
          "centralGravity": 0.01,
          "springLength": 150,
          "springConstant": 0.08
        },
        "stabilization": {
          "enabled": true,
          "iterations": 1000
        }
      },

      "interaction": {
        "hover": true,
        "navigationButtons": true,
        "keyboard": true
      }
    }
    """)

    # -------------------------
    # ADD NODES
    # -------------------------

    for node in nodes:

        node_id = node.get("id")

        entity_type = node.get(
            "entity_type",
            "UNKNOWN"
        )

        value = node.get(
            "canonical_value",
            node_id
        )

        evidence_ids = node.get(
            "evidence_ids",
            []
        )

        label = f"{entity_type}\\n{value}"

        title = (
            f"<b>Entity Type:</b> {entity_type}<br>"
            f"<b>Value:</b> {value}<br>"
            f"<b>Evidence:</b> "
            f"{', '.join(map(str, evidence_ids[:10]))}"
        )

        # Different colors by entity type
        color = "#60a5fa"

        if entity_type == "PHONE":
            color = "#22c55e"

        elif entity_type == "IMEI":
            color = "#f59e0b"

        elif entity_type == "BANK_ACCOUNT":
            color = "#ef4444"

        elif entity_type == "TOWER":
            color = "#a78bfa"

        elif entity_type == "COMPLAINT":
            color = "#ec4899"

        net.add_node(
            node_id,
            label=label,
            title=title,
            color=color
        )

    # -------------------------
    # ADD EDGES
    # -------------------------

    for edge in edges:

        source = edge.get("source")
        target = edge.get("target")

        relationship = edge.get(
            "relationship",
            "RELATED"
        )

        evidence_id = edge.get(
            "evidence_id",
            "N/A"
        )

        timestamp = edge.get(
            "timestamp",
            "N/A"
        )

        amount = edge.get(
            "amount_inr",
            ""
        )

        title = (
            f"<b>Relationship:</b> {relationship}<br>"
            f"<b>Evidence ID:</b> {evidence_id}<br>"
            f"<b>Timestamp:</b> {timestamp}"
        )

        if amount:
            title += (
                f"<br><b>Amount:</b> INR {amount}"
            )

        net.add_edge(
            source,
            target,
            label=relationship,
            title=title
        )

    # -------------------------
    # SAVE HTML
    # -------------------------

    os.makedirs(
        os.path.dirname(OUTPUT_FILE),
        exist_ok=True
    )

    net.write_html(
        OUTPUT_FILE,
        open_browser=False
    )

    print("\n" + "=" * 60)
    print("VISUALIZATION CREATED")
    print("=" * 60)

    print(f"\nHTML file:")
    print(OUTPUT_FILE)

    print("\nOpening graph in browser...")

    webbrowser.open(
        "file:///" +
        os.path.abspath(OUTPUT_FILE).replace(
            "\\",
            "/"
        )
    )


if __name__ == "__main__":
    main()