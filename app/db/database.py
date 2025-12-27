"""
Database module - re-exports from session.py for backward compatibility.

This module maintains backward compatibility with imports that reference
'app.db.database' instead of 'app.db.session'.
"""

from app.db.session import AsyncSessionLocal, engine, get_db, init_db

__all__ = ["AsyncSessionLocal", "engine", "get_db", "init_db"]
