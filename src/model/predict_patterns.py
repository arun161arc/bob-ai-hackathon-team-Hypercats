import os
import json
import joblib
import pandas as pd

from feature_extractor import (
    load_graph,
    extract_features,
    FEATURE_NAMES
)


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

MODEL_FILE = os.path.join(
    BASE_DIR,
    "output",
    "model",
    "fraud_pattern_model.pkl"
)

OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "output",
    "model",
    "predictions.json"
)


def main():

    print("=" * 60)
    print("PHASE 4 — FRAUD PATTERN PREDICTION")
    print("=" * 60)

    # Check graph
    if not os.path.exists(GRAPH_FILE):

        print("\nERROR: Graph file not found:")
        print(GRAPH_FILE)

        print("\nRun Phase 3 first:")
        print("python src/graph/run_phase3.py")

        return

    # Check model
    if not os.path.exists(MODEL_FILE):

        print("\nERROR: ML model not found:")
        print(MODEL_FILE)

        print("\nRun model training first:")
        print("python src/model/train_model.py")

        return

    # Load graph
    print("\nLoading investigation graph...")

    graph = load_graph(
        GRAPH_FILE
    )

    print(
        f"Nodes: {graph.number_of_nodes()}"
    )

    print(
        f"Edges: {graph.number_of_edges()}"
    )

    # Extract graph features
    print("\nExtracting graph features...")

    features = extract_features(
        graph
    )

    print(
        f"Features extracted for "
        f"{len(features)} entities."
    )

    # Load trained model
    print("\nLoading trained ML model...")

    model = joblib.load(
        MODEL_FILE
    )

    print("Model loaded successfully.")

    results = []

    # Predict each entity
    print("\nRunning predictions...")

    for node_id, feature_data in features.items():

        row = {}

        for feature in FEATURE_NAMES:

            row[feature] = feature_data.get(
                feature,
                0
            )

        X = pd.DataFrame(
            [row],
            columns=FEATURE_NAMES
        )

        # Prediction
        prediction = model.predict(
            X
        )[0]

        # Probability
        probabilities = model.predict_proba(
            X
        )[0]

        confidence = max(
            probabilities
        )

        result = {
            "entity_id": node_id,

            "entity_type": feature_data.get(
                "entity_type",
                "UNKNOWN"
            ),

            "predicted_pattern": prediction,

            "confidence": round(
                float(confidence),
                4
            ),

            "features": feature_data
        }

        results.append(
            result
        )

    # Highest confidence first
    results.sort(
        key=lambda x: x["confidence"],
        reverse=True
    )

    # Save predictions
    os.makedirs(
        os.path.dirname(
            OUTPUT_FILE
        ),
        exist_ok=True
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            results,
            f,
            indent=2,
            default=str
        )

    # Display results
    print("\n" + "=" * 60)
    print("TOP ANALYTICAL FINDINGS")
    print("=" * 60)

    for result in results[:20]:

        print(
            f"\nEntity: "
            f"{result['entity_id']}"
        )

        print(
            f"Type: "
            f"{result['entity_type']}"
        )

        print(
            f"Predicted Pattern: "
            f"{result['predicted_pattern']}"
        )

        print(
            f"Confidence: "
            f"{result['confidence'] * 100:.2f}%"
        )

    print("\n" + "=" * 60)
    print("PREDICTION COMPLETE")
    print("=" * 60)

    print(
        f"\nPredictions saved to:"
    )

    print(
        OUTPUT_FILE
    )


if __name__ == "__main__":
    main()