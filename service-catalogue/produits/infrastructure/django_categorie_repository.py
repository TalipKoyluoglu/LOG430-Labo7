"""
Implémentation Django basique du CategorieRepository
(Implementation temporaire - à compléter avec le modèle Catégorie)
"""

from typing import List, Optional

from ..application.repositories.categorie_repository import CategorieRepository
from ..domain.entities import Categorie
from ..domain.value_objects import CategorieId


class DjangoCategorieRepository(CategorieRepository):
    """
    Implémentation Django basique du repository Catégorie
    TODO: Implémenter avec un vrai modèle Django Catégorie
    """

    def save(self, categorie: Categorie) -> Categorie:
        """
        TODO: Implémenter avec Django ORM
        """
        return categorie

    def get_by_id(self, categorie_id: CategorieId) -> Optional[Categorie]:
        """
        TODO: Implémenter avec Django ORM
        Pour l'instant, retourne une catégorie fictive
        """
        # Catégorie fictive pour tests
        return Categorie(
            id=categorie_id, nom="Catégorie Test", description="Catégorie de test"
        )

    def get_all(self) -> List[Categorie]:
        """
        TODO: Implémenter avec Django ORM
        """
        return []

    def get_categories_actives(self) -> List[Categorie]:
        """
        TODO: Implémenter avec Django ORM
        """
        return []

    def get_categories_racines(self) -> List[Categorie]:
        """
        TODO: Implémenter avec Django ORM
        """
        return []

    def get_sous_categories(self, parent_id: CategorieId) -> List[Categorie]:
        """
        TODO: Implémenter avec Django ORM
        """
        return []

    def delete(self, categorie_id: CategorieId) -> bool:
        """
        TODO: Implémenter avec Django ORM
        """
        return True

    def has_produits(self, categorie_id: CategorieId) -> bool:
        """
        TODO: Implémenter avec Django ORM
        """
        return False
