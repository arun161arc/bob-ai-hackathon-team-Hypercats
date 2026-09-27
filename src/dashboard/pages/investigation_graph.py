from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# PATHS
# ============================================================

GRAPH_FILE = (
    PROJECT_ROOT
    / "output"
    / "graph"
    / "investigation_graph.json"
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Chanakya-Graph | Investigation Graph",
    page_icon="🕸️",
    layout="wide",
)


# ============================================================
# STYLE
# ============================================================

st.markdown(
    """
    <style>

    .title {
        font-size: 34px;
        font-weight: 700;
        margin-bottom: 2px;
    }

    .subtitle {
        color: #8b949e;
        font-size: 15px;
        margin-bottom: 22px;
    }

    .panel {
        padding: 16px;
        border: 1px solid #30363d;
        border-radius: 12px;
        background: #161b22;
        margin-bottom: 14px;
    }

    .connection-card {
        padding: 16px;
        border: 1px solid #30363d;
        border-radius: 12px;
        background: #161b22;
        margin-top: 10px;
    }

    .evidence-id {
        font-family: monospace;
        font-size: 14px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# LOAD GRAPH
# ============================================================

@st.cache_data
def load_graph():

    if not GRAPH_FILE.exists():
        return {
            "nodes": [],
            "edges": [],
        }

    with open(
        GRAPH_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


graph = load_graph()

nodes = graph.get("nodes", [])
edges = graph.get("edges", [])


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="title">🕸️ Investigation Graph</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    'Evidence-linked network reconstruction and relationship analysis'
    '</div>',
    unsafe_allow_html=True,
)


# ============================================================
# GRAPH STATUS
# ============================================================

if not nodes:

    st.error(
        "Investigation graph not found or contains no nodes."
    )

    st.info(
        "Run Phase 3 graph construction first."
    )

    st.stop()


# ============================================================
# NORMALIZE GRAPH DATA
# ============================================================

def node_id(node):

    return str(
        node.get("id")
        or node.get("entity_id")
        or ""
    )


def node_label(node):

    return str(
        node.get("label")
        or node.get("value")
        or node_id(node)
    )


def node_type(node):

    return str(
        node.get("entity_type")
        or node.get("type")
        or "UNKNOWN"
    )


node_lookup = {
    node_id(node): node
    for node in nodes
}


# ============================================================
# NODE TYPES
# ============================================================

node_types = sorted(
    {
        node_type(node)
        for node in nodes
    }
)


# ============================================================
# RELATIONSHIP TYPES
# ============================================================

relationship_types = sorted(
    {
        str(
            edge.get("relationship")
            or edge.get("type")
            or "UNKNOWN"
        )
        for edge in edges
    }
)


# ============================================================
# TOP METRICS
# ============================================================

metric_columns = st.columns(4)

with metric_columns[0]:
    st.metric(
        "Graph Nodes",
        f"{len(nodes):,}",
    )

with metric_columns[1]:
    st.metric(
        "Relationships",
        f"{len(edges):,}",
    )

with metric_columns[2]:
    st.metric(
        "Entity Types",
        f"{len(node_types):,}",
    )

with metric_columns[3]:
    st.metric(
        "Relationship Types",
        f"{len(relationship_types):,}",
    )


# ============================================================
# SIDEBAR FILTERS
# ============================================================

st.sidebar.header("Graph Controls")


selected_node_types = st.sidebar.multiselect(
    "Entity Types",
    options=node_types,
    default=node_types,
)


selected_relationships = st.sidebar.multiselect(
    "Relationships",
    options=relationship_types,
    default=relationship_types,
)


search_text = st.sidebar.text_input(
    "Search Entity",
    placeholder="Phone, account, IMEI...",
)


max_edges = st.sidebar.slider(
    "Maximum Graph Relationships",
    min_value=100,
    max_value=min(
        max(100, len(edges)),
        5000,
    ),
    value=min(
        max(500, len(edges)),
        2000,
    ),
    step=100,
)


# ============================================================
# FILTER NODES
# ============================================================

filtered_nodes = [
    node
    for node in nodes
    if node_type(node) in selected_node_types
]


if search_text.strip():

    query = search_text.strip().lower()

    filtered_nodes = [
        node
        for node in filtered_nodes
        if query in node_label(node).lower()
        or query in node_id(node).lower()
    ]


allowed_node_ids = {
    node_id(node)
    for node in filtered_nodes
}


# ============================================================
# FILTER EDGES
# ============================================================

filtered_edges = []

for edge in edges:

    relationship = str(
        edge.get("relationship")
        or edge.get("type")
        or "UNKNOWN"
    )

    source = str(
        edge.get("source")
        or edge.get("from")
        or ""
    )

    target = str(
        edge.get("target")
        or edge.get("to")
        or ""
    )

    if relationship not in selected_relationships:
        continue

    if (
        source not in allowed_node_ids
        or target not in allowed_node_ids
    ):
        continue

    filtered_edges.append(edge)

    if len(filtered_edges) >= max_edges:
        break


# ============================================================
# GRAPH DATA FOR VISUALIZATION
# ============================================================

def escape_js(value):

    return (
        str(value)
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "")
    )


# ============================================================
# NODE COLORS
# ============================================================

NODE_COLORS = {
    "PHONE": "#2ea043",
    "IMEI": "#d29922",
    "BANK_ACCOUNT": "#f85149",
    "ACCOUNT": "#f85149",
    "TOWER": "#a371f7",
    "COMPLAINT": "#db61a2",
    "PERSON": "#58a6ff",
    "TRANSACTION": "#79c0ff",
}


def get_node_color(entity_type):

    return NODE_COLORS.get(
        entity_type.upper(),
        "#8b949e",
    )


# ============================================================
# BUILD HTML GRAPH
# ============================================================

nodes_js = []

for node in filtered_nodes:

    nid = node_id(node)
    label = node_label(node)
    entity_type = node_type(node)

    nodes_js.append(
        {
            "id": nid,
            "label": label,
            "group": entity_type,
            "title": (
                f"<b>{label}</b><br>"
                f"Type: {entity_type}<br>"
                f"Entity ID: {nid}"
            ),
            "color": get_node_color(
                entity_type
            ),
        }
    )


edges_js = []

for index, edge in enumerate(filtered_edges):

    source = str(
        edge.get("source")
        or edge.get("from")
        or ""
    )

    target = str(
        edge.get("target")
        or edge.get("to")
        or ""
    )

    relationship = str(
        edge.get("relationship")
        or edge.get("type")
        or "UNKNOWN"
    )

    evidence_id = str(
        edge.get("evidence_id")
        or edge.get("evidence")
        or "N/A"
    )

    timestamp = str(
        edge.get("timestamp")
        or "N/A"
    )

    amount = edge.get(
    "amount_inr",
    edge.get("amount", ""),
)

    status = str(
        edge.get("evidence_status")
        or edge.get("status")
        or "OBSERVED"
    )

    hover_text = (
        f"<b>{relationship}</b><br>"
        f"Evidence: {evidence_id}<br>"
        f"Timestamp: {timestamp}<br>"
        f"Status: {status}"
    )

    if amount not in ("", None):

        try:

            hover_text += (
                f"<br>Amount: INR "
                f"{float(amount):,.2f}"
            )

        except Exception:
            pass

    edges_js.append(
        {
            "id": f"edge-{index}",
            "from": source,
            "to": target,
            "label": relationship,
            "title": hover_text,
            "arrows": "to",
            "evidence_id": evidence_id,
            "timestamp": timestamp,
            "status": status,
            "amount": amount,
        }
    )


# ============================================================
# VIS.JS HTML
# ============================================================

graph_html = f"""
<!DOCTYPE html>

<html>

<head>

<meta charset="utf-8">

<script
src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js">
</script>

<style>

html, body {{
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%;
    background: #0d1117;
    color: #e6edf3;
    font-family: Arial, sans-serif;
}}

#network {{
    width: 100%;
    height: 720px;
    border: 1px solid #30363d;
    border-radius: 12px;
    background: #0d1117;
}}

