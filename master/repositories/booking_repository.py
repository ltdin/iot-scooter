from master.repositories.base_repository import BaseRepository


class BookingRepository(BaseRepository):
    def create_booking_and_mark_scooter_booked(self, booking_data):
        connection = self.connection_factory()
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                INSERT INTO bookings
                    (user_id, scooter_id, status, calendar_event_id, unlock_code)
                VALUES
                    (%s, %s, %s, %s, %s)
                """,
                (
                    booking_data["user_id"],
                    booking_data["scooter_id"],
                    booking_data.get("status", "Active"),
                    booking_data.get("calendar_event_id"),
                    booking_data.get("unlock_code"),
                ),
            )
            booking_id = cursor.lastrowid
            cursor.execute(
                "UPDATE scooters SET status = 'Booked' WHERE id = %s",
                (booking_data["scooter_id"],),
            )
            connection.commit()
            return self.find_by_id(booking_id)
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

    def create(self, booking_data):
        return self.execute(
            """
            INSERT INTO bookings
                (user_id, scooter_id, status, calendar_event_id, unlock_code)
            VALUES
                (%s, %s, %s, %s, %s)
            """,
            (
                booking_data["user_id"],
                booking_data["scooter_id"],
                booking_data.get("status", "Active"),
                booking_data.get("calendar_event_id"),
                booking_data.get("unlock_code"),
            ),
        )

    def find_by_id(self, booking_id):
        return self.fetch_one(
            """
            SELECT id, user_id, scooter_id, status, booked_at, unlock_time, lock_time,
                   calendar_event_id, unlock_code, max_usage_minutes, auto_lock_at
            FROM bookings
            WHERE id = %s
            """,
            (booking_id,),
        )

    def find_active_for_user(self, user_id):
        return self.fetch_all(
            """
            SELECT id, user_id, scooter_id, status, booked_at, unlock_time, lock_time,
                   calendar_event_id, unlock_code, max_usage_minutes, auto_lock_at
            FROM bookings
            WHERE user_id = %s AND status = 'Active'
            ORDER BY booked_at DESC
            """,
            (user_id,),
        )

    def find_active_for_scooter(self, scooter_id):
        return self.fetch_one(
            """
            SELECT id, user_id, scooter_id, status, booked_at, unlock_time, lock_time,
                   calendar_event_id, unlock_code, max_usage_minutes, auto_lock_at
            FROM bookings
            WHERE scooter_id = %s AND status = 'Active'
            ORDER BY booked_at DESC
            LIMIT 1
            """,
            (scooter_id,),
        )

    def find_active_by_unlock_code(self, unlock_code):
        return self.fetch_one(
            """
            SELECT id, user_id, scooter_id, status, booked_at, unlock_time, lock_time,
                   calendar_event_id, unlock_code, max_usage_minutes, auto_lock_at
            FROM bookings
            WHERE unlock_code = %s AND status = 'Active'
            ORDER BY booked_at DESC
            LIMIT 1
            """,
            (unlock_code,),
        )

    def cancel_booking_and_mark_scooter_available(self, booking_id):
        connection = self.connection_factory()
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT id, user_id, scooter_id, status, booked_at, unlock_time, lock_time,
                       calendar_event_id, unlock_code
                FROM bookings
                WHERE id = %s
                """,
                (booking_id,),
            )
            booking = cursor.fetchone()
            if not booking:
                connection.rollback()
                return None

            cursor.execute(
                "UPDATE bookings SET status = 'Canceled' WHERE id = %s",
                (booking_id,),
            )
            cursor.execute(
                "UPDATE scooters SET status = 'Available' WHERE id = %s",
                (booking["scooter_id"],),
            )
            connection.commit()
            return self.find_by_id(booking_id)
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

    def unlock_booking_and_mark_scooter_occupying(self, booking_id, usage_limit):
        connection = self.connection_factory()
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT id, user_id, scooter_id, status, booked_at, unlock_time, lock_time,
                       calendar_event_id, unlock_code, max_usage_minutes, auto_lock_at
                FROM bookings
                WHERE id = %s
                """,
                (booking_id,),
            )
            booking = cursor.fetchone()
            if not booking:
                connection.rollback()
                return None

            cursor.execute(
                """
                UPDATE bookings
                SET unlock_time = %s, max_usage_minutes = %s, auto_lock_at = %s
                WHERE id = %s
                """,
                (
                    usage_limit["unlock_time"],
                    usage_limit["max_usage_minutes"],
                    usage_limit["auto_lock_at"],
                    booking_id,
                ),
            )
            cursor.execute(
                "UPDATE scooters SET status = 'Occupying' WHERE id = %s",
                (booking["scooter_id"],),
            )
            connection.commit()
            return self.find_by_id(booking_id)
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

    def complete_booking_and_mark_scooter_available(self, booking_id):
        connection = self.connection_factory()
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT id, user_id, scooter_id, status, booked_at, unlock_time, lock_time,
                       calendar_event_id, unlock_code, max_usage_minutes, auto_lock_at
                FROM bookings
                WHERE id = %s
                """,
                (booking_id,),
            )
            booking = cursor.fetchone()
            if not booking:
                connection.rollback()
                return None

            cursor.execute(
                """
                UPDATE bookings
                SET lock_time = CURRENT_TIMESTAMP, status = 'Completed'
                WHERE id = %s
                """,
                (booking_id,),
            )
            cursor.execute(
                "UPDATE scooters SET status = 'Available' WHERE id = %s",
                (booking["scooter_id"],),
            )
            connection.commit()
            return self.find_by_id(booking_id)
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

    def complete_booking_with_billing(self, booking_id, billing_data):
        connection = self.connection_factory()
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT id, user_id, scooter_id, status, booked_at, unlock_time, lock_time,
                       calendar_event_id, unlock_code, max_usage_minutes, auto_lock_at
                FROM bookings
                WHERE id = %s
                """,
                (booking_id,),
            )
            booking = cursor.fetchone()
            if not booking:
                connection.rollback()
                return None

            cursor.execute(
                """
                UPDATE bookings
                SET lock_time = %s, status = 'Completed'
                WHERE id = %s
                """,
                (billing_data["end_time"], booking_id),
            )
            cursor.execute(
                "UPDATE scooters SET status = 'Available' WHERE id = %s",
                (booking["scooter_id"],),
            )
            cursor.execute(
                "UPDATE users SET balance = balance - %s WHERE id = %s",
                (billing_data["charged_amount"], booking["user_id"]),
            )
            cursor.execute(
                """
                INSERT INTO usage_history
                    (user_id, scooter_id, booking_id, start_time, end_time,
                     duration_minutes, total_cost, charged_amount, unpaid_amount,
                     payment_status)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    booking["user_id"],
                    booking["scooter_id"],
                    booking_id,
                    billing_data["start_time"],
                    billing_data["end_time"],
                    billing_data["duration_minutes"],
                    billing_data["total_cost"],
                    billing_data["charged_amount"],
                    billing_data["unpaid_amount"],
                    billing_data["payment_status"],
                ),
            )
            usage_id = cursor.lastrowid
            connection.commit()
            completed_booking = self.find_by_id(booking_id)
            usage = self.fetch_one(
                """
                SELECT id, user_id, scooter_id, booking_id, start_time, end_time,
                       duration_minutes, total_cost, charged_amount, unpaid_amount,
                       payment_status
                FROM usage_history
                WHERE id = %s
                """,
                (usage_id,),
            )
            return {
                "booking": completed_booking,
                "usage": usage,
            }
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

    def update_status(self, booking_id, status):
        self.execute(
            "UPDATE bookings SET status = %s WHERE id = %s",
            (status, booking_id),
        )
        return self.fetch_one("SELECT * FROM bookings WHERE id = %s", (booking_id,))

    def list_usage_history(self):
        return self.fetch_all(
            """
            SELECT uh.id, uh.user_id, u.username, uh.scooter_id, uh.booking_id,
                   uh.start_time, uh.end_time, uh.duration_minutes, uh.total_cost,
                   uh.charged_amount, uh.unpaid_amount, uh.payment_status
            FROM usage_history uh
            JOIN users u ON u.id = uh.user_id
            ORDER BY uh.start_time DESC
            """
        )

    def usage_report_by_day(self):
        return self.fetch_all(
            """
            SELECT
                DATE(uh.start_time) AS period,
                COUNT(*) AS trip_count,
                COUNT(DISTINCT uh.user_id) AS customer_count,
                COUNT(DISTINCT uh.scooter_id) AS scooter_count,
                COALESCE(SUM(uh.duration_minutes), 0) AS total_duration_minutes,
                COALESCE(SUM(uh.total_cost), 0) AS total_cost,
                COALESCE(SUM(uh.charged_amount), 0) AS charged_amount,
                COALESCE(SUM(uh.unpaid_amount), 0) AS unpaid_amount
            FROM usage_history uh
            GROUP BY DATE(uh.start_time)
            ORDER BY period
            """
        )

    def usage_report_by_week(self):
        return self.fetch_all(
            """
            SELECT
                YEARWEEK(uh.start_time, 3) AS period,
                MIN(DATE(uh.start_time)) AS start_date,
                MAX(DATE(uh.start_time)) AS end_date,
                COUNT(*) AS trip_count,
                COUNT(DISTINCT uh.user_id) AS customer_count,
                COUNT(DISTINCT uh.scooter_id) AS scooter_count,
                COALESCE(SUM(uh.duration_minutes), 0) AS total_duration_minutes,
                COALESCE(SUM(uh.total_cost), 0) AS total_cost,
                COALESCE(SUM(uh.charged_amount), 0) AS charged_amount,
                COALESCE(SUM(uh.unpaid_amount), 0) AS unpaid_amount
            FROM usage_history uh
            GROUP BY YEARWEEK(uh.start_time, 3)
            ORDER BY period
            """
        )
