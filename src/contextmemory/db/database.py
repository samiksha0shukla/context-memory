"""
Database connection and session management.

Uses lazy initialization - engine is created only when first accessed.
Supports both PostgreSQL and SQLite (default fallback).
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from contextmemory.core.settings import get_settings

# Global instances (lazy initialized)
_engine = None
_SessionLocal = None

Base = declarative_base()


def get_engine():
    """
    Get or create the database engine.
    
    Uses lazy initialization - engine is created on first call.
    """
    global _engine
    if _engine is None:
        settings = get_settings()
        database_url = settings.get_database_url()
        
        # SQLite requires special connect_args for multi-threading
        connect_args = {}
        if database_url.startswith("sqlite"):
            connect_args["check_same_thread"] = False
        
        _engine = create_engine(database_url, connect_args=connect_args)
        
        if settings.debug:
            print(f"Database connected: {database_url}")
    
    return _engine


def get_session_local():
    """
    Get or create the SessionLocal factory.
    """
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            autoflush=False, 
            autocommit=False, 
            bind=get_engine()
        )
    return _SessionLocal


def SessionLocal():
    """
    Create a new database session.
    
    Convenience wrapper around get_session_local()().
    """
    return get_session_local()()


def get_db():
    """
    Database session generator for dependency injection.
    
    Yields a session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_table():
    """
    Create all database tables.
    
    Safe to call multiple times (idempotent).
    """
    try:
        import contextmemory.db.models
        
        Base.metadata.create_all(bind=get_engine())
        print("Tables created successfully")
    except Exception as e:
        print("Error while creating tables")
        raise e


def reset_engine():
    """
    Reset engine and session factory. Useful for testing.
    """
    global _engine, _SessionLocal
    if _engine:
        _engine.dispose()
    _engine = None
    _SessionLocal = None
