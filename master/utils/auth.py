"""Request authorization helpers for role-specific API contracts."""

from functools import wraps

from flask import g, request

from master.repositories.user_repository import UserRepository
from master.utils.response import error_response
from master.utils.token_utils import revoke_access_token, verify_access_token


def _get_bearer_token():
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        return None
    return authorization.removeprefix("Bearer ").strip()


def get_bearer_token():
    return _get_bearer_token()


def logout_current_token():
    token = _get_bearer_token()
    if not token:
        return None, error_response("Authorization bearer token is required", 401)

    _payload, token_error = verify_access_token(token)
    if token_error:
        return None, error_response(token_error, 401)

    revoke_access_token(token)
    return token, None


def get_request_user():
    if hasattr(g, "current_user"):
        return {
            "id": str(g.current_user["id"]),
            "role": g.current_user["role"],
        }

    token = _get_bearer_token()
    if token:
        payload, _error = verify_access_token(token)
        if payload:
            return {
                "id": str(payload["user_id"]),
                "role": payload["role"],
            }

    return {
        "id": "",
        "role": "",
    }


def get_verified_request_user():
    token = _get_bearer_token()
    if not token:
        return None, error_response("Authorization bearer token is required", 401)

    payload, token_error = verify_access_token(token)
    if token_error:
        return None, error_response(token_error, 401)

    user = UserRepository().find_by_id(payload["user_id"])
    if not user:
        return None, error_response("Authenticated user not found", 401)
    if user["role"] != payload["role"]:
        return None, error_response("Access token role no longer matches user", 403)

    g.current_user = {
        **user,
        "source": payload.get("source"),
    }
    return g.current_user, None


def require_roles(*allowed_roles):
    allowed = {role.lower() for role in allowed_roles}

    def decorator(route_handler):
        @wraps(route_handler)
        def wrapper(*args, **kwargs):
            current_user, auth_error = get_verified_request_user()
            if auth_error:
                return auth_error
            if current_user["role"] not in allowed:
                return error_response("Access denied for this role", 403)
            return route_handler(*args, **kwargs)

        return wrapper

    return decorator
