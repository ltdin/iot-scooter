from master.repositories.base_repository import BaseRepository


class ScooterRepository(BaseRepository):
    def list_all(self):
        return self.fetch_all(
            """
            SELECT id, make, colour, location, latitude, longitude, cost_per_minute,
                   status, created_at, updated_at
            FROM scooters
            ORDER BY id
            """
        )

    def list_available(self):
        return self.fetch_all(
            """
            SELECT id, make, colour, location, latitude, longitude, cost_per_minute,
                   status, created_at, updated_at
            FROM scooters
            WHERE status = 'Available'
            ORDER BY id
            """
        )

    def find_by_id(self, scooter_id):
        return self.fetch_one(
            """
            SELECT id, make, colour, location, latitude, longitude, cost_per_minute,
                   status, created_at, updated_at
            FROM scooters
            WHERE id = %s
            """,
            (scooter_id,),
        )

    def create(self, scooter_data):
        self.execute(
            """
            INSERT INTO scooters
                (id, make, colour, location, latitude, longitude, cost_per_minute, status)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                scooter_data["id"],
                scooter_data["make"],
                scooter_data["colour"],
                scooter_data["location"],
                scooter_data.get("latitude"),
                scooter_data.get("longitude"),
                scooter_data["cost_per_minute"],
                scooter_data.get("status", "Available"),
            ),
        )
        return self.find_by_id(scooter_data["id"])

    def update(self, scooter_id, scooter_data):
        existing = self.find_by_id(scooter_id)
        if not existing:
            return None

        updated = {**existing, **scooter_data}
        self.execute(
            """
            UPDATE scooters
            SET make = %s, colour = %s, location = %s, latitude = %s, longitude = %s,
                cost_per_minute = %s, status = %s
            WHERE id = %s
            """,
            (
                updated["make"],
                updated["colour"],
                updated["location"],
                updated.get("latitude"),
                updated.get("longitude"),
                updated["cost_per_minute"],
                updated["status"],
                scooter_id,
            ),
        )
        return self.find_by_id(scooter_id)

    def delete(self, scooter_id):
        return self.execute("DELETE FROM scooters WHERE id = %s", (scooter_id,))

    def update_status(self, scooter_id, status):
        self.execute(
            "UPDATE scooters SET status = %s WHERE id = %s",
            (status, scooter_id),
        )
        return self.find_by_id(scooter_id)