#info {{
    position: absolute;
    right: 20px;
    top: 20px;
    width: 300px;
    padding: 15px;
    background: rgba(22,27,34,0.96);
    border: 1px solid #30363d;
    border-radius: 10px;
    display: none;
    z-index: 10;
}}

.info-title {{
    font-weight: 700;
    font-size: 16px;
    margin-bottom: 10px;
}}

.info-row {{
    margin-top: 7px;
    color: #8b949e;
}}

.value {{
    color: #e6edf3;
    font-family: monospace;
}}

</style>

</head>

<body>

<div id="network"></div>

<div id="info">

    <div class="info-title">
        Explain This Connection
    </div>

    <div id="connection"></div>

</div>

<script>

const nodes = new vis.DataSet(
    {json.dumps(nodes_js)}
);

const edges = new vis.DataSet(
    {json.dumps(edges_js)}
);

const container =
    document.getElementById("network");

const data = {{
    nodes: nodes,
    edges: edges
}};

const options = {{

    interaction: {{
        hover: true,
        navigationButtons: true,
        keyboard: true,
        multiselect: false
    }},

    physics: {{

        enabled: true,

        stabilization: {{
            iterations: 150
        }},

        barnesHut: {{

            gravitationalConstant: -3500,
            centralGravity: 0.2,
            springLength: 160,
            springConstant: 0.04,
            damping: 0.12

        }}

    }},

    nodes: {{

        shape: "dot",

        size: 18,

        borderWidth: 2,

        font: {{
            color: "#e6edf3",
            size: 12
        }}

    }},

    edges: {{

        smooth: {{
            type: "dynamic"
        }},

        color: {{
            color: "#586069",
            highlight: "#58a6ff",
            hover: "#58a6ff"
        }},

        font: {{
            color: "#8b949e",
            size: 9,
            strokeWidth: 0
        }},

        arrows: {{
            to: {{
                enabled: true,
                scaleFactor: 0.6
            }}
        }},

        width: 1.5

    }}

}};

