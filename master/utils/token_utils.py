"""Signed access token helpers for Master Pi API authentication."""

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from master.config import Config

TOKEN_SALT = "master-pi-access-token"
_REVOKED_TOKENS = set()


def _serializer():
    return URLSafeTimedSerializer(Config.SECRET_KEY)


def create_access_token(user, source):
    payload = {
        "user_id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "source": source,
    }
    return _serializer().dumps(payload, salt=TOKEN_SALT)


def revoke_access_token(token):
    _REVOKED_TOKENS.add(token)


def is_access_token_revoked(token):
    return token in _REVOKED_TOKENS


def verify_access_token(token):
    if is_access_token_revoked(token):
        return None, "Access token has been revoked"
    try:
        return _serializer().loads(
            token,
            salt=TOKEN_SALT,
            max_age=Config.TOKEN_MAX_AGE_SECONDS,
        ), None
    except SignatureExpired:
        return None, "Access token has expired"
    except BadSignature:
        return None, "Invalid access token"
