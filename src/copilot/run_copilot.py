from .graph_query import load_graph
from .natural_language import process_question


def display_data(data):

    if not data:
        return

    print("\nRESULTS:")

    if isinstance(data, dict):

        for key, value in data.items():

            print(f"\n{key}:")

            if isinstance(value, list):

                for item in value[:10]:
                    print(f"  {item}")

            else:
                print(f"  {value}")

    elif isinstance(data, list):

        for item in data[:10]:
            print(item)

    else:

        print(data)


def main():

    print("=" * 75)
    print("CHANAKYA-GRAPH — ADVANCED INVESTIGATION COPILOT")
    print("=" * 75)

    graph = load_graph()

    print("\nInvestigation Graph:")
    print(f"Nodes : {graph.number_of_nodes()}")
    print(f"Edges : {graph.number_of_edges()}")

    questions = [

        "How many entities are in the graph?",

        "Show cumulative loss",

        "Show transactions for ACC-MULTIDAY-VICTIM-001",

        "Show transaction timeline",

        "Who received the money?",

        "What was the largest transaction?",

        "Show complaint information",

        "Show detection delay",

        "Show shared devices",

        "Show shared towers",

        "Show high value transactions",

        "Find +919800000101",

        "Show connections for +919800000101",

        "Show top connected entities"
    ]

    for question in questions:

        print("\n" + "-" * 75)
        print("QUESTION:")
        print(question)

        result = process_question(
            graph,
            question
        )

        print("\nANSWER:")
        print(result["answer"])

        print("\nQUERY TYPE:")
        print(result["query_type"])

        display_data(
            result.get("data")
        )

    print("\n" + "=" * 75)
    print("ADVANCED COPILOT TEST COMPLETE")
    print("=" * 75)


if __name__ == "__main__":
    main()