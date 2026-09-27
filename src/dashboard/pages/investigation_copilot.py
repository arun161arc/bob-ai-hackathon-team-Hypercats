import sys
import os
import streamlit as st

# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        ".."
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ============================================================
# IMPORTS
# ============================================================

from src.copilot.graph_query import load_graph
from src.copilot.natural_language import process_question


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Investigation Copilot",
    page_icon="🤖",
    layout="wide"
)


# ============================================================
# HEADER
# ============================================================

st.title("🤖 Investigation Copilot")

st.markdown(
    """
    **Natural-language investigation assistant**

    Ask questions about entities, transactions, connections,
    devices, towers, evidence and financial activity.
    """
)

st.divider()


# ============================================================
# LOAD INVESTIGATION GRAPH
# ============================================================

try:

    graph_data = load_graph()

except Exception as e:

    st.error(
        f"Unable to load investigation graph: {e}"
    )

    st.stop()


# ============================================================
# GRAPH METRICS
# ============================================================

# graph_data is a NetworkX MultiDiGraph

node_count = graph_data.number_of_nodes()
edge_count = graph_data.number_of_edges()


col1, col2 = st.columns(2)

with col1:

    st.metric(
        "Entities",
        node_count
    )

with col2:

    st.metric(
        "Relationships",
        edge_count
    )


st.divider()


# ============================================================
# EXAMPLE QUESTIONS
# ============================================================

st.subheader("💡 Example Investigation Questions")

example_questions = [
    "How many entities are in the graph?",
    "Show cumulative loss",
    "Show transactions for ACC-MULTIDAY-VICTIM-001",
    "What was the largest transaction?",
    "Who received the money?",
    "Show shared devices",
    "Show shared towers",
    "Show high value transactions",
    "Find +919800000101",
    "Show connections for +919800000101",
    "Show top connected entities",
]


selected_example = st.selectbox(
    "Choose an example question",
    ["-- Select a question --"] + example_questions
)


# ============================================================
# QUESTION INPUT
# ============================================================

question = st.text_input(
    "Ask an investigation question",
    placeholder=(
        "Example: Show transactions for "
        "ACC-MULTIDAY-VICTIM-001"
    )
)


# ============================================================
# BUTTONS
# ============================================================

col1, col2 = st.columns(2)

with col1:

    ask_button = st.button(
        "🔎 Ask Copilot",
        type="primary",
        use_container_width=True
    )

with col2:

    use_example = st.button(
        "📌 Use Selected Example",
        use_container_width=True
    )


# ============================================================
# USE EXAMPLE
# ============================================================

if use_example:

    if selected_example != "-- Select a question --":

        question = selected_example

        ask_button = True

    else:

        st.warning(
            "Please select an example question first."
        )


# ============================================================
# PROCESS QUESTION
# ============================================================

if ask_button:

    if not question.strip():

        st.warning(
            "Please enter an investigation question."
        )

    else:

        st.divider()

        st.subheader("🔍 Investigation Query")

        st.code(
            question,
            language="text"
        )

        with st.spinner(
            "Analyzing investigation graph..."
        ):

            try:

                # IMPORTANT:
                # graph_data is a NetworkX MultiDiGraph
                #
                # process_question expects:
                # process_question(graph_data, question)

                result = process_question(
                    graph_data,
                    question
                )

            except Exception as e:

                st.error(
                    f"Copilot error: {e}"
                )

                st.stop()


        # ====================================================
        # RESULT TYPE
        # ====================================================

        result_type = result.get(
            "type",
            "UNKNOWN"
        )

        st.subheader(
            f"📊 {result_type}"
        )


        # ====================================================
        # RESULT MESSAGE
        # ====================================================

        message = result.get(
            "message",
            ""
        )

        if message:

            st.info(message)


        # ====================================================
        # RESULT DATA
        # ====================================================

        data = result.get(
            "data",
            []
        )


        # ----------------------------------------------------
        # DICTIONARY
        # ----------------------------------------------------

        if isinstance(data, dict):

            # Transaction analysis
            if (
                "transactions" in data
                and isinstance(
                    data["transactions"],
                    list
                )
            ):

                st.json(
                    {
                        key: value
                        for key, value in data.items()
                        if key != "transactions"
                    }
                )

                st.subheader(
                    "Transaction Records"
                )

                if data["transactions"]:

                    st.dataframe(
                        data["transactions"],
                        use_container_width=True
                    )

                else:

                    st.info(
                        "No transaction records found."
                    )

            else:

                st.json(data)


        # ----------------------------------------------------
        # LIST
        # ----------------------------------------------------

        elif isinstance(data, list):

            if len(data) > 0:

                st.dataframe(
                    data,
                    use_container_width=True
                )

            else:

                st.info(
                    "No matching records were found."
                )


        # ----------------------------------------------------
        # OTHER
        # ----------------------------------------------------

        else:

            st.write(data)


# ============================================================
# SUPPORTED QUERY TYPES
# ============================================================

st.divider()

st.subheader(
    "📚 Supported Investigation Queries"
)

query_col1, query_col2 = st.columns(2)

with query_col1:

    st.markdown(
        """
        **Graph Analysis**

        - How many entities are in the graph?
        - Show top connected entities
        - Show connections for a phone
        - Find an entity
        - Show shared devices
        - Show shared towers
        """
    )

with query_col2:

    st.markdown(
        """
        **Financial Investigation**

        - Show cumulative loss
        - Show transactions for an account
        - What was the largest transaction?
        - Who received the money?
        - Show high value transactions
        - Show evidence
        """
    )


# ============================================================
# INVESTIGATION GUIDANCE
# ============================================================

st.divider()

st.subheader(
    "⚠️ Investigation Guidance"
)

st.caption(
    """
    Copilot reports information derived from the investigation
    dataset and graph. Results are intended to support
    investigation and should not be treated as automatic
    determinations of wrongdoing.
    """
)