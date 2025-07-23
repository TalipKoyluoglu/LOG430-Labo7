"""
Interface Repository pour les clients - DDD
"""

import uuid
from abc import ABC, abstractmethod
from typing import List, Optional
from ...domain.entities import Client
from ...domain.value_objects import Email


class ClientRepository(ABC):
    """
    Interface Repository pour l'entité Client
    Définit les opérations de persistance dans le langage du domaine
    """

    @abstractmethod
    def save(self, client: Client) -> None:
        """
        Sauvegarde un client (création ou mise à jour)
        """
        pass

    @abstractmethod
    def get_by_id(self, client_id: uuid.UUID) -> Optional[Client]:
        """
        Récupère un client par son ID
        """
        pass

    @abstractmethod
    def get_by_email(self, email: Email) -> Optional[Client]:
        """
        Récupère un client par son email
        """
        pass

    @abstractmethod
    def exists_by_email(self, email: Email) -> bool:
        """
        Vérifie si un client existe avec cet email
        """
        pass

    @abstractmethod
    def get_all_active(self) -> List[Client]:
        """
        Récupère tous les clients actifs
        """
        pass

    @abstractmethod
    def delete(self, client_id: uuid.UUID) -> bool:
        """
        Supprime un client (soft delete)
        """
        pass
