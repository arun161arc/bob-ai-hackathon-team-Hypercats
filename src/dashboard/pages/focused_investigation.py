from __future__ import annotations

import sys
import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


# =========================================================
# PROJECT PATH
# =========================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

if str(PROJECT_ROOT) not in sys.path:

    sys.path.insert(
        0,
        str(PROJECT_ROOT)
    )


from investigation.focused_graph import (
    load_graph_data,
    get_nodes,
    get_edges,
    search_entities,
    get_focused_network,
)


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Chanakya-Graph | Phase 11",
    page_icon="🔎",
    layout="wide",
)


# =========================================================
# CSS
# =========================================================

st.markdown(
    """
<style>

.title {
    font-size: 32px;
    font-weight: 800;
}

.subtitle {
    color: #9ca3af;
    margin-bottom: 20px;
}

.metric {
    background: #111827;
    border: 1px solid #374151;
    border-radius: 12px;
    padding: 15px;
    text-align: center;
}

.metric-value {
    font-size: 25px;
    font-weight: 800;
}

.metric-label {
    color: #9ca3af;
    font-size: 11px;
}

</style>
""",
    unsafe_allow_html=True
)


# =========================================================
# LOAD GRAPH
# =========================================================

@st.cache_data
def load_data():

    graph = load_graph_data()

    nodes = get_nodes(
        graph
    )

    edges = get_edges(
        graph
    )

    return (
        graph,
        nodes,
        edges
    )


try:

    (
        graph_data,
        all_nodes,
        all_edges
    ) = load_data()

except Exception as error:

    st.error(
        f"Unable to load graph:\n\n{error}"
    )

    st.stop()


# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="title">'
    '🔎 Focused Investigation Graph'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Search an entity, expand its network, '
    'and investigate evidence-backed connections.'
    '</div>',
    unsafe_allow_html=True
)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header(
        "Investigation Controls"
    )

    # -----------------------------------------------------
    # SEARCH
    # -----------------------------------------------------

    st.subheader(
        "1. Select Entity"
    )

    search_text = st.text_input(
        "Search entity",
        placeholder=(
            "Phone, account, IMEI, tower..."
        )
    )

    matches = search_entities(
        graph_data,
        search_text,
        limit=30
    )

    if matches:

        labels = [
            (
                f"{node['label']} | "
                f"{node['entity_type']}"
            )
            for node in matches
        ]

        selected_index = st.selectbox(
            "Matching entities",
            range(len(labels)),
            format_func=lambda i:
                labels[i]
        )

        selected_node = matches[
            selected_index
        ]

    else:

        if search_text:

            st.warning(
                "No matching entity found."
            )

        selected_node = None

    st.divider()

    # -----------------------------------------------------
    # DEPTH
    # -----------------------------------------------------

    st.subheader(
        "2. Network Depth"
    )

    depth = st.radio(
        "Expand network",
        options=[1, 2, 3],
        index=0,
        horizontal=True,
        format_func=lambda value:
            f"{value}-hop"
    )

    max_nodes = st.slider(
        "Maximum nodes",
        min_value=10,
        max_value=100,
        value=50,
        step=10
    )

    st.divider()

    # -----------------------------------------------------
    # ENTITY TYPES
    # -----------------------------------------------------

    st.subheader(
        "3. Entity Type"
    )

    entity_types = sorted(
        {
            node["entity_type"]
            for node in all_nodes
            if node.get(
                "entity_type"
            )
        }
    )

    selected_types = st.multiselect(
        "Limit connected entities",
        options=entity_types
    )


# =========================================================
# DEFAULT ENTITY
# =========================================================

if selected_node is None:

    if not all_nodes:

        st.error(
            "No entities found in graph."
        )

        st.stop()

    selected_node = all_nodes[0]


center_id = selected_node["id"]


# =========================================================
# FOCUSED GRAPH
# =========================================================

focused_nodes, focused_edges = (
    get_focused_network(
        graph_data,
        center_id=center_id,
        depth=depth,
        max_nodes=max_nodes,
        entity_type_filter=(
            selected_types
            if selected_types
            else None
        )
    )
)


# =========================================================
# METRICS
# =========================================================

c1, c2, c3, c4 = st.columns(4)


