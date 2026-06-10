"""Repositories de active-trace.

Todos los repositories de dominio heredan de BaseRepository[T]
que garantiza scope de tenant en todos los queries.
"""

from app.repositories.base import BaseRepository

__all__ = ["BaseRepository"]
