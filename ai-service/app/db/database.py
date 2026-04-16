"""
Veritabanı Bağlantı Yönetimi
==============================
SQLAlchemy engine ve session factory.
Şu an aktif değil — ileride PostgreSQL bağlantısı burada kurulacak.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# ---------------------------------------------------------------------------
# Engine — Veritabanı bağlantı motoru
# İleride asyncpg ile async engine'e geçilecek:
#   from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
# ---------------------------------------------------------------------------
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)

# ---------------------------------------------------------------------------
# Session Factory
# ---------------------------------------------------------------------------
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


def get_db():
    """
    FastAPI dependency olarak kullanılacak DB session üreteci.

    Kullanım:
        @router.get("/items")
        def read_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