const network =
    new vis.Network(
        container,
        data,
        options
    );


/*
------------------------------------------------------------
NODE CLICK
------------------------------------------------------------
*/

network.on(
    "click",
    function(params) {{

        const info =
            document.getElementById("info");

        const connection =
            document.getElementById("connection");

        if (
            params.edges &&
            params.edges.length > 0
        ) {{

            const edgeId =
                params.edges[0];

            const edge =
                edges.get(edgeId);

            if (edge) {{

                let html = "";

                html +=
                    "<div class='info-row'>"
                    + "Relationship<br>"
                    + "<span class='value'>"
                    + edge.label
                    + "</span>"
                    + "</div>";

                html +=
                    "<div class='info-row'>"
                    + "Evidence ID<br>"
                    + "<span class='value'>"
                    + edge.evidence_id
                    + "</span>"
                    + "</div>";

                html +=
                    "<div class='info-row'>"
                    + "Timestamp<br>"
                    + "<span class='value'>"
                    + edge.timestamp
                    + "</span>"
                    + "</div>";

                html +=
                    "<div class='info-row'>"
                    + "Status<br>"
                    + "<span class='value'>"
                    + edge.status
                    + "</span>"
                    + "</div>";

                if (
                    edge.amount !== ""
                    && edge.amount !== null
                ) {{

                    html +=
                        "<div class='info-row'>"
                        + "Amount<br>"
                        + "<span class='value'>INR "
                        + Number(edge.amount)
                            .toLocaleString(
                                "en-IN",
                                {{
                                    minimumFractionDigits: 2
                                }}
                            )
                        + "</span>"
                        + "</div>";

                }}

                html +=
                    "<div class='info-row'>"
                    + "Source<br>"
                    + "<span class='value'>"
                    + edge.from
                    + "</span>"
                    + "</div>";

                html +=
                    "<div class='info-row'>"
                    + "Target<br>"
                    + "<span class='value'>"
                    + edge.to
                    + "</span>"
                    + "</div>";

                connection.innerHTML =
                    html;

                info.style.display =
                    "block";

            }}

        }}

    }}
);


/*
------------------------------------------------------------
DOUBLE CLICK = FOCUS NODE
------------------------------------------------------------
*/

