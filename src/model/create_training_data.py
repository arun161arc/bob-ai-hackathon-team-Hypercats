import os
import random
import pandas as pd


OUTPUT_FILE = os.path.join(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    ),
    "output",
    "model",
    "training_data.csv"
)


PATTERNS = [
    "MULE_CHAIN",
    "FUNNEL_ACCOUNT",
    "SHARED_DEVICE",
    "MULTI_HOP"
]


def random_value(low, high):

    return random.uniform(
        low,
        high
    )


def create_sample(pattern):

    # Normal baseline
    sample = {
        "degree": random.randint(1, 8),
        "in_degree": random.randint(0, 5),
        "out_degree": random.randint(0, 5),
        "betweenness": random_value(0.0, 0.08),
        "call_count": random.randint(0, 8),
        "fund_transfer_count": random.randint(0, 6),
        "total_received": random_value(0, 30000),
        "total_sent": random_value(0, 30000),
        "unique_senders": random.randint(0, 4),
        "unique_receivers": random.randint(0, 4),
        "shared_devices": random.randint(0, 1),
        "shared_towers": random.randint(0, 2),
        "phone_connections": random.randint(0, 3),
        "account_connections": random.randint(0, 3),
        "transaction_velocity": random_value(0, 1),
        "max_transfer_amount": random_value(500, 10000),
        "pattern": pattern
    }

    if pattern == "MULE_CHAIN":

        sample.update({
            "degree": random.randint(5, 15),
            "in_degree": random.randint(3, 8),
            "out_degree": random.randint(2, 7),
            "betweenness": random_value(0.10, 0.40),
            "fund_transfer_count":
                random.randint(5, 15),
            "unique_senders":
                random.randint(3, 8),
            "unique_receivers":
                random.randint(2, 7),
            "total_received":
                random_value(20000, 150000),
            "total_sent":
                random_value(15000, 140000),
            "transaction_velocity":
                random_value(0.5, 1.0)
        })

    elif pattern == "FUNNEL_ACCOUNT":

        sample.update({
            "degree": random.randint(8, 25),
            "in_degree": random.randint(8, 20),
            "out_degree": random.randint(1, 4),
            "betweenness": random_value(0.08, 0.30),
            "fund_transfer_count":
                random.randint(8, 25),
            "unique_senders":
                random.randint(8, 20),
            "unique_receivers":
                random.randint(1, 4),
            "total_received":
                random_value(50000, 300000),
            "total_sent":
                random_value(5000, 80000)
        })

    elif pattern == "SHARED_DEVICE":

        sample.update({
            "degree": random.randint(4, 12),
            "shared_devices":
                random.randint(2, 5),
            "shared_towers":
                random.randint(1, 4),
            "phone_connections":
                random.randint(3, 10),
            "call_count":
                random.randint(5, 20),
            "fund_transfer_count":
                random.randint(0, 5)
        })

    elif pattern == "MULTI_HOP":

        sample.update({
            "degree": random.randint(6, 18),
            "in_degree": random.randint(2, 8),
            "out_degree": random.randint(3, 9),
            "betweenness": random_value(0.15, 0.50),
            "fund_transfer_count":
                random.randint(6, 18),
            "unique_senders":
                random.randint(2, 8),
            "unique_receivers":
                random.randint(3, 9),
            "transaction_velocity":
                random_value(0.6, 1.0),
            "total_received":
                random_value(30000, 200000),
            "total_sent":
                random_value(25000, 180000)
        })

    return sample


def main():

    random.seed(42)

    rows = []

    samples_per_pattern = 1000

    for pattern in PATTERNS:

        for _ in range(
            samples_per_pattern
        ):

            rows.append(
                create_sample(pattern)
            )

    df = pd.DataFrame(rows)

    os.makedirs(
        os.path.dirname(OUTPUT_FILE),
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("=" * 60)
    print("PHASE 4 — TRAINING DATA CREATION")
    print("=" * 60)

    print(
        f"\nTraining samples: {len(df)}"
    )

    print("\nClass distribution:")

    print(
        df["pattern"].value_counts()
    )

    print(
        f"\nSaved to:\n{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()