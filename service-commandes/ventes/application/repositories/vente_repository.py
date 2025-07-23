"""
Repository Pattern pour Vente
Interface d'accès aux données selon DDD
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from uuid import UUID

from ...domain.entities import Vente


class VenteRepository(ABC):
    """
    Interface Repository pour l'entité Vente
    Définit les contrats d'accès aux données sans dépendance à l'infrastructure
    """

    @abstractmethod
    def save(self, vente: Vente) -> None:
        """Persiste une vente (création ou mise à jour)"""
        pass

    @abstractmethod
    def get_by_id(self, vente_id: str) -> Optional[Vente]:
        """Récupère une vente par son ID"""
        pass

    @abstractmethod
    def get_all(self) -> List[Vente]:
        """Récupère toutes les ventes"""
        pass

    @abstractmethod
    def get_ventes_actives_by_magasin(self, magasin_id: UUID) -> List[Vente]:
        """Récupère les ventes actives d'un magasin"""
        pass

    @abstractmethod
    def get_ventes_actives_by_magasin_and_period(
        self, magasin_id: UUID, debut: datetime, fin: datetime
    ) -> List[Vente]:
        """Récupère les ventes actives d'un magasin sur une période"""
        pass

    @abstractmethod
    def delete(self, vente_id: str) -> None:
        """Supprime une vente"""
        pass
