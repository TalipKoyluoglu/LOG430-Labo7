"""
Service abstrait pour la communication avec le service Stock
Interface pour les opérations sur les stocks.
"""

from abc import ABC, abstractmethod
from ...domain.value_objects import ProduitId, MagasinId, Quantite


class StockService(ABC):
    """Interface abstraite pour les opérations de stock"""

    @abstractmethod
    def diminuer_stock_central(self, produit_id: ProduitId, quantite: Quantite) -> bool:
        """Diminue le stock central d'un produit"""
        pass

    @abstractmethod
    def augmenter_stock_central(
        self, produit_id: ProduitId, quantite: Quantite
    ) -> bool:
        """Augmente le stock central d'un produit (pour rollback)"""
        pass

    @abstractmethod
    def augmenter_stock_local(
        self, produit_id: ProduitId, magasin_id: MagasinId, quantite: Quantite
    ) -> bool:
        """Augmente le stock local d'un magasin"""
        pass

    @abstractmethod
    def diminuer_stock_local(
        self, produit_id: ProduitId, magasin_id: MagasinId, quantite: Quantite
    ) -> bool:
        """Diminue le stock local d'un magasin (pour rollback)"""
        pass
