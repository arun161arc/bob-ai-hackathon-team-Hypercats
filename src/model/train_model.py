import os
import json
import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report
)

from feature_extractor import FEATURE_NAMES


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

TRAINING_FILE = os.path.join(
    BASE_DIR,
    "output",
    "model",
    "training_data.csv"
)

MODEL_FILE = os.path.join(
    BASE_DIR,
    "output",
    "model",
    "fraud_pattern_model.pkl"
)

FEATURE_FILE = os.path.join(
    BASE_DIR,
    "output",
    "model",
    "feature_names.json"
)


def train_model():

    print("=" * 60)
    print("PHASE 4 — FRAUD PATTERN MODEL TRAINING")
    print("=" * 60)

    if not os.path.exists(
        TRAINING_FILE
    ):

        print(
            "\nTraining data not found."
        )

        print(
            "Run:"
        )

        print(
            "python src/model/create_training_data.py"
        )

        return

    df = pd.read_csv(
        TRAINING_FILE
    )

    X = df[
        FEATURE_NAMES
    ]

    y = df[
        "pattern"
    ]

    X_train, X_test, y_train, y_test = (
        train_test_split(
            X,
            y,
            test_size=0.20,
            random_state=42,
            stratify=y
        )
    )

    print(
        f"\nTraining samples: "
        f"{len(X_train)}"
    )

    print(
        f"Testing samples: "
        f"{len(X_test)}"
    )

    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=12,
        min_samples_split=4,
        random_state=42,
        class_weight="balanced",
        n_jobs=-1
    )

    print("\nTraining Random Forest...")

    model.fit(
        X_train,
        y_train
    )

    predictions = model.predict(
        X_test
    )

    accuracy = accuracy_score(
        y_test,
        predictions
    )

    print(
        f"\nAccuracy: "
        f"{accuracy * 100:.2f}%"
    )

    print("\nClassification Report:")

    print(
        classification_report(
            y_test,
            predictions
        )
    )

    os.makedirs(
        os.path.dirname(MODEL_FILE),
        exist_ok=True
    )

    joblib.dump(
        model,
        MODEL_FILE
    )

    with open(
        FEATURE_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            FEATURE_NAMES,
            f,
            indent=2
        )

    print(
        "\nModel saved:"
    )

    print(
        MODEL_FILE
    )

    print(
        "\nFeature list saved:"
    )

    print(
        FEATURE_FILE
    )


if __name__ == "__main__":
    train_model()