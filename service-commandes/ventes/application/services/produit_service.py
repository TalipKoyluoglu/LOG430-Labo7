"""
Service d'Infrastructure pour Produits
Interface de communication avec le service externe produits
"""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from ...domain.value_objects import ProduitInfo


class ProduitService(ABC):
    """
    Service d'infrastructure pour communiquer avec le service produits
    Encapsule la communication réseau et les détails d'implémentation
    """

    @abstractmethod
    def get_produit_details(self, produit_id: UUID) -> Optional[ProduitInfo]:
        """
        Récupère les détails d'un produit depuis le service externe

        Args:
            produit_id: ID du produit à récupérer

        Returns:
            ProduitInfo si trouvé, None sinon
        """
        pass
