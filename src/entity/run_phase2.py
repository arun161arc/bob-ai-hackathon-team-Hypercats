import csv
import json
import os
import sys


# ---------------------------------------------------------
# Make src available for imports
# ---------------------------------------------------------

CURRENT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

SRC_DIR = os.path.dirname(
    CURRENT_DIR
)

if SRC_DIR not in sys.path:
    sys.path.insert(
        0,
        SRC_DIR
    )


from entity.entity_extractor import EntityExtractor
from entity.entity_resolver import EntityResolver


# ---------------------------------------------------------
# PATHS
# ---------------------------------------------------------

DATA_DIR = os.path.join(
    SRC_DIR,
    "data"
)

OUTPUT_DIR = os.path.join(
    SRC_DIR,
    "output",
    "entities"
)

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


# ---------------------------------------------------------
# INPUT FILES
# ---------------------------------------------------------

FILES = {

    "CDR":
        "cdr_records.csv",

    "UPI":
        "upi_transactions.csv",

    "COMPLAINT":
        "complaints.csv",

    "DEVICE":
        "device_records.csv"
}


# ---------------------------------------------------------
# CSV LOADER
# ---------------------------------------------------------

def load_csv(path):

    with open(
        path,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        return list(
            csv.DictReader(file)
        )


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():

    print()
    print("=" * 70)
    print(
        "CHANAKYA-GRAPH — PHASE 2"
    )
    print(
        "ENTITY EXTRACTION + NORMALIZATION + RESOLUTION"
    )
    print("=" * 70)

    print()
    print(
        f"Input directory : {DATA_DIR}"
    )

    print(
        f"Output directory: {OUTPUT_DIR}"
    )

    extractor = EntityExtractor()

    resolver = EntityResolver()

    all_entities = []

    processed_records = 0

    missing_files = []

    # -----------------------------------------------------
    # PROCESS ALL EVIDENCE TYPES
    # -----------------------------------------------------

    for evidence_type, filename in FILES.items():

        file_path = os.path.join(
            DATA_DIR,
            filename
        )

        print()
        print("-" * 70)
        print(
            f"Evidence Type: {evidence_type}"
        )
        print(
            f"File         : {filename}"
        )

        if not os.path.exists(file_path):

            print(
                "[WARNING] File not found"
            )

            missing_files.append(
                filename
            )

            continue

        records = load_csv(
            file_path
        )

        print(
            f"Records      : {len(records)}"
        )

        # -------------------------------------------------
        # PROCESS EACH RECORD
        # -------------------------------------------------

        for index, record in enumerate(
            records,
            start=1
        ):

            processed_records += 1

            # ---------------------------------------------
            # Evidence ID
            # ---------------------------------------------

            evidence_id = record.get(
                "evidence_id"
            )

            if not evidence_id:

                evidence_id = (
                    f"{evidence_type}-"
                    f"{index:06d}"
                )

                record[
                    "evidence_id"
                ] = evidence_id

            record[
                "evidence_type"
            ] = evidence_type

            # ---------------------------------------------
            # EXTRACT
            # ---------------------------------------------

            extracted_entities = (
                extractor.extract_from_record(
                    record,
                    evidence_type
                )
            )

            # ---------------------------------------------
            # NORMALIZE + RESOLVE
            # ---------------------------------------------

            for entity in extracted_entities:

                resolved_entity = (
                    resolver.resolve(
                        entity
                    )
                )

                all_entities.append(
                    resolved_entity
                )

    # -----------------------------------------------------
    # CANONICAL REGISTRY
    # -----------------------------------------------------

    canonical_registry = {}

    for entity in all_entities:

        entity_id = entity[
            "entity_id"
        ]

        if entity_id not in canonical_registry:

            canonical_registry[
                entity_id
            ] = {

                "entity_id":
                    entity_id,

                "entity_type":
                    entity[
                        "entity_type"
                    ],

                "canonical_value":
                    entity[
                        "canonical_value"
                    ],

                "evidence_ids":
                    [],

                "source_types":
                    []
            }

        evidence_id = entity[
            "source_evidence_id"
        ]

        source_type = entity[
            "source_type"
        ]

        if (
            evidence_id
            and evidence_id not in
            canonical_registry[
                entity_id
            ]["evidence_ids"]
        ):

            canonical_registry[
                entity_id
            ]["evidence_ids"].append(
                evidence_id
            )

        if (
            source_type
            and source_type not in
            canonical_registry[
                entity_id
            ]["source_types"]
        ):

            canonical_registry[
                entity_id
            ]["source_types"].append(
                source_type
            )

    # -----------------------------------------------------
    # OUTPUT 1
    # Entity occurrences
    # -----------------------------------------------------

    occurrences_file = os.path.join(
        OUTPUT_DIR,
        "entity_occurrences.json"
    )

    with open(
        occurrences_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            all_entities,
            file,
            indent=4,
            ensure_ascii=False
        )

    # -----------------------------------------------------
    # OUTPUT 2
    # Canonical entities
    # -----------------------------------------------------

    canonical_file = os.path.join(
        OUTPUT_DIR,
        "canonical_entities.json"
    )

    canonical_entities = list(
        canonical_registry.values()
    )

    with open(
        canonical_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            canonical_entities,
            file,
            indent=4,
            ensure_ascii=False
        )

    # -----------------------------------------------------
    # STATISTICS
    # -----------------------------------------------------

    entity_type_counts = {}

    for entity in canonical_entities:

        entity_type = entity[
            "entity_type"
        ]

        entity_type_counts[
            entity_type
        ] = (
            entity_type_counts.get(
                entity_type,
                0
            ) + 1
        )

    # -----------------------------------------------------
    # MULTI-SOURCE ENTITIES
    # -----------------------------------------------------

    multi_source_entities = []

    for entity in canonical_entities:

        if len(
            entity["source_types"]
        ) > 1:

            multi_source_entities.append(
                entity
            )

    multi_source_file = os.path.join(
        OUTPUT_DIR,
        "multi_source_entities.json"
    )

    with open(
        multi_source_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            multi_source_entities,
            file,
            indent=4,
            ensure_ascii=False
        )

    # -----------------------------------------------------
    # DISPLAY RESULTS
    # -----------------------------------------------------

    print()
    print("=" * 70)
    print("PHASE 2 RESULTS")
    print("=" * 70)

    print()
    print(
        f"Processed records       : "
        f"{processed_records}"
    )

    print(
        f"Entity occurrences      : "
        f"{len(all_entities)}"
    )

    print(
        f"Canonical entities      : "
        f"{len(canonical_entities)}"
    )

    print(
        f"Multi-source entities   : "
        f"{len(multi_source_entities)}"
    )

    print()
    print(
        "CANONICAL ENTITY TYPES"
    )

    print("-" * 70)

    for entity_type, count in sorted(
        entity_type_counts.items()
    ):

        print(
            f"{entity_type:<20}"
            f": {count}"
        )

    # -----------------------------------------------------
    # OUTPUT FILES
    # -----------------------------------------------------

    print()
    print(
        "OUTPUT FILES"
    )

    print("-" * 70)

    print(
        occurrences_file
    )

    print(
        canonical_file
    )

    print(
        multi_source_file
    )

    # -----------------------------------------------------
    # WARNINGS
    # -----------------------------------------------------

    if missing_files:

        print()
        print(
            "WARNING: Missing files"
        )

        for filename in missing_files:

            print(
                f"  - {filename}"
            )

    # -----------------------------------------------------
    # SUCCESS
    # -----------------------------------------------------

    print()
    print("=" * 70)
    print(
        "PHASE 2 ENTITY PROCESSING SUCCESSFUL"
    )
    print("=" * 70)
    print()


if __name__ == "__main__":

    main()