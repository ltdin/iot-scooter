"""Initialize the configured Cloud SQL database with schema and seed data."""

from pathlib import Path

from master.db.connection import get_connection

DB_DIR = Path(__file__).resolve().parent


def _read_sql_file(filename):
    return (DB_DIR / filename).read_text(encoding="utf-8")


def _split_statements(sql_text):
    return [statement.strip() for statement in sql_text.split(";") if statement.strip()]


def execute_sql_file(filename):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        for statement in _split_statements(_read_sql_file(filename)):
            cursor.execute(statement)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def initialize_database():
    execute_sql_file("schema.sql")
    execute_sql_file("seed_data.sql")


if __name__ == "__main__":
    initialize_database()
    print("Database schema and seed data applied successfully.")
