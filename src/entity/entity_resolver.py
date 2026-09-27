import hashlib

from entity.normalizer import EntityNormalizer


class EntityResolver:

    def __init__(self):

        self.normalizer = EntityNormalizer()

    def resolve(self, entity):

        entity_type = entity[
            "entity_type"
        ]

        raw_value = entity[
            "raw_value"
        ]

        canonical_value = self.normalize(
            entity_type,
            raw_value
        )

        entity_id = self.generate_entity_id(
            entity_type,
            canonical_value
        )

        return {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "raw_value": raw_value,
            "canonical_value": canonical_value,
            "source_evidence_id":
                entity.get(
                    "source_evidence_id"
                ),
            "source_type":
                entity.get(
                    "source_type"
                ),
            "evidence_status": "OBSERVED"
        }

    def normalize(
        self,
        entity_type,
        value
    ):

        if entity_type == "PHONE":

            return self.normalizer.normalize_phone(
                value
            )

        if entity_type == "IMEI":

            return self.normalizer.normalize_imei(
                value
            )

        if entity_type == "BANK_ACCOUNT":

            return self.normalizer.normalize_account(
                value
            )

        if entity_type == "TOWER":

            return self.normalizer.normalize_tower(
                value
            )

        if entity_type == "PERSON":

            return self.normalizer.normalize_person(
                value
            )

        return self.normalizer.normalize_generic(
            value
        )

    @staticmethod
    def generate_entity_id(
        entity_type,
        canonical_value
    ):

        raw = (
            f"{entity_type}|"
            f"{canonical_value}"
        )

        digest = hashlib.sha256(
            raw.encode("utf-8")
        ).hexdigest()[:16]

        return (
            f"{entity_type}:{digest}"
        )