import os
import json


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


def load_predictions():

    if not os.path.exists(
        PREDICTIONS_FILE
    ):
        raise FileNotFoundError(
            f"Predictions file not found:\n"
            f"{PREDICTIONS_FILE}"
        )

    with open(
        PREDICTIONS_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


def generate_explanation(result):

    pattern = result.get(
        "predicted_pattern",
        "UNKNOWN"
    )

    confidence = result.get(
        "confidence",
        0
    )

    features = result.get(
        "features",
        {}
    )

    indicators = []

    degree = features.get(
        "degree",
        0
    )

    in_degree = features.get(
        "in_degree",
        0
    )

    out_degree = features.get(
        "out_degree",
        0
    )

    fund_transfers = features.get(
        "fund_transfer_count",
        0
    )

    unique_senders = features.get(
        "unique_senders",
        0
    )

    unique_receivers = features.get(
        "unique_receivers",
        0
    )

    shared_devices = features.get(
        "shared_devices",
        0
    )

    shared_towers = features.get(
        "shared_towers",
        0
    )

    total_received = features.get(
        "total_received",
        0
    )

    total_sent = features.get(
        "total_sent",
        0
    )

    betweenness = features.get(
        "betweenness",
        0
    )

    # -------------------------
    # PATTERN-SPECIFIC EXPLANATION
    # -------------------------

    if pattern == "MULE_CHAIN":

        if unique_senders >= 3:
            indicators.append(
                f"Connected to {unique_senders} "
                f"distinct sending entities."
            )

        if unique_receivers >= 2:
            indicators.append(
                f"Connected to {unique_receivers} "
                f"distinct receiving entities."
            )

        if fund_transfers >= 5:
            indicators.append(
                f"Observed {fund_transfers} "
                f"fund-transfer relationships."
            )

        if in_degree > 0 and out_degree > 0:
            indicators.append(
                "Shows both incoming and outgoing "
                "fund-flow relationships."
            )

    elif pattern == "FUNNEL_ACCOUNT":

        if in_degree >= 5:
            indicators.append(
                f"High incoming connectivity "
                f"({in_degree} incoming relationships)."
            )

        if unique_senders >= 5:
            indicators.append(
                f"Funds originate from "
                f"{unique_senders} distinct senders."
            )

        if total_received > total_sent:
            indicators.append(
                "Observed incoming value exceeds "
                "outgoing value in the extracted data."
            )

    elif pattern == "SHARED_DEVICE":

        if shared_devices >= 2:
            indicators.append(
                f"Associated with {shared_devices} "
                f"shared device identifiers."
            )

        if shared_towers >= 2:
            indicators.append(
                f"Associated with {shared_towers} "
                f"tower identifiers."
            )

        if degree >= 4:
            indicators.append(
                f"Has {degree} graph connections "
                "across the evidence network."
            )

    elif pattern == "MULTI_HOP":

        if in_degree >= 2 and out_degree >= 2:
            indicators.append(
                "Shows both incoming and outgoing "
                "fund-flow relationships."
            )

        if fund_transfers >= 5:
            indicators.append(
                f"Observed {fund_transfers} "
                f"fund-transfer relationships."
            )

        if unique_senders >= 2:
            indicators.append(
                f"Receives funds from "
                f"{unique_senders} distinct senders."
            )

        if unique_receivers >= 2:
            indicators.append(
                f"Sends funds toward "
                f"{unique_receivers} distinct receivers."
            )

    # General graph indicators

    if betweenness >= 0.10:

        indicators.append(
            "The entity occupies a relatively "
            "central position in the observed graph."
        )

    if degree >= 8:

        indicators.append(
            f"High graph connectivity observed "
            f"({degree} connections)."
        )

    if not indicators:

        indicators.append(
            "The model classification is based on "
            "the available graph features."
        )

    return {
        "pattern": pattern,
        "confidence": round(
            confidence,
            4
        ),
        "interpretation": (
            f"The model classified this entity "
            f"under the analytical pattern "
            f"'{pattern}'."
        ),
        "indicators": indicators,
        "analytical_note": (
            "This is an analytical model output "
            "based on the supplied synthetic evidence. "
            "It should be reviewed against the underlying "
            "records and is not, by itself, proof of wrongdoing."
        )
    }