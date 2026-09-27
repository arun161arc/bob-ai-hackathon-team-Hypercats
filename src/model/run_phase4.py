import os
import sys


CURRENT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

if CURRENT_DIR not in sys.path:
    sys.path.insert(
        0,
        CURRENT_DIR
    )


from create_training_data import main as create_training_data
from train_model import train_model as train_model
from predict_patterns import main as predict_patterns


def main():

    print()
    print("=" * 70)
    print("              CHANAKYA-GRAPH")
    print("                 PHASE 4")
    print("          AI FRAUD PATTERN MODEL")
    print("=" * 70)

    print("\n[1/3] Creating labeled synthetic training data...")

    create_training_data()

    print("\n[2/3] Training ML model...")

    train_model()

    print("\n[3/3] Running model against Phase 3 graph...")

    predict_patterns()

    print()
    print("=" * 70)
    print("              PHASE 4 COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()