from master.repositories.base_repository import BaseRepository


class ReportRepository(BaseRepository):
    def create(self, report_data):
        return self.execute(
            """
            INSERT INTO reports
                (scooter_id, reported_by, issue_description, status)
            VALUES
                (%s, %s, %s, %s)
            """,
            (
                report_data["scooter_id"],
                report_data["reported_by"],
                report_data["issue_description"],
                report_data.get("status", "Open"),
            ),
        )

    def list_open(self):
        return self.fetch_all(
            """
            SELECT r.id, r.scooter_id, s.make, s.colour, s.location, s.latitude,
                   s.longitude, s.status AS scooter_status, r.reported_by,
                   u.username AS reported_by_username,
                   CONCAT_WS(' ', u.first_name, u.last_name) AS reported_by_full_name,
                   r.issue_description, r.status, r.created_at
            FROM reports r
            JOIN scooters s ON s.id = r.scooter_id
            JOIN users u ON u.id = r.reported_by
            WHERE r.status IN ('Open', 'Under Repair')
            ORDER BY r.created_at DESC
            """
        )

    def find_by_id(self, report_id):
        return self.fetch_one(
            """
            SELECT r.id, r.scooter_id, s.make, s.colour, s.location, s.latitude,
                   s.longitude, s.status AS scooter_status, r.reported_by,
                   u.username AS reported_by_username,
                   CONCAT_WS(' ', u.first_name, u.last_name) AS reported_by_full_name,
                   r.issue_description, r.status, r.created_at, r.resolved_at
            FROM reports r
            JOIN scooters s ON s.id = r.scooter_id
            JOIN users u ON u.id = r.reported_by
            WHERE r.id = %s
            """,
            (report_id,),
        )

    def update_status(self, report_id, status):
        resolved_expression = "CURRENT_TIMESTAMP" if status == "Resolved" else "NULL"
        self.execute(
            f"""
            UPDATE reports
            SET status = %s, resolved_at = {resolved_expression}
            WHERE id = %s
            """,
            (status, report_id),
        )
        return self.find_by_id(report_id)

    def create_repair_log(self, repair_data):
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

    def complete_repair(self, repair_data):
        connection = self.connection_factory()
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
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
            repair_id = cursor.lastrowid

            if repair_data.get("report_id"):
                cursor.execute(
                    """
                    UPDATE reports
                    SET status = 'Resolved', resolved_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (repair_data["report_id"],),
                )

            cursor.execute(
                "UPDATE scooters SET status = 'Available' WHERE id = %s",
                (repair_data["scooter_id"],),
            )
            connection.commit()
            return repair_id
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

    def find_repair_log_by_id(self, repair_id):
        return self.fetch_one(
            """
            SELECT id, engineer_id, scooter_id, report_id, result, repaired_at
            FROM repair_logs
            WHERE id = %s
            """,
            (repair_id,),
        )