"""
Service d'Infrastructure pour Stock
Interface de communication avec le service externe stock
"""

from abc import ABC, abstractmethod
from typing import List
from uuid import UUID

from ...domain.value_objects import StockInfo


class StockService(ABC):
    """
    Service d'infrastructure pour communiquer avec le service stock
    Encapsule la communication réseau et les détails d'implémentation
    """

    @abstractmethod
    def get_stock_local(self, magasin_id: UUID, produit_id: UUID) -> StockInfo:
        """
        Récupère les informations de stock local pour un produit dans un magasin

        Args:
            magasin_id: ID du magasin
            produit_id: ID du produit

        Returns:
            StockInfo avec la quantité disponible
        """
        pass

    @abstractmethod
    def get_all_stock_local(self, magasin_id: UUID) -> List[StockInfo]:
        """
        Récupère tous les stocks locaux d'un magasin

        Args:
            magasin_id: ID du magasin

        Returns:
            Liste des StockInfo du magasin
        """
        pass

    @abstractmethod
    def decrease_stock(self, magasin_id: UUID, produit_id: UUID, quantite: int) -> None:
        """
        Diminue le stock d'un produit dans un magasin

        Args:
            magasin_id: ID du magasin
            produit_id: ID du produit
            quantite: Quantité à décrémenter
        """
        pass

    @abstractmethod
    def increase_stock(self, magasin_id: UUID, produit_id: UUID, quantite: int) -> None:
        """
        Augmente le stock d'un produit dans un magasin

        Args:
            magasin_id: ID du magasin
            produit_id: ID du produit
            quantite: Quantité à incrémenter
        """
        pass
