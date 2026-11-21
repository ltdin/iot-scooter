from master.utils.response import error_response, success_response
from master.utils.password_utils import hash_password, verify_password
from master.utils.token_utils import create_access_token
from master.utils.validators import (
    is_valid_email,
    is_valid_password,
    is_valid_source,
    require_fields,
)
from master.config import Config
from master.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, user_repository=None):
        self.user_repository = user_repository or UserRepository()

    def _build_user_data(self, user, source=None):
        user_data = {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            "phone": user["phone"],
            "email": user["email"],
            "balance": user["balance"],
        }

        if source is not None:
            user_data["source"] = source

        return user_data

    def register_customer(self, data):
        missing = require_fields(
            data,
            ["username", "password", "first_name", "last_name", "phone", "email"],
        )
        if missing:
            return error_response(f"Missing required fields: {', '.join(missing)}", 400)

        if not is_valid_email(data["email"]):
            return error_response("Invalid email address", 400)
        if not is_valid_password(data["password"]):
            return error_response("Password must be at least 8 characters", 400)
        if self.user_repository.find_by_username(data["username"]):
            return error_response("Username already exists", 409)
        if self.user_repository.find_by_email(data["email"]):
            return error_response("Email already exists", 409)

        customer = self.user_repository.create_customer(
            {
                "username": data["username"],
                "password_hash": hash_password(data["password"]),
                "first_name": data["first_name"],
                "last_name": data["last_name"],
                "phone": data["phone"],
                "email": data["email"],
                "balance": data.get("balance", 0),
            }
        )

        return success_response("Customer registered", customer, 201)

    def login(self, data):
        missing = require_fields(data, ["username", "password", "source"])
        if missing:
            return error_response(f"Missing required fields: {', '.join(missing)}", 400)

        source = str(data["source"]).upper()
        if not is_valid_source(source):
            return error_response("Invalid source. Use AP or MP.", 400)

        user = self.user_repository.find_by_username(data["username"])
        if not user or not verify_password(data["password"], user["password_hash"]):
            return error_response("Invalid username or password", 401)

        role = user["role"]
        if role == "admin" and source != "MP":
            return error_response("Admin can only login from Master Pi", 403)
        if role in {"customer", "engineer"} and source != "AP":
            return error_response("Customers and engineers can only login from Agent Pi", 403)

        user_data = self._build_user_data(user, source)

        return success_response(
            "Login successful",
            {
                "access_token": create_access_token(user, source),
                "token_type": "Bearer",
                "expires_in": Config.TOKEN_MAX_AGE_SECONDS,
                "user": user_data,
            },
        )

    def get_current_user(self, user_id):
        user = self.user_repository.find_by_id(user_id)
        if not user:
            return error_response("User not found", 404)

        return success_response(
            "Current user retrieved",
            self._build_user_data(user),
        )

    def list_customers(self):
        customers = self.user_repository.list_customers()
        return success_response("Customers retrieved", customers)

    def logout(self):
        return success_response(
            "Logout successful",
            {"revoked": True},
        )