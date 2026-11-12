"""Generic validation for text questions. Rules are declared in content.py."""
from datetime import datetime

DIGITS = "0123456789"
TAJ_WEIGHTS = (2, 4, 6, 8, 10, 3, 5, 7)


def taj_check_ok(taj):
    """Hungarian TAJ check digit. Verify the weights against a known valid TAJ before enabling."""
    total = sum(int(d) * w for d, w in zip(taj[:8], TAJ_WEIGHTS))
    remainder = total % 11
    return remainder != 10 and remainder == int(taj[8])


def validate(question, value):
    """Returns None if the value is acceptable, otherwise the question's error_label."""
    if not value:
        return question["error_label"] if question.get("required") else None

    rules = question.get("validate", {})
    error = question["error_label"]

    if "length" in rules and len(value) != rules["length"]:
        return error
    if rules.get("digits_only") and not all(c in DIGITS for c in value):
        return error
    if "date_format" in rules:
        try:
            datetime.strptime(value, rules["date_format"])
        except ValueError:
            return error
    if rules.get("check_digit") and not taj_check_ok(value):
        return error
    return None