from decimal import Decimal, InvalidOperation
from uuid import uuid4

from master.config import Config
from master.repositories.payment_repository import PaymentRepository
from master.repositories.user_repository import UserRepository
from master.utils.response import error_response, success_response
from master.utils.validators import require_fields

try:
    import stripe
except ImportError:  # pragma: no cover - depends on installed requirements
    stripe = None


class PaymentService:
    def __init__(self, payment_repository=None, user_repository=None):
        self.payment_repository = payment_repository or PaymentRepository()
        self.user_repository = user_repository or UserRepository()

    def _parse_amount(self, amount):
        try:
            parsed = Decimal(str(amount)).quantize(Decimal("0.01"))
        except (InvalidOperation, TypeError, ValueError):
            return None
        if parsed <= 0:
            return None
        return parsed

    def get_config(self):
        return success_response(
            "Stripe payment config retrieved",
            {
                "publishable_key": Config.STRIPE_PUBLISHABLE_KEY,
                "publishable_key_configured": bool(Config.STRIPE_PUBLISHABLE_KEY),
                "currency": Config.STRIPE_CURRENCY,
                "mock_mode": Config.STRIPE_MOCK_MODE,
            },
        )

    def create_top_up(self, data):
        missing = require_fields(data, ["user_id", "amount"])
        if missing:
            return error_response(f"Missing required fields: {', '.join(missing)}", 400)

        amount = self._parse_amount(data["amount"])
        if amount is None:
            return error_response("Top-up amount must be greater than zero", 400)

        currency = data.get("currency", Config.STRIPE_CURRENCY).lower()
        payment_intent = None
        provider = "stripe"

        if Config.STRIPE_MOCK_MODE or not Config.STRIPE_SECRET_KEY:
            payment_intent_id = f"pi_mock_{uuid4().hex}"
            client_secret = f"{payment_intent_id}_secret_mock"
            provider = "stripe_mock"
        else:
            if stripe is None:
                return error_response("Stripe package is not installed", 500)
            stripe.api_key = Config.STRIPE_SECRET_KEY
            payment_intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),
                currency=currency,
                metadata={"user_id": str(data["user_id"])},
                automatic_payment_methods={"enabled": True},
            )
            payment_intent_id = payment_intent["id"]
            client_secret = payment_intent["client_secret"]

        transaction = self.payment_repository.create(
            {
                "user_id": data["user_id"],
                "stripe_payment_intent_id": payment_intent_id,
                "amount": amount,
                "currency": currency,
                "status": "Pending",
                "provider": provider,
            }
        )
        return success_response(
            "Top-up payment created",
            {
                "transaction": transaction,
                "payment_intent_id": payment_intent_id,
                "client_secret": client_secret,
                "provider": provider,
                "stripe_status": payment_intent["status"] if payment_intent else "mock_pending",
            },
            201,
        )

    def list_user_top_ups(self, user_id):
        transactions = self.payment_repository.list_for_user(user_id)
        return success_response("Top-up transactions retrieved", transactions)

    def get_user_top_up(self, user_id, payment_intent_id):
        transaction = self.payment_repository.find_by_payment_intent(payment_intent_id)
        if not transaction:
            return error_response("Payment transaction not found", 404)
        if str(transaction["user_id"]) != str(user_id):
            return error_response("You can only view your own payment transaction", 403)
        return success_response("Top-up transaction retrieved", transaction)

    def mark_top_up_succeeded(self, payment_intent_id):
        transaction = self.payment_repository.find_by_payment_intent(payment_intent_id)
        if not transaction:
            return error_response("Payment transaction not found", 404)
        if transaction["status"] == "Succeeded":
            user = self.user_repository.find_by_id(transaction["user_id"])
            return success_response(
                "Top-up already applied",
                {"transaction": transaction, "user": user},
            )

        updated_transaction = self.payment_repository.update_status(
            transaction["id"],
            "Succeeded",
        )
        user = self.user_repository.add_balance(
            transaction["user_id"],
            transaction["amount"],
        )
        return success_response(
            "Top-up applied",
            {"transaction": updated_transaction, "user": user},
        )

    def confirm_mock_top_up(self, data):
        missing = require_fields(data, ["payment_intent_id"])
        if missing:
            return error_response("Missing required fields: payment_intent_id", 400)
        if not Config.STRIPE_MOCK_MODE:
            return error_response("Mock top-up confirmation is disabled", 403)
        return self.mark_top_up_succeeded(data["payment_intent_id"])
    
    def create_checkout_session(self, data):
        missing = require_fields(data, ["user_id", "amount"])
        if missing:
            return error_response(f"Missing required fields: {', '.join(missing)}", 400)

        amount = self._parse_amount(data["amount"])
        if amount is None:
            return error_response("Top-up amount must be greater than zero", 400)

        if stripe is None:
            return error_response("Stripe package is not installed", 500)

        if not Config.STRIPE_SECRET_KEY:
            return error_response("Stripe secret key is not configured", 500)

        stripe.api_key = Config.STRIPE_SECRET_KEY

        currency = data.get("currency", Config.STRIPE_CURRENCY).lower()
        amount_cents = int(amount * 100)

        transaction = self.payment_repository.create(
            {
                "user_id": data["user_id"],
                "stripe_payment_intent_id": f"checkout_pending_{uuid4().hex}",
                "amount": amount,
                "currency": currency,
                "status": "Pending",
                "provider": "stripe_checkout",
            }
        )

        frontend_base_url = getattr(
            Config,
            "FRONTEND_BASE_URL",
            "http://127.0.0.1:5500/frontend/agent",
        ).rstrip("/")

        success_url = (
            f"{frontend_base_url}/payment-success.html"
            "?session_id={CHECKOUT_SESSION_ID}"
        )
        cancel_url = f"{frontend_base_url}/customer.html"

        try:
            session = stripe.checkout.Session.create(
                mode="payment",
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": currency,
                            "product_data": {
                                "name": "Scooter Share Account Top-up",
                            },
                            "unit_amount": amount_cents,
                        },
                        "quantity": 1,
                    }
                ],
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    "transaction_id": str(transaction["id"]),
                    "user_id": str(data["user_id"]),
                    "purpose": "top_up",
                },
            )
        except Exception as error:
            return error_response(f"Could not create Stripe Checkout session: {error}", 500)

        updated_transaction = self.payment_repository.update_payment_intent_id(
            transaction["id"],
            session["id"],
        )

        return success_response(
            "Stripe Checkout session created",
            {
                "transaction": updated_transaction,
                "checkout_session_id": session["id"],
                "checkout_url": session["url"],
            },
            201,
        )

    def confirm_checkout_session(self, data):
        missing = require_fields(data, ["session_id"])
        if missing:
            return error_response("Missing required fields: session_id", 400)

        if stripe is None:
            return error_response("Stripe package is not installed", 500)

        if not Config.STRIPE_SECRET_KEY:
            return error_response("Stripe secret key is not configured", 500)

        stripe.api_key = Config.STRIPE_SECRET_KEY

        try:
            session = stripe.checkout.Session.retrieve(data["session_id"])
        except Exception as error:
            return error_response(f"Could not retrieve Stripe Checkout session: {error}", 500)

        if session["payment_status"] != "paid":
            return error_response("Stripe Checkout session has not been paid", 400)

        transaction = self.payment_repository.find_by_checkout_session(session["id"])
        if not transaction:
            return error_response("Payment transaction not found", 404)

        # if str(transaction["user_id"]) != str(data["user_id"]):
        #     return error_response("You can only confirm your own top-up", 403)

        if transaction["status"] == "Succeeded":
            user = self.user_repository.find_by_id(transaction["user_id"])
            return success_response(
                "Top-up already applied",
                {"transaction": transaction, "user": user},
            )

        updated_transaction = self.payment_repository.update_status(
            transaction["id"],
            "Succeeded",
        )
        user = self.user_repository.add_balance(
            transaction["user_id"],
            transaction["amount"],
        )

        return success_response(
            "Stripe Checkout top-up applied",
            {"transaction": updated_transaction, "user": user},
        )

    def handle_stripe_webhook(self, payload, signature):
        if stripe is None:
            return error_response("Stripe package is not installed", 500)
        if not Config.STRIPE_WEBHOOK_SECRET:
            return error_response("Stripe webhook secret is not configured", 500)

        try:
            event = stripe.Webhook.construct_event(
                payload,
                signature,
                Config.STRIPE_WEBHOOK_SECRET,
            )
        except Exception as error:
            return error_response(f"Invalid Stripe webhook: {error}", 400)

        if event["type"] == "payment_intent.payment_failed":
            payment_intent_id = event["data"]["object"]["id"]
            transaction = self.payment_repository.find_by_payment_intent(payment_intent_id)
            if transaction:
                updated = self.payment_repository.update_status(transaction["id"], "Failed")
                return success_response("Top-up marked failed", {"transaction": updated})
            return success_response("Stripe failed event received for unknown transaction")

        if event["type"] != "payment_intent.succeeded":
            return success_response("Stripe event ignored", {"event_type": event["type"]})

        payment_intent_id = event["data"]["object"]["id"]
        return self.mark_top_up_succeeded(payment_intent_id)
