"""
Interface du service Produit pour la validation des entités externes
Définit le contrat de validation des produits via API externe.
"""

from abc import ABC, abstractmethod
from ...domain.value_objects import ProduitId
from ...domain.exceptions import ProduitInexistantError


class ProduitService(ABC):
    """Interface abstraite pour la validation des produits"""

    @abstractmethod
    def produit_existe(self, produit_id: ProduitId) -> bool:
        """
        Vérifie si un produit existe dans le service catalogue
        """
        pass

    @abstractmethod
    def valider_produit_existe(self, produit_id: ProduitId) -> None:
        """
        Valide qu'un produit existe, lève une exception sinon
        """
        if not self.produit_existe(produit_id):
            raise ProduitInexistantError(f"Le produit {produit_id} n'existe pas")

    @abstractmethod
    def get_nom_produit(self, produit_id: ProduitId) -> str:
        """
        Récupère le nom d'un produit pour l'affichage
        """
        pass
