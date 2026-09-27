import os
import json
from datetime import datetime


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "output",
    "investigation"
)

BRIEF_FILE = os.path.join(
    OUTPUT_DIR,
    "case_brief.json"
)

BRIEF_TEXT_FILE = os.path.join(
    OUTPUT_DIR,
    "case_brief.txt"
)


def generate_case_brief(
    predictions,
    evidence_lookup
):

    sorted_predictions = sorted(
        predictions,
        key=lambda x: x.get(
            "confidence",
            0
        ),
        reverse=True
    )

    top_findings = []

    for result in sorted_predictions[:10]:

        entity_id = result.get(
            "entity_id"
        )

        explanation = evidence_lookup.get(
            entity_id,
            {}
        )

        top_findings.append({
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
            "evidence_ids": explanation.get(
                "evidence_ids",
                []
            ),
            "connections": explanation.get(
                "connections",
                []
            )
        })

    brief = {
        "case_id": "DEMO-CYB-2026-0001",

        "generated_at": datetime.now().isoformat(),

        "data_classification": "SYNTHETIC_DEMO",

        "purpose": (
            "AI-assisted cyber-fraud investigation "
            "analysis using synthetic evidence."
        ),

        "top_analytical_findings": top_findings,

        "methodology": [
            "Evidence ingestion",
            "Entity extraction",
            "Entity normalization",
            "Investigation graph construction",
            "Graph feature extraction",
            "Machine-learning pattern classification",
            "Evidence-linked explanation"
        ],

        "important_note": (
            "The findings are analytical outputs generated "
            "from synthetic demonstration data. They should "
            "be independently reviewed against source records "
            "before any investigative or legal action."
        )
    }

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    with open(
        BRIEF_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            brief,
            f,
            indent=2,
            default=str
        )

    # -------------------------
    # HUMAN-READABLE REPORT
    # -------------------------

    lines = []

    lines.append(
        "=" * 70
    )

    lines.append(
        "CHANAKYA-GRAPH — INVESTIGATION CASE BRIEF"
    )

    lines.append(
        "=" * 70
    )

    lines.append(
        f"\nCase ID: {brief['case_id']}"
    )

    lines.append(
        f"Generated: {brief['generated_at']}"
    )

    lines.append(
        f"Data Class: {brief['data_classification']}"
    )

    lines.append(
        "\nPURPOSE"
    )

    lines.append(
        brief["purpose"]
    )

    lines.append(
        "\nTOP ANALYTICAL FINDINGS"
    )

    lines.append(
        "-" * 70
    )

    for index, finding in enumerate(
        top_findings,
        start=1
    ):

        lines.append(
            f"\n{index}. {finding['entity_id']}"
        )

        lines.append(
            f"   Entity Type: "
            f"{finding['entity_type']}"
        )

        lines.append(
            f"   Pattern: "
            f"{finding['predicted_pattern']}"
        )

        lines.append(
            f"   Confidence: "
            f"{finding['confidence'] * 100:.2f}%"
        )

        lines.append(
            f"   Evidence IDs: "
            f"{', '.join(map(str, finding['evidence_ids'][:10]))}"
        )

        lines.append(
            f"   Connections: "
            f"{len(finding['connections'])}"
        )

    lines.append(
        "\nMETHODOLOGY"
    )

    lines.append(
        "-" * 70
    )

    for method in brief[
        "methodology"
    ]:

        lines.append(
            f"• {method}"
        )

    lines.append(
        "\nIMPORTANT NOTE"
    )

    lines.append(
        brief["important_note"]
    )

    lines.append(
        "\n" + "=" * 70
    )

    with open(
        BRIEF_TEXT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(
            "\n".join(lines)
        )

    return brief