with c1:

    st.markdown(
        f"""
<div class="metric">
<div class="metric-value">
{len(focused_nodes)}
</div>
<div class="metric-label">
FOCUSED ENTITIES
</div>
</div>
""",
        unsafe_allow_html=True
    )


with c2:

    st.markdown(
        f"""
<div class="metric">
<div class="metric-value">
{len(focused_edges)}
</div>
<div class="metric-label">
VISIBLE CONNECTIONS
</div>
</div>
""",
        unsafe_allow_html=True
    )


with c3:

    st.markdown(
        f"""
<div class="metric">
<div class="metric-value">
{depth}-HOP
</div>
<div class="metric-label">
NETWORK DEPTH
</div>
</div>
""",
        unsafe_allow_html=True
    )


with c4:

    st.markdown(
        f"""
<div class="metric">
<div class="metric-value">
{selected_node["entity_type"]}
</div>
<div class="metric-label">
FOCUS TYPE
</div>
</div>
""",
        unsafe_allow_html=True
    )


# =========================================================
# FOCUS
# =========================================================

st.subheader(
    "Investigation Focus"
)

st.info(
    f"Entity: **{selected_node['label']}**  "
    f"| Type: **{selected_node['entity_type']}**"
)


# =========================================================
# CREATE NODE DATA
# =========================================================

nodes_for_js = []

for node in focused_nodes:

    entity_type = node[
        "entity_type"
    ]

    if node["id"] == center_id:

        color = "#f97316"
        size = 32

    elif entity_type == "PHONE":

        color = "#22c55e"
        size = 22

    elif entity_type == "BANK_ACCOUNT":

        color = "#ef4444"
        size = 24

    elif entity_type == "IMEI":

        color = "#f59e0b"
        size = 21

    elif entity_type == "TOWER":

        color = "#a855f7"
        size = 20

    elif entity_type == "PERSON":

        color = "#3b82f6"
        size = 22

    elif entity_type == "TRANSACTION":

        color = "#06b6d4"
        size = 18

    else:

        color = "#9ca3af"
        size = 18

    nodes_for_js.append(
        {
            "id": node["id"],
            "label": node["label"],
            "type": entity_type,
            "color": color,
            "size": size
        }
    )


# =========================================================
# CREATE EDGE DATA
# =========================================================

edges_for_js = []

for index, edge in enumerate(
    focused_edges
):

    edges_for_js.append(
        {
            "id": (
                edge.get(
                    "edge_id"
                )
                or
                f"edge-{index}"
            ),

            "from": edge[
                "source"
            ],

            "to": edge[
                "target"
            ],

            "relationship": edge.get(
                "relationship",
                "RELATED"
            ),

            "evidence_id": edge.get(
                "evidence_id"
            ),

            "timestamp": edge.get(
                "timestamp"
            ),

            "status": edge.get(
                "evidence_status",
                "OBSERVED"
            ),

            "amount": edge.get(
                "amount_inr",
                ""
            )
        }
    )


nodes_json = json.dumps(
    nodes_for_js
)

edges_json = json.dumps(
    edges_for_js
)


# =========================================================
# HTML / JAVASCRIPT
# =========================================================

