import re


class EntityExtractor:

    PHONE_PATTERN = re.compile(r"\+?\d{10,13}")
    IMEI_PATTERN = re.compile(r"\d{15}")

    def extract_from_record(self, record, evidence_type):

        entities = []

        if evidence_type == "CDR":

            self.add_entity(
                entities,
                "PHONE",
                record.get("caller"),
                record
            )

            self.add_entity(
                entities,
                "PHONE",
                record.get("called"),
                record
            )

            self.add_entity(
                entities,
                "IMEI",
                record.get("imei"),
                record
            )

            self.add_entity(
                entities,
                "TOWER",
                record.get("tower_id"),
                record
            )

        elif evidence_type == "UPI":

            self.add_entity(
                entities,
                "BANK_ACCOUNT",
                record.get("sender_account"),
                record
            )

            self.add_entity(
                entities,
                "BANK_ACCOUNT",
                record.get("receiver_account"),
                record
            )

            self.add_entity(
                entities,
                "TRANSACTION",
                record.get("transaction_id"),
                record
            )

            self.add_entity(
                entities,
                "REFERENCE",
                record.get("reference_id"),
                record
            )

        elif evidence_type == "COMPLAINT":

            self.add_entity(
                entities,
                "PERSON",
                record.get("victim_name"),
                record
            )

            self.add_entity(
                entities,
                "PHONE",
                record.get("victim_phone"),
                record
            )

            self.add_entity(
                entities,
                "BANK_ACCOUNT",
                record.get("victim_account"),
                record
            )

            self.add_entity(
                entities,
                "PHONE",
                record.get("reported_caller"),
                record
            )

        elif evidence_type == "DEVICE":

            self.add_entity(
                entities,
                "PHONE",
                record.get("phone_number"),
                record
            )

            self.add_entity(
                entities,
                "IMEI",
                record.get("imei"),
                record
            )

            self.add_entity(
                entities,
                "TOWER",
                record.get("tower_id"),
                record
            )

        return entities

    @staticmethod
    def add_entity(
        entities,
        entity_type,
        value,
        record
    ):

        if value is None:
            return

        value = str(value).strip()

        if not value:
            return

        entities.append({
            "entity_type": entity_type,
            "raw_value": value,
            "source_evidence_id": record.get(
                "evidence_id"
            ),
            "source_type": record.get(
                "evidence_type"
            )
        })