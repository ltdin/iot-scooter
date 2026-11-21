from master.repositories.base_repository import BaseRepository


class RepairRepository(BaseRepository):
    def create(self, repair_data):
        return self.execute(
            """
            INSERT INTO repair_logs
                (engineer_id, scooter_id, report_id, result)
            VALUES
                (%s, %s, %s, %s)
            """,
            (
                repair_data["engineer_id"],
                repair_data["scooter_id"],
                repair_data.get("report_id"),
                repair_data["result"],
            ),
        )

    def list_by_engineer(self, engineer_id):
        return self.fetch_all(
            """
            SELECT id, engineer_id, scooter_id, report_id, result, repaired_at
            FROM repair_logs
            WHERE engineer_id = %s
            ORDER BY repaired_at DESC
            """,
            (engineer_id,),
        )
