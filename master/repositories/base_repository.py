"""Base repository helpers used by concrete database repositories."""

from master.db.connection import get_connection


class BaseRepository:
    def __init__(self, connection_factory=None):
        self.connection_factory = connection_factory or get_connection

    def fetch_all(self, query, params=None):
        connection = self.connection_factory()
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            return cursor.fetchall()
        finally:
            cursor.close()
            connection.close()

    def fetch_one(self, query, params=None):
        connection = self.connection_factory()
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            return cursor.fetchone()
        finally:
            cursor.close()
            connection.close()

    def execute(self, query, params=None):
        connection = self.connection_factory()
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            connection.commit()
            return cursor.lastrowid
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()
