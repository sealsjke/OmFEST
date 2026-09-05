import os
import psycopg2


def get_db():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "db"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        database=os.getenv("POSTGRES_DB", "coinrace"),
        user=os.getenv("POSTGRES_USER", "coinrace"),
        password=os.getenv("POSTGRES_PASSWORD", "coinrace"),
    )