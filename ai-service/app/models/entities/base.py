"""
ORM Taban Sınıfı — SQLAlchemy DeclarativeBase.
Tüm entity'ler bu sınıftan türer.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Tüm ORM entity'lerinin taban sınıfı."""

    pass
