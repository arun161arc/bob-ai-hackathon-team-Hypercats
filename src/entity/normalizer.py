import re


class EntityNormalizer:

    @staticmethod
    def normalize_phone(value):

        if value is None:
            return None

        value = str(value).strip()

        digits = re.sub(
            r"\D",
            "",
            value
        )

        # Indian number with country code
        if digits.startswith("91") and len(digits) == 12:
            digits = digits[2:]

        # Standard Indian mobile number
        if len(digits) == 10:
            return "+91" + digits

        return "+" + digits if digits else None

    @staticmethod
    def normalize_imei(value):

        if value is None:
            return None

        value = re.sub(
            r"\D",
            "",
            str(value)
        )

        if len(value) == 15:
            return value

        return value

    @staticmethod
    def normalize_account(value):

        if value is None:
            return None

        value = str(value).strip().upper()

        value = re.sub(
            r"\s+",
            "",
            value
        )

        return value

    @staticmethod
    def normalize_tower(value):

        if value is None:
            return None

        return str(value).strip().upper()

    @staticmethod
    def normalize_person(value):

        if value is None:
            return None

        value = str(value).strip().upper()

        value = re.sub(
            r"\s+",
            " ",
            value
        )

        return value

    @staticmethod
    def normalize_generic(value):

        if value is None:
            return None

        return str(value).strip().upper()