"""
Repository Pattern pour Magasin
Interface d'accès aux données selon DDD
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ...domain.entities import Magasin


class MagasinRepository(ABC):
    """
    Interface Repository pour l'entité Magasin
    Définit les contrats d'accès aux données sans dépendance à l'infrastructure
    """

    @abstractmethod
    def get_by_id(self, magasin_id: UUID) -> Optional[Magasin]:
        """Récupère un magasin par son ID"""
        pass

    @abstractmethod
    def get_all(self) -> List[Magasin]:
        """Récupère tous les magasins"""
        pass

    @abstractmethod
    def save(self, magasin: Magasin) -> None:
        """Persiste un magasin"""
        pass
