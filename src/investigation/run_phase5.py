import os
import sys
import json


CURRENT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

if CURRENT_DIR not in sys.path:

    sys.path.insert(
        0,
        CURRENT_DIR
    )


from finding_explainer import (
    generate_explanation
)

from evidence_tracer import (
    get_entity_evidence,
    get_entity_connections
)

from case_brief import (
    generate_case_brief
)


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

PREDICTIONS_FILE = os.path.join(
    BASE_DIR,
    "output",
    "model",
    "predictions.json"
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "output",
    "investigation"
)

EXPLANATIONS_FILE = os.path.join(
    OUTPUT_DIR,
    "finding_explanations.json"
)


def main():

    print()
    print("=" * 70)
    print("              CHANAKYA-GRAPH")
    print("                 PHASE 5")
    print("       INVESTIGATION INTELLIGENCE")
    print("=" * 70)

    # -------------------------
    # LOAD PREDICTIONS
    # -------------------------

    if not os.path.exists(
        PREDICTIONS_FILE
    ):

        print(
            "\nERROR: predictions.json not found."
        )

        print(
            "\nRun Phase 4 first:"
        )

        print(
            "python src/model/run_phase4.py"
        )

        return

    with open(
        PREDICTIONS_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        predictions = json.load(f)

    print(
        f"\nLoaded {len(predictions)} "
        f"model predictions."
    )

    # -------------------------
    # CREATE EXPLANATIONS
    # -------------------------

    print(
        "\nGenerating evidence-linked explanations..."
    )

    explanations = []

    evidence_lookup = {}

    for result in predictions:

        entity_id = result.get(
            "entity_id"
        )

        explanation = generate_explanation(
            result
        )

        entity_evidence = (
            get_entity_evidence(
                entity_id
            )
        )

        connections = (
            get_entity_connections(
                entity_id
            )
        )

        if entity_evidence is None:

            entity_evidence = {
                "entity_id": entity_id,
                "entity_type": result.get(
                    "entity_type"
                ),
                "canonical_value": "",
                "evidence_ids": []
            }

        combined = {
            "entity_id": entity_id,

            "entity_type": result.get(
                "entity_type"
            ),

            "predicted_pattern": result.get(
                "predicted_pattern"
            ),

            "confidence": result.get(
                "confidence"
            ),

            "interpretation": explanation[
                "interpretation"
            ],

            "indicators": explanation[
                "indicators"
            ],

            "analytical_note": explanation[
                "analytical_note"
            ],

            "canonical_value":
                entity_evidence.get(
                    "canonical_value",
                    ""
                ),

            "evidence_ids":
                entity_evidence.get(
                    "evidence_ids",
                    []
                ),

            "connections":
                connections
        }

        explanations.append(
            combined
        )

        evidence_lookup[
            entity_id
        ] = {
            "evidence_ids":
                entity_evidence.get(
                    "evidence_ids",
                    []
                ),

            "connections":
                connections
        }

    # -------------------------
    # SAVE EXPLANATIONS
    # -------------------------

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    with open(
        EXPLANATIONS_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            explanations,
            f,
            indent=2,
            default=str
        )

    print(
        f"\nFinding explanations saved:"
    )

    print(
        EXPLANATIONS_FILE
    )

    # -------------------------
    # GENERATE CASE BRIEF
    # -------------------------

    print(
        "\nGenerating investigation case brief..."
    )

    brief = generate_case_brief(
        predictions,
        evidence_lookup
    )

    print(
        "\nCase brief generated successfully."
    )

    # -------------------------
    # DISPLAY TOP FINDING
    # -------------------------

    if explanations:

        top = explanations[0]

        print()
        print("=" * 70)
        print("TOP ANALYTICAL FINDING")
        print("=" * 70)

        print(
            f"\nEntity: "
            f"{top['entity_id']}"
        )

        print(
            f"Type: "
            f"{top['entity_type']}"
        )

        print(
            f"Pattern: "
            f"{top['predicted_pattern']}"
        )

        print(
            f"Confidence: "
            f"{top['confidence'] * 100:.2f}%"
        )

        print(
            "\nWhy this finding was produced:"
        )

        for indicator in top[
            "indicators"
        ]:

            print(
                f"  • {indicator}"
            )

        print(
            "\nEvidence:"
        )

        for evidence_id in top[
            "evidence_ids"
        ][:10]:

            print(
                f"  • {evidence_id}"
            )

    print()
    print("=" * 70)
    print("              PHASE 5 COMPLETE")
    print("=" * 70)

    print(
        "\nOutput directory:"
    )

    print(
        OUTPUT_DIR
    )


if __name__ == "__main__":
    main()