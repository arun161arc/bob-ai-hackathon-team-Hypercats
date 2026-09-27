import csv
import json
import os
import sys
import hashlib

import networkx as nx


CURRENT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

SRC_DIR = os.path.dirname(
    CURRENT_DIR
)

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


from entity.entity_resolver import EntityResolver


class InvestigationGraphBuilder:

    def __init__(self):

        self.graph = nx.MultiDiGraph()

        self.resolver = EntityResolver()

        self.entity_lookup = {}

    # -----------------------------------------------------
    # LOAD CANONICAL ENTITIES
    # -----------------------------------------------------

    def load_entities(self, path):

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as file:

            entities = json.load(file)

        for entity in entities:

            key = (
                entity["entity_type"],
                entity["canonical_value"]
            )

            self.entity_lookup[key] = (
                entity["entity_id"]
            )

            self.graph.add_node(
                entity["entity_id"],
                entity_type=entity["entity_type"],
                label=entity["canonical_value"],
                evidence_ids=entity.get(
                    "evidence_ids",
                    []
                ),
                source_types=entity.get(
                    "source_types",
                    []
                )
            )

    # -----------------------------------------------------
    # FIND ENTITY
    # -----------------------------------------------------

    def get_entity_id(
        self,
        entity_type,
        value
    ):

        if value is None:
            return None

        entity = {
            "entity_type": entity_type,
            "raw_value": str(value)
        }

        resolved = self.resolver.resolve(
            entity
        )

        key = (
            resolved["entity_type"],
            resolved["canonical_value"]
        )

        return self.entity_lookup.get(key)

    # -----------------------------------------------------
    # ADD RELATIONSHIP
    # -----------------------------------------------------

    def add_relationship(
        self,
        source,
        target,
        relationship,
        evidence_id,
        timestamp=None,
        properties=None
    ):

        if not source or not target:
            return

        properties = properties or {}

        edge_id = hashlib.sha256(
            f"{source}|{target}|"
            f"{relationship}|{evidence_id}".encode()
        ).hexdigest()[:16]

        self.graph.add_edge(
            source,
            target,
            key=edge_id,
            relationship=relationship,
            evidence_id=evidence_id,
            timestamp=timestamp,
            evidence_status="OBSERVED",
            **properties
        )

    # -----------------------------------------------------
    # PROCESS CDR
    # -----------------------------------------------------

    def process_cdr(self, records):

        for index, record in enumerate(
            records,
            start=1
        ):

            evidence_id = record.get(
                "evidence_id"
            )

            if not evidence_id:
                evidence_id = (
                    f"CDR-{index:06d}"
                )

            caller = self.get_entity_id(
                "PHONE",
                record.get("caller")
            )

            called = self.get_entity_id(
                "PHONE",
                record.get("called")
            )

            imei = self.get_entity_id(
                "IMEI",
                record.get("imei")
            )

            tower = self.get_entity_id(
                "TOWER",
                record.get("tower_id")
            )

            timestamp = record.get(
                "timestamp"
            )

            # PHONE -> PHONE
            self.add_relationship(
                caller,
                called,
                "CALLED",
                evidence_id,
                timestamp,
                {
                    "duration_seconds":
                        record.get(
                            "duration_seconds"
                        ),
                    "call_type":
                        record.get(
                            "call_type"
                        )
                }
            )

            # PHONE -> IMEI
            self.add_relationship(
                caller,
                imei,
                "USED_HARDWARE",
                evidence_id,
                timestamp
            )

            # PHONE -> TOWER
            self.add_relationship(
                caller,
                tower,
                "CONNECTED_TO_TOWER",
                evidence_id,
                timestamp
            )

            # CALLED PHONE -> IMEI
            self.add_relationship(
                called,
                imei,
                "USED_HARDWARE",
                evidence_id,
                timestamp
            )

    # -----------------------------------------------------
    # PROCESS UPI
    # -----------------------------------------------------

    def process_upi(self, records):

        for index, record in enumerate(
            records,
            start=1
        ):

            evidence_id = record.get(
                "evidence_id"
            )

            if not evidence_id:

                evidence_id = (
                    f"UPI-{index:06d}"
                )

            sender = self.get_entity_id(
                "BANK_ACCOUNT",
                record.get(
                    "sender_account"
                )
            )

            receiver = self.get_entity_id(
                "BANK_ACCOUNT",
                record.get(
                    "receiver_account"
                )
            )

            transaction = self.get_entity_id(
                "TRANSACTION",
                record.get(
                    "transaction_id"
                )
            )

            timestamp = record.get(
                "timestamp"
            )

            amount = record.get(
                "amount_inr"
            )

            # ACCOUNT -> ACCOUNT
            self.add_relationship(
                sender,
                receiver,
                "TRANSFERRED_FUNDS",
                evidence_id,
                timestamp,
                {
                    "amount_inr": amount,
                    "transaction_id":
                        record.get(
                            "transaction_id"
                        ),
                    "status":
                        record.get(
                            "transaction_status"
                        )
                }
            )

            # ACCOUNT -> TRANSACTION
            self.add_relationship(
                sender,
                transaction,
                "INITIATED_TRANSACTION",
                evidence_id,
                timestamp,
                {
                    "amount_inr": amount
                }
            )

            # TRANSACTION -> ACCOUNT
            self.add_relationship(
                transaction,
                receiver,
                "RECEIVED_BY",
                evidence_id,
                timestamp
            )

    # -----------------------------------------------------
    # PROCESS DEVICE
    # -----------------------------------------------------

    def process_device(self, records):

        for index, record in enumerate(
            records,
            start=1
        ):

            evidence_id = record.get(
                "evidence_id"
            )

            if not evidence_id:

                evidence_id = (
                    f"DEVICE-{index:06d}"
                )

            phone = self.get_entity_id(
                "PHONE",
                record.get(
                    "phone_number"
                )
            )

            imei = self.get_entity_id(
                "IMEI",
                record.get(
                    "imei"
                )
            )

            tower = self.get_entity_id(
                "TOWER",
                record.get(
                    "tower_id"
                )
            )

            timestamp = record.get(
                "first_seen"
            )

            self.add_relationship(
                phone,
                imei,
                "ASSOCIATED_WITH_DEVICE",
                evidence_id,
                timestamp,
                {
                    "device_type":
                        record.get(
                            "device_type"
                        ),
                    "first_seen":
                        record.get(
                            "first_seen"
                        ),
                    "last_seen":
                        record.get(
                            "last_seen"
                        )
                }
            )

            self.add_relationship(
                imei,
                tower,
                "OBSERVED_AT_TOWER",
                evidence_id,
                timestamp
            )

    # -----------------------------------------------------
    # PROCESS COMPLAINT
    # -----------------------------------------------------

    def process_complaints(
        self,
        records
    ):

        for index, record in enumerate(
            records,
            start=1
        ):

            evidence_id = record.get(
                "evidence_id"
            )

            if not evidence_id:

                evidence_id = (
                    f"COMPLAINT-{index:06d}"
                )

            person = self.get_entity_id(
                "PERSON",
                record.get(
                    "victim_name"
                )
            )

            phone = self.get_entity_id(
                "PHONE",
                record.get(
                    "victim_phone"
                )
            )

            account = self.get_entity_id(
                "BANK_ACCOUNT",
                record.get(
                    "victim_account"
                )
            )

            caller = self.get_entity_id(
                "PHONE",
                record.get(
                    "reported_caller"
                )
            )

            timestamp = record.get(
                "complaint_timestamp"
            )

            self.add_relationship(
                person,
                phone,
                "OWNS_PHONE",
                evidence_id,
                timestamp
            )

            self.add_relationship(
                person,
                account,
                "OWNS_ACCOUNT",
                evidence_id,
                timestamp
            )

            self.add_relationship(
                person,
                caller,
                "REPORTED_CALLER",
                evidence_id,
                timestamp,
                {
                    "fraud_category":
                        record.get(
                            "fraud_category"
                        ),
                    "reported_amount_inr":
                        record.get(
                            "reported_amount_inr"
                        )
                }
            )

    # -----------------------------------------------------
    # SAVE GRAPH
    # -----------------------------------------------------

    def save_graph(
        self,
        output_path
    ):

        data = nx.node_link_data(
            self.graph
        )

        with open(
            output_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                indent=4,
                ensure_ascii=False
            )

    # -----------------------------------------------------
    # GRAPH SUMMARY
    # -----------------------------------------------------

    def summary(self):

        relationship_counts = {}

        for _, _, data in (
            self.graph.edges(
                data=True
            )
        ):

            relationship = data.get(
                "relationship",
                "UNKNOWN"
            )

            relationship_counts[
                relationship
            ] = (
                relationship_counts.get(
                    relationship,
                    0
                ) + 1
            )

        return {
            "nodes":
                self.graph.number_of_nodes(),

            "edges":
                self.graph.number_of_edges(),

            "relationship_counts":
                relationship_counts
        }


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