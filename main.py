"""
Application entry point.

Responsibilities:
- Load configuration
- Initialize database
- Verify core services
- Start application runtime

"""

import logging

from sqlalchemy.orm import Session

from src.contextmemory.core.config import settings
from src.contextmemory.core.openai_client import get_openai_client
from src.contextmemory.db.database import create_table, SessionLocal


# Logging

logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# Application bootstrap

def init_database() -> None:
    """
    Initialize database schema.
    Safe to call multiple times (idempotent).
    """
    logger.info("Initializing database...")
    create_table()
    logger.info("Database initialized successfully.")


from sqlalchemy import text
from sqlalchemy.orm import Session


def verify_database_connection() -> None:
    """
    Ensures DB connection is working.
    """
    logger.info("Verifying database connection...")
    db: Session = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        logger.info("Database connection OK.")
    finally:
        db.close()



def verify_openai_client() -> None:
    """
    Ensures OpenAI client can be created.
    """
    logger.info("Initializing OpenAI client...")
    _ = get_openai_client()
    logger.info("OpenAI client initialized successfully.")


def main() -> None:
    """
    Main application entry.
    """

    logger.info("Starting ContextMemory application...")

    # 1️⃣ Load & validate settings
    logger.info("Loaded settings:")
    logger.info(f"DEBUG = {settings.DEBUG}")
    logger.info(f"DATABASE_URL = {settings.DATABASE_URL}")

    # 2️⃣ Init core services
    init_database()
    verify_database_connection()
    verify_openai_client()

    logger.info("Application startup completed successfully.")


# Entry


if __name__ == "__main__":
    main()
