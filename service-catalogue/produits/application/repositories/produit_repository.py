"""
Repository interface pour les Produits
Définit le contrat d'accès aux données pour les produits (abstraction DDD)
"""

from abc import ABC, abstractmethod
from typing import List, Optional
import uuid

from ...domain.entities import Produit
from ...domain.value_objects import ProduitId, CategorieId


class ProduitRepository(ABC):
    """
    Interface Repository pour les Produits
    Suit le pattern Repository du DDD pour abstraire la persistance
    """

    @abstractmethod
    def save(self, produit: Produit) -> Produit:
        """
        Sauvegarde un produit (création ou mise à jour)

        Args:
            produit: Entité Produit à sauvegarder

        Returns:
            Produit sauvegardé avec les données persistées
        """
        pass

    @abstractmethod
    def get_by_id(self, produit_id: ProduitId) -> Optional[Produit]:
        """
        Récupère un produit par son ID

        Args:
            produit_id: UUID du produit

        Returns:
            Produit trouvé ou None
        """
        pass

    @abstractmethod
    def get_by_nom(self, nom: str) -> Optional[Produit]:
        """
        Récupère un produit par son nom (pour vérifier unicité)

        Args:
            nom: Nom du produit

        Returns:
            Produit trouvé ou None
        """
        pass

    @abstractmethod
    def get_by_sku(self, sku: str) -> Optional[Produit]:
        """
        Récupère un produit par son SKU (pour vérifier unicité)

        Args:
            sku: SKU du produit

        Returns:
            Produit trouvé ou None
        """
        pass

    @abstractmethod
    def get_all(self) -> List[Produit]:
        """
        Récupère tous les produits

        Returns:
            Liste de tous les produits
        """
        pass

    @abstractmethod
    def get_produits_actifs(self) -> List[Produit]:
        """
        Récupère tous les produits actifs

        Returns:
            Liste des produits actifs
        """
        pass

    @abstractmethod
    def get_by_categorie(self, categorie_id: CategorieId) -> List[Produit]:
        """
        Récupère tous les produits d'une catégorie

        Args:
            categorie_id: ID de la catégorie

        Returns:
            Liste des produits de la catégorie
        """
        pass

    @abstractmethod
    def get_produits_premium(self) -> List[Produit]:
        """
        Récupère tous les produits premium (prix > 100€)
        Peut être optimisé au niveau base de données

        Returns:
            Liste des produits premium
        """
        pass

    @abstractmethod
    def search_by_nom(self, terme: str) -> List[Produit]:
        """
        Recherche de produits par nom (recherche textuelle)

        Args:
            terme: Terme de recherche

        Returns:
            Liste des produits correspondants
        """
        pass

    @abstractmethod
    def delete(self, produit_id: ProduitId) -> bool:
        """
        Supprime un produit

        Args:
            produit_id: ID du produit à supprimer

        Returns:
            True si suppression réussie, False sinon
        """
        pass

    @abstractmethod
    def exists_by_nom(self, nom: str) -> bool:
        """
        Vérifie si un produit avec ce nom existe

        Args:
            nom: Nom à vérifier

        Returns:
            True si existe, False sinon
        """
        pass

    @abstractmethod
    def exists_by_sku(self, sku: str) -> bool:
        """
        Vérifie si un produit avec ce SKU existe

        Args:
            sku: SKU à vérifier

        Returns:
            True si existe, False sinon
        """
        pass
