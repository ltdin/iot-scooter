from master.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository):
    def find_by_username(self, username):
        return self.fetch_one(
            """
            SELECT id, username, password_hash, role, first_name, last_name, phone,
                   email, balance, created_at
            FROM users
            WHERE username = %s
            """,
            (username,),
        )
    def find_by_email(self, email):
        return self.fetch_one(
            """
            SELECT id, username, password_hash, role, first_name, last_name, phone,
                   email, balance, created_at
            FROM users
            WHERE email = %s
            """,
            (email,),
        )
    def find_by_id(self, user_id):
        return self.fetch_one(
            """
            SELECT id, username, password_hash, role, first_name, last_name, phone,
                   email, balance, created_at
            FROM users
            WHERE id = %s
            """,
            (user_id,),
        )
    def create_customer(self, customer_data):
        user_id = self.execute(
            """
            INSERT INTO users
                (username, password_hash, role, first_name, last_name, phone, email, balance)
            VALUES
                (%s, %s, 'customer', %s, %s, %s, %s, %s)
            """,
            (
                customer_data["username"],
                customer_data["password_hash"],
                customer_data["first_name"],
                customer_data["last_name"],
                customer_data["phone"],
                customer_data["email"],
                customer_data.get("balance", 0),
            ),
        )
        return self.find_by_id(user_id)

    def list_customers(self):
        return self.fetch_all(
            """
            SELECT id, username, first_name, last_name, phone, email, balance, created_at
            FROM users
            WHERE role = 'customer'
            ORDER BY id
            """
        )

    def list_engineers(self):
        return self.fetch_all(
            """
            SELECT id, username, first_name, last_name, phone, email, created_at
            FROM users
            WHERE role = 'engineer'
            ORDER BY id
            """
        )

    def add_balance(self, user_id, amount):
        self.execute(
            """
            UPDATE users
            SET balance = balance + %s
            WHERE id = %s
            """,
            (amount, user_id),
        )
        return self.find_by_id(user_id)
