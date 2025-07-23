"""
Interface Repository pour le domaine Panier
Architecture DDD - Port vers l'infrastructure
"""

import uuid
from abc import ABC, abstractmethod
from typing import Optional, List

from ...domain.entities import Panier


class PanierRepository(ABC):
    """
    Interface repository pour les opérations de persistance du Panier
    Définit le contrat entre le domaine et l'infrastructure
    """

    @abstractmethod
    def save(self, panier: Panier) -> None:
        """
        Sauvegarde un panier (création ou mise à jour)

        Args:
            panier: Entité Panier à sauvegarder
        """
        pass

    @abstractmethod
    def get_by_id(self, panier_id: uuid.UUID) -> Optional[Panier]:
        """
        Récupère un panier par son ID

        Args:
            panier_id: UUID du panier

        Returns:
            Panier ou None si non trouvé
        """
        pass

    @abstractmethod
    def get_by_client_id(self, client_id: uuid.UUID) -> Optional[Panier]:
        """
        Récupère le panier actuel d'un client

        Args:
            client_id: UUID du client

        Returns:
            Panier ou None si aucun panier actuel
        """
        pass

    @abstractmethod
    def delete(self, panier_id: uuid.UUID) -> bool:
        """
        Supprime un panier

        Args:
            panier_id: UUID du panier à supprimer

        Returns:
            True si supprimé avec succès
        """
        pass

    @abstractmethod
    def get_all_by_client(self, client_id: uuid.UUID) -> List[Panier]:
        """
        Récupère tous les paniers d'un client (historique)

        Args:
            client_id: UUID du client

        Returns:
            Liste des paniers du client
        """
        pass
