from master.repositories.base_repository import BaseRepository


class UsageRepository(BaseRepository):
    def create(self, usage_data):
        return self.execute(
            """
            INSERT INTO usage_history
                (user_id, scooter_id, booking_id, start_time, end_time,
                 duration_minutes, total_cost)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                usage_data["user_id"],
                usage_data["scooter_id"],
                usage_data.get("booking_id"),
                usage_data["start_time"],
                usage_data["end_time"],
                usage_data["duration_minutes"],
                usage_data["total_cost"],
            ),
        )

    def list_all(self):
        return self.fetch_all("SELECT * FROM usage_history ORDER BY start_time DESC")

    def list_by_user(self, user_id):
        return self.fetch_all(
            "SELECT * FROM usage_history WHERE user_id = %s ORDER BY start_time DESC",
            (user_id,),
        )
