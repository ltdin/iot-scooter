def require_fields(data, fields):
    return [field for field in fields if data.get(field) in (None, "")]


def is_valid_source(source):
    return source in {"AP", "MP"}


def is_valid_email(email):
    return isinstance(email, str) and "@" in email and "." in email.rsplit("@", 1)[-1]


def is_valid_password(password):
    return isinstance(password, str) and len(password) >= 8


def is_positive_number(value):
    try:
        return float(value) > 0
    except (TypeError, ValueError):
        return False


def is_non_empty_string(value):
    return isinstance(value, str) and bool(value.strip())


def is_valid_latitude(value):
    if value in (None, ""):
        return True
    try:
        return -90 <= float(value) <= 90
    except (TypeError, ValueError):
        return False


def is_valid_longitude(value):
    if value in (None, ""):
        return True
    try:
        return -180 <= float(value) <= 180
    except (TypeError, ValueError):
        return False
