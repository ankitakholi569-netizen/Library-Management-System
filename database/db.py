"""
Database Engine & Session Management for Library Management System.
Implements TQM Data Integrity: SQLite WAL mode, PRAGMA foreign keys, and atomic transactions.
"""

import logging
from contextlib import contextmanager
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker, scoped_session
from config.settings import DATABASE_URL

logger = logging.getLogger("database")

# Initialize SQLite Engine with multi-thread support and foreign key enforcement
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

# SQLite foreign key constraint & high-concurrency WAL mode listener
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging for high concurrency & speed
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()

# Scoped Thread-Safe Session Factory
SessionLocal = scoped_session(
    sessionmaker(
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
        bind=engine
    )
)

class Base(DeclarativeBase):
    """Base declarative class for all TQM ORM models."""
    pass

@contextmanager
def get_db():
    """
    Context manager for database sessions with automatic commit/rollback.
    Demonstrates TQM Principle: Error Prevention & Data Consistency.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as exc:
        session.rollback()
        logger.error(f"Database transaction rollback due to error: {exc}")
        raise
    finally:
        session.close()

def init_db():
    """
    Initializes all database tables declared on Base metadata.
    Includes safe non-destructive column migrations for SQLite.
    """
    logger.info("Initializing database schema with SQLAlchemy...")
    Base.metadata.create_all(bind=engine)

    # Safe column migrations for existing SQLite database
    try:
        with engine.connect() as conn:
            user_cols = [c[1] for c in conn.exec_driver_sql("PRAGMA table_info(users)").fetchall()]
            if user_cols:
                if "department" not in user_cols:
                    conn.exec_driver_sql("ALTER TABLE users ADD COLUMN department VARCHAR(60) DEFAULT 'Library Administration'")
                if "hourly_rate" not in user_cols:
                    conn.exec_driver_sql("ALTER TABLE users ADD COLUMN hourly_rate FLOAT DEFAULT 120.0")
                if "base_salary" not in user_cols:
                    conn.exec_driver_sql("ALTER TABLE users ADD COLUMN base_salary FLOAT DEFAULT 24000.0")
            conn.commit()
    except Exception as exc:
        logger.warning(f"Notice on schema migration check: {exc}")

    logger.info("Database schema initialized and verified.")
