"""
Base Repository — Generic CRUD soyut sınıfı.
Tüm repository'ler bu sınıftan türer.

Şu an in-memory dict ile çalışır.
İleride SQLAlchemy session'a geçişte sadece bu katman değişir.
"""

from abc import ABC, abstractmethod
from typing import Dict, Generic, List, Optional, TypeVar

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """
    Generic CRUD operasyonları sağlayan soyut taban sınıf.

    Alt sınıflar:
        - CameraRepository
        - DetectionRepository
        - IoTRepository
        - AlertRepository
    """

    @abstractmethod
    async def get_by_id(self, entity_id: str) -> Optional[T]:
        """ID'ye göre tek kayıt getirir."""
        ...

    @abstractmethod
    async def get_all(self) -> List[T]:
        """Tüm kayıtları listeler."""
        ...

    @abstractmethod
    async def create(self, entity: T) -> T:
        """Yeni kayıt oluşturur."""
        ...

    @abstractmethod
    async def update(self, entity_id: str, entity: T) -> Optional[T]:
        """Var olan kaydı günceller."""
        ...

    @abstractmethod
    async def delete(self, entity_id: str) -> bool:
        """Kaydı siler. Başarılıysa True döner."""
        ...


class InMemoryRepository(BaseRepository[T]):
    """
    In-memory implementasyon.
    Geliştirme aşamasında DB olmadan çalışmayı sağlar.
    Veriler uygulama kapandığında kaybolur.
    """

    def __init__(self) -> None:
        self._store: Dict[str, T] = {}

    async def get_by_id(self, entity_id: str) -> Optional[T]:
        return self._store.get(entity_id)

    async def get_all(self) -> List[T]:
        return list(self._store.values())

    async def create(self, entity: T) -> T:
        # Alt sınıf entity'den ID'yi çıkarmalı
        raise NotImplementedError("Alt sınıfta implement edilmeli.")

    async def update(self, entity_id: str, entity: T) -> Optional[T]:
        if entity_id not in self._store:
            return None
        self._store[entity_id] = entity
        return entity

    async def delete(self, entity_id: str) -> bool:
        if entity_id in self._store:
            del self._store[entity_id]
            return True
        return False
