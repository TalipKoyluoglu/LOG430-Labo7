"""
Repository interface pour les Catégories
Définit le contrat d'accès aux données pour les catégories (abstraction DDD)
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from ...domain.entities import Categorie
from ...domain.value_objects import CategorieId


class CategorieRepository(ABC):
    """
    Interface Repository pour les Catégories
    Suit le pattern Repository du DDD pour abstraire la persistance
    """

    @abstractmethod
    def save(self, categorie: Categorie) -> Categorie:
        """
        Sauvegarde une catégorie (création ou mise à jour)

        Args:
            categorie: Entité Catégorie à sauvegarder

        Returns:
            Catégorie sauvegardée
        """
        pass

    @abstractmethod
    def get_by_id(self, categorie_id: CategorieId) -> Optional[Categorie]:
        """
        Récupère une catégorie par son ID

        Args:
            categorie_id: ID de la catégorie

        Returns:
            Catégorie trouvée ou None
        """
        pass

    @abstractmethod
    def get_all(self) -> List[Categorie]:
        """
        Récupère toutes les catégories

        Returns:
            Liste de toutes les catégories
        """
        pass

    @abstractmethod
    def get_categories_actives(self) -> List[Categorie]:
        """
        Récupère toutes les catégories actives

        Returns:
            Liste des catégories actives
        """
        pass

    @abstractmethod
    def get_categories_racines(self) -> List[Categorie]:
        """
        Récupère toutes les catégories racines (sans parent)

        Returns:
            Liste des catégories racines
        """
        pass

    @abstractmethod
    def get_sous_categories(self, parent_id: CategorieId) -> List[Categorie]:
        """
        Récupère toutes les sous-catégories d'une catégorie parent

        Args:
            parent_id: ID de la catégorie parent

        Returns:
            Liste des sous-catégories
        """
        pass

    @abstractmethod
    def delete(self, categorie_id: CategorieId) -> bool:
        """
        Supprime une catégorie

        Args:
            categorie_id: ID de la catégorie à supprimer

        Returns:
            True si suppression réussie, False sinon
        """
        pass

    @abstractmethod
    def has_produits(self, categorie_id: CategorieId) -> bool:
        """
        Vérifie si une catégorie contient des produits

        Args:
            categorie_id: ID de la catégorie

        Returns:
            True si la catégorie contient des produits, False sinon
        """
        pass
