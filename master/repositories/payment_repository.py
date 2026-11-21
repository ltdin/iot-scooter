from master.repositories.base_repository import BaseRepository


class PaymentRepository(BaseRepository):
    def create(self, payment_data):
        payment_id = self.execute(
            """
            INSERT INTO payment_transactions
                (user_id, stripe_payment_intent_id, amount, currency, status, provider)
            VALUES
                (%s, %s, %s, %s, %s, %s)
            """,
            (
                payment_data["user_id"],
                payment_data["stripe_payment_intent_id"],
                payment_data["amount"],
                payment_data["currency"],
                payment_data.get("status", "Pending"),
                payment_data.get("provider", "stripe"),
            ),
        )
        return self.find_by_id(payment_id)

    def find_by_id(self, payment_id):
        return self.fetch_one(
            """
            SELECT id, user_id, stripe_payment_intent_id, amount, currency, status,
                   provider, created_at, updated_at
            FROM payment_transactions
            WHERE id = %s
            """,
            (payment_id,),
        )

    def find_by_payment_intent(self, payment_intent_id):
        return self.fetch_one(
            """
            SELECT id, user_id, stripe_payment_intent_id, amount, currency, status,
                   provider, created_at, updated_at
            FROM payment_transactions
            WHERE stripe_payment_intent_id = %s
            """,
            (payment_intent_id,),
        )

    def list_for_user(self, user_id):
        return self.fetch_all(
            """
            SELECT id, user_id, stripe_payment_intent_id, amount, currency, status,
                   provider, created_at, updated_at
            FROM payment_transactions
            WHERE user_id = %s
            ORDER BY created_at DESC
            """,
            (user_id,),
        )

    def update_status(self, payment_id, status):
        self.execute(
            """
            UPDATE payment_transactions
            SET status = %s
            WHERE id = %s
            """,
            (status, payment_id),
        )
        return self.find_by_id(payment_id)
    
    def update_payment_intent_id(self, payment_id, payment_intent_id):
        self.execute(
            """
            UPDATE payment_transactions
            SET stripe_payment_intent_id = %s
            WHERE id = %s
            """,
            (payment_intent_id, payment_id),
        )
        return self.find_by_id(payment_id)

    def find_by_checkout_session(self, checkout_session_id):
        return self.find_by_payment_intent(checkout_session_id)
