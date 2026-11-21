"""Apply database migration files to the configured Cloud SQL database."""

from pathlib import Path

from mysql.connector import Error

from master.db.init_db import _split_statements
from master.db.connection import get_connection

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def apply_migrations():
    connection = get_connection()
    try:
        cursor = connection.cursor()
        for migration_path in sorted(MIGRATIONS_DIR.glob("*.sql")):
            sql_text = migration_path.read_text(encoding="utf-8")
            for statement in _split_statements(sql_text):
                try:
                    cursor.execute(statement)
                except Error as error:
                    if error.errno == 1060:
                        continue
                    raise
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    apply_migrations()
    print("Database migrations applied successfully.")
