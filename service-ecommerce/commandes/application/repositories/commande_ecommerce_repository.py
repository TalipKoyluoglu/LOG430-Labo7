"""
Repository pour les commandes e-commerce
Interface abstraite et implémentation concrète
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from ...domain.entities import CommandeEcommerce as CommandeEcommerceDomain


class CommandeEcommerceRepository(ABC):
    """
    Interface abstraite pour la persistance des commandes e-commerce
    """

    @abstractmethod
    def save(self, commande: CommandeEcommerceDomain) -> CommandeEcommerceDomain:
        """
        Sauvegarde une commande e-commerce
        """
        pass

    @abstractmethod
    def get_by_id(self, commande_id: UUID) -> Optional[CommandeEcommerceDomain]:
        """
        Récupère une commande par son ID
        """
        pass

    @abstractmethod
    def get_by_client_id(
        self, client_id: UUID, limit: int = 50
    ) -> List[CommandeEcommerceDomain]:
        """
        Récupère toutes les commandes d'un client
        """
        pass

    @abstractmethod
    def get_by_checkout_id(
        self, checkout_id: UUID
    ) -> Optional[CommandeEcommerceDomain]:
        """
        Récupère une commande par son checkout ID
        """
        pass

    @abstractmethod
    def get_recent_commandes(
        self, days: int = 30, limit: int = 100
    ) -> List[CommandeEcommerceDomain]:
        """
        Récupère les commandes récentes
        """
        pass