graph_html = f"""
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>

<style>

html,
body {{

    margin: 0;

    padding: 0;

    background: #0b0f14;

    width: 100%;

    height: 100%;

    font-family: Arial, sans-serif;

}}

#network {{

    width: 100%;

    height: 600px;

    background: #0b0f14;

    border: 1px solid #374151;

    border-radius: 12px;

}}

</style>

</head>

<body>

<div id="network"></div>

<script>

const nodeData = {nodes_json};

const edgeData = {edges_json};


const nodes = new vis.DataSet(
    nodeData.map(function(n) {{

        return {{

            id: n.id,

            label: n.label,

            shape: "dot",

            size: n.size,

            title:
                n.label +
                "<br>Type: " +
                n.type,

            color: {{

                background: n.color,

                border: "#ffffff",

                highlight: {{

                    background: "#ffffff",

                    border: n.color

                }}

            }},

            font: {{

                color: "#ffffff",

                size: 11

            }}

        }};

    }})
);


const edges = new vis.DataSet(
    edgeData.map(function(e) {{

        return {{

            id: e.id,

            from: e.from,

            to: e.to,

            arrows: "to",

            label: e.relationship,

            title:
                "Relationship: " +
                e.relationship +
                "<br>Evidence: " +
                (e.evidence_id || "N/A") +
                "<br>Timestamp: " +
                (e.timestamp || "N/A") +
                "<br>Status: " +
                (e.status || "OBSERVED"),

            color: {{

                color: "#6b7280",

                highlight: "#f97316"

            }},

            font: {{

                color: "#d1d5db",

                size: 8,

                strokeWidth: 0

            }},

            width: 1

        }};

    }})
);


const container =
    document.getElementById(
        "network"
    );


const data = {{

    nodes: nodes,

    edges: edges

}};


const options = {{

    autoResize: true,

    interaction: {{

        hover: true,

        navigationButtons: true,

        keyboard: true,

        dragNodes: true,

        dragView: true,

        zoomView: true

    }},

    physics: {{

        enabled: true,

        stabilization: {{

            enabled: true,

            iterations: 200

        }},

        barnesHut: {{

            gravitationalConstant: -4000,

            centralGravity: 0.2,

            springLength: 150,

            springConstant: 0.04,

            damping: 0.12,

            avoidOverlap: 0.7

        }}

    }},

    edges: {{

        smooth: {{

            enabled: true,

            type: "dynamic"

        }}

    }}

}};


const network =
    new vis.Network(
        container,
        data,
        options
    );


network.on(
    "click",
    function(params) {{

        if (
            !params.edges ||
            params.edges.length === 0
        ) {{

            return;

        }}

        const edgeId =
            params.edges[0];


        const edge =
            edgeData.find(
                function(item) {{

                    return (
                        item.id === edgeId
                    );

                }}
            );


        if (!edge) {{

            return;

        }}


        const message =

            "SOURCE: " +
            edge.from +

            "\\n\\nTARGET: " +
            edge.to +

            "\\n\\nRELATIONSHIP: " +
            edge.relationship +

            "\\n\\nEVIDENCE ID: " +
            (
                edge.evidence_id
                || "N/A"
            ) +

            "\\n\\nTIMESTAMP: " +
            (
                edge.timestamp
                || "N/A"
            ) +

            "\\n\\nSTATUS: " +
            (
                edge.status
                || "OBSERVED"
            ) +

            "\\n\\nAMOUNT: " +
            (
                edge.amount
                ? "INR " + edge.amount
                : "N/A"
            );


        window.alert(
            message
        );

    }}

);

</script>

</body>

</html>
"""


# =========================================================
# DISPLAY GRAPH
# =========================================================

st.subheader(
    "Network"
)

st.caption(
    f"Showing {len(focused_nodes)} "
    f"entities and "
    f"{len(focused_edges)} "
    f"relationships around "
    f"{selected_node['label']}."
)


components.html(
    graph_html,
    height=630,
    scrolling=False
)


# =========================================================
# EVIDENCE TABLE
# =========================================================

st.subheader(
    "Evidence Connections"
)

if focused_edges:

    rows = []

    for edge in focused_edges:

        rows.append(
            {
                "Source": edge[
                    "source"
                ],

                "Relationship": edge[
                    "relationship"
                ],

                "Target": edge[
                    "target"
                ],

                "Evidence ID": edge.get(
                    "evidence_id",
                    "N/A"
                ),

                "Timestamp": edge.get(
                    "timestamp",
                    "N/A"
                ),

                "Status": edge.get(
                    "evidence_status",
                    "OBSERVED"
                ),

                "Amount": edge.get(
                    "amount_inr",
                    ""
                )
            }
        )

    st.dataframe(
        rows,
        use_container_width=True,
        hide_index=True
    )

else:

    st.info(
        "No evidence connections found."
    )


# =========================================================
# GUIDANCE
# =========================================================

with st.expander(
    "Investigation guidance"
):

    st.markdown(
        """
**OBSERVED**

Directly recorded in the supplied evidence.

**DERIVED**

Calculated from the observed evidence.

**ANALYTICAL INFERENCE**

An investigative lead derived from observed
and calculated information. It should not
be treated as proof of wrongdoing.

A graph connection represents an
evidence-backed relationship in the supplied
dataset.
"""
    )