network.on(
    "doubleClick",
    function(params) {{

        if (
            params.nodes &&
            params.nodes.length > 0
        ) {{

            network.focus(
                params.nodes[0],
                {{
                    scale: 1.5,
                    animation: true
                }}
            );

        }}

    }}
);

</script>

</body>

</html>
"""


# ============================================================
# DISPLAY GRAPH
# ============================================================

st.markdown(
    '<div class="panel">',
    unsafe_allow_html=True,
)

st.write(
    f"Displaying **{len(filtered_nodes):,} nodes** "
    f"and **{len(filtered_edges):,} relationships**."
)

if len(filtered_edges) >= max_edges:

    st.caption(
        "The graph is limited by the selected maximum "
        "relationship count for performance."
    )

components.html(
    graph_html,
    height=740,
    scrolling=False,
)

st.markdown(
    "</div>",
    unsafe_allow_html=True,
)


# ============================================================
# SELECT ENTITY
# ============================================================

st.markdown(
    "## 🔎 Entity Investigation"
)

entity_options = [
    (
        node_label(node),
        node_id(node)
    )
    for node in filtered_nodes
]

entity_options.sort(
    key=lambda item: item[0]
)

selected_entity = st.selectbox(
    "Select an entity",
    options=[
        "None"
    ] + entity_options,
    format_func=lambda value:
        value
        if isinstance(value, str)
        else f"{value[0]}  [{value[1]}]",
)


# ============================================================
# ENTITY DETAILS
# ============================================================

if selected_entity != "None":

    selected_id = selected_entity[1]

    selected_node = node_lookup.get(
        selected_id
    )

    if selected_node:

        st.markdown(
            "### Entity Details"
        )

        details = {
            "Entity ID": selected_id,
            "Label": node_label(
                selected_node
            ),
            "Type": node_type(
                selected_node
            ),
        }

        st.json(details)

        # ----------------------------------------------------
        # CONNECTIONS FOR ENTITY
        # ----------------------------------------------------

        entity_connections = []

        for edge in edges:

            source = str(
                edge.get("source")
                or edge.get("from")
                or ""
            )

            target = str(
                edge.get("target")
                or edge.get("to")
                or ""
            )

            if (
                source == selected_id
                or target == selected_id
            ):

                relationship = str(
                    edge.get("relationship")
                    or edge.get("type")
                    or "UNKNOWN"
                )

                entity_connections.append({
                    "Relationship": relationship,
                    "Source": source,
                    "Target": target,
                    "Evidence ID": edge.get(
                        "evidence_id",
                        "N/A",
                    ),
                    "Timestamp": edge.get(
                        "timestamp",
                        "N/A",
                    ),
                    "Status": edge.get(
                        "evidence_status",
                        edge.get(
                            "status",
                            "OBSERVED",
                        ),
                    ),
                })

        st.markdown(
            f"### Connections "
            f"({len(entity_connections):,})"
        )

        if entity_connections:

            st.dataframe(
                entity_connections[:500],
                use_container_width=True,
                hide_index=True,
            )

            if len(entity_connections) > 500:

                st.caption(
                    "Showing first 500 connections."
                )

        else:

            st.info(
                "No connections found for this entity."
            )


# ============================================================
# LEGEND
# ============================================================

st.markdown(
    "## Graph Legend"
)

legend_columns = st.columns(6)

legend = [
    ("PHONE", "#2ea043"),
    ("IMEI", "#d29922"),
    ("ACCOUNT", "#f85149"),
    ("TOWER", "#a371f7"),
    ("PERSON", "#58a6ff"),
    ("OTHER", "#8b949e"),
]

for column, (label, color) in zip(
    legend_columns,
    legend,
):

    with column:

        st.markdown(
            f"""
            <div style="
                border:1px solid #30363d;
                border-radius:8px;
                padding:8px;
            ">
                <span style="
                    display:inline-block;
                    width:12px;
                    height:12px;
                    border-radius:50%;
                    background:{color};
                    margin-right:6px;
                "></span>
                {label}
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Chanakya-Graph | Phase 10 | "
    "Evidence-linked Investigation Graph"
)

st.caption(
    "Graph relationships represent records extracted from "
    "the processed evidence. They are not, by themselves, "
    "proof of wrongdoing."
)