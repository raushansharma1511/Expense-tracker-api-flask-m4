import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Load environment variables
load_dotenv()


def setup_test_database():
    """Set up or reset a dedicated test database."""
    db_name = os.getenv("TEST_DB_NAME", "expense_tracker_test")
    db_user = os.getenv("DB_USER", "mac")
    db_password = os.getenv("DB_PASSWORD", "1234")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")

    print(f"Setting up test database: {db_name}")

    # Connect to the 'postgres' database (a default system database)
    try:
        conn = psycopg2.connect(
            dbname="postgres",  # Explicitly connect to 'postgres'
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
        )
    except psycopg2.OperationalError as e:
        print(f"Failed to connect to PostgreSQL server: {e}")
        sys.exit(1)

    # Set autocommit mode for database creation/dropping
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    # Check if database exists
    cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
    exists = cursor.fetchone()

    if exists:
        print(f"Database {db_name} already exists, dropping it...")
        # Terminate existing connections
        cursor.execute(
            f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{db_name}'
            AND pid <> pg_backend_pid();
            """
        )
        # Drop the database
        cursor.execute(f"DROP DATABASE {db_name}")

    # Create the database
    print(f"Creating database {db_name}")
    cursor.execute(f"CREATE DATABASE {db_name}")

    # Clean up
    cursor.close()
    conn.close()

    print(f"Test database {db_name} set up successfully")
    return db_name


if __name__ == "__main__":
    setup_test_database()
