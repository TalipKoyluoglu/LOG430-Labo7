"""
Interface du service Magasin pour la validation des entités externes
Définit le contrat de validation des magasins via API externe.
"""

from abc import ABC, abstractmethod
from ...domain.value_objects import MagasinId
from ...domain.exceptions import MagasinInexistantError


class MagasinService(ABC):
    """Interface abstraite pour la validation des magasins"""

    @abstractmethod
    def magasin_existe(self, magasin_id: MagasinId) -> bool:
        """
        Vérifie si un magasin existe dans le service correspondant
        """
        pass

    @abstractmethod
    def valider_magasin_existe(self, magasin_id: MagasinId) -> None:
        """
        Valide qu'un magasin existe, lève une exception sinon
        """
        if not self.magasin_existe(magasin_id):
            raise MagasinInexistantError(f"Le magasin {magasin_id} n'existe pas")

    @abstractmethod
    def get_nom_magasin(self, magasin_id: MagasinId) -> str:
        """
        Récupère le nom d'un magasin pour l'affichage
        """
        pass
