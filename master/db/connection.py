"""Database connection factory for Cloud SQL MySQL."""

import mysql.connector
from mysql.connector import Error

from master.config import Config


def get_connection():
    try:
        return mysql.connector.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            database=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            autocommit=False,
            connection_timeout=10,
            use_pure=True,
        )
    except Error as error:
        raise RuntimeError(f"Could not connect to cloud MySQL: {error}") from error
