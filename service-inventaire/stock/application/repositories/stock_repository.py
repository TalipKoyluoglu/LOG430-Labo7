"""
Interface du repository Stock pour la couche Application
Définit le contrat d'accès aux données pour les entités Stock.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from ...domain.entities import StockCentral, StockLocal
from ...domain.value_objects import ProduitId, MagasinId, StockId


class StockRepository(ABC):
    """Interface abstraite pour l'accès aux données de stock"""

    @abstractmethod
    def get_stock_central_by_produit(
        self, produit_id: ProduitId
    ) -> Optional[StockCentral]:
        """
        Récupère le stock central d'un produit spécifique
        """
        pass

    @abstractmethod
    def get_stock_local_by_produit_magasin(
        self, produit_id: ProduitId, magasin_id: MagasinId
    ) -> Optional[StockLocal]:
        """
        Récupère le stock local d'un produit dans un magasin spécifique
        """
        pass

    @abstractmethod
    def get_all_stocks_centraux(self) -> List[StockCentral]:
        """
        Récupère tous les stocks centraux
        """
        pass

    @abstractmethod
    def get_all_stocks_locaux_by_magasin(
        self, magasin_id: MagasinId
    ) -> List[StockLocal]:
        """
        Récupère tous les stocks locaux d'un magasin
        """
        pass

    @abstractmethod
    def get_all_stocks_locaux(self) -> List[StockLocal]:
        """
        Récupère tous les stocks locaux de tous les magasins
        """
        pass

    @abstractmethod
    def get_stocks_centraux_faibles(self, seuil: int = 10) -> List[StockCentral]:
        """
        Récupère les stocks centraux sous le seuil spécifié
        """
        pass

    @abstractmethod
    def get_stocks_locaux_faibles(
        self, magasin_id: MagasinId, seuil: int = 5
    ) -> List[StockLocal]:
        """
        Récupère les stocks locaux d'un magasin sous le seuil spécifié
        """
        pass

    @abstractmethod
    def save_stock_central(self, stock: StockCentral) -> StockCentral:
        """
        Sauvegarde un stock central (création ou mise à jour)
        """
        pass

    @abstractmethod
    def save_stock_local(self, stock: StockLocal) -> StockLocal:
        """
        Sauvegarde un stock local (création ou mise à jour)
        """
        pass

    @abstractmethod
    def delete_stock_central(self, stock_id: StockId) -> bool:
        """
        Supprime un stock central
        """
        pass

    @abstractmethod
    def delete_stock_local(self, stock_id: StockId) -> bool:
        """
        Supprime un stock local
        """
        pass
