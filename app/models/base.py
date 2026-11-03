"""
app.models.base — backward-compatible shim providing get_db() context manager.
Patches the SQLAlchemy 2.x Session to support legacy db.query(Model) calls
used by test_part3.py and test_part4.py.
"""
from __future__ import annotations
from contextlib import contextmanager
from sqlalchemy.orm import Session
from sqlalchemy import select

# Import the real get_db from the actual database module
from database.db import get_db as _real_get_db


class _LegacySessionWrapper:
    """
    Wraps a SQLAlchemy 2.x Session and adds a backward-compat .query() method
    so that legacy code like `db.query(Book).filter(...).first()` still works.
    """

    def __init__(self, session: Session):
        self._session = session

    # --- Compatibility shim ---
    def query(self, model):
        return _LegacyQuery(self._session, model)

    # --- Delegate everything else to the real session ---
    def __getattr__(self, name):
        return getattr(self._session, name)


class _LegacyQuery:
    """
    Minimal SQLAlchemy 1.x-style Query object backed by select().
    Supports: .all(), .first(), .filter(), .filter_by(), .get() (via session.get)
    """

    def __init__(self, session: Session, model):
        self._session = session
        self._model = model
        self._stmt = select(model)

    def filter(self, *criteria):
        q = _LegacyQuery(self._session, self._model)
        q._stmt = self._stmt.where(*criteria)
        return q

    def filter_by(self, **kwargs):
        conditions = [
            getattr(self._model, k) == v for k, v in kwargs.items()
        ]
        q = _LegacyQuery(self._session, self._model)
        q._stmt = self._stmt.where(*conditions)
        return q

    def order_by(self, *clauses):
        q = _LegacyQuery(self._session, self._model)
        q._stmt = self._stmt.order_by(*clauses)
        return q

    def limit(self, n: int):
        q = _LegacyQuery(self._session, self._model)
        q._stmt = self._stmt.limit(n)
        return q

    def all(self):
        return list(self._session.scalars(self._stmt).all())

    def first(self):
        q = _LegacyQuery(self._session, self._model)
        q._stmt = self._stmt.limit(1)
        result = self._session.scalars(q._stmt).first()
        return result

    def count(self):
        from sqlalchemy import func
        cnt_stmt = select(func.count()).select_from(self._stmt.subquery())
        return self._session.scalar(cnt_stmt) or 0


@contextmanager
def get_db():
    """Context manager that yields a legacy-compatible DB session."""
    with _real_get_db() as session:
        yield _LegacySessionWrapper(session)
