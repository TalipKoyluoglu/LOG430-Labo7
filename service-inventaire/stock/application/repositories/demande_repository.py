"""
Interface du repository Demande pour la couche Application
Définit le contrat d'accès aux données pour les demandes de réapprovisionnement.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from ...domain.entities import DemandeReapprovisionnement, StatutDemandeStock
from ...domain.value_objects import DemandeId, ProduitId, MagasinId


class DemandeRepository(ABC):
    """Interface abstraite pour l'accès aux données des demandes"""

    @abstractmethod
    def get_by_id(self, demande_id: DemandeId) -> Optional[DemandeReapprovisionnement]:
        """
        Récupère une demande par son identifiant
        """
        pass

    @abstractmethod
    def get_demandes_by_statut(
        self, statut: StatutDemandeStock
    ) -> List[DemandeReapprovisionnement]:
        """
        Récupère toutes les demandes avec un statut spécifique
        """
        pass

    @abstractmethod
    def get_demandes_en_attente(self) -> List[DemandeReapprovisionnement]:
        """
        Récupère toutes les demandes en attente de traitement
        """
        pass

    @abstractmethod
    def get_demandes_by_magasin(
        self, magasin_id: MagasinId
    ) -> List[DemandeReapprovisionnement]:
        """
        Récupère toutes les demandes d'un magasin spécifique
        """
        pass

    @abstractmethod
    def get_demandes_by_produit(
        self, produit_id: ProduitId
    ) -> List[DemandeReapprovisionnement]:
        """
        Récupère toutes les demandes pour un produit spécifique
        """
        pass

    @abstractmethod
    def save(self, demande: DemandeReapprovisionnement) -> DemandeReapprovisionnement:
        """
        Sauvegarde une demande (création ou mise à jour)
        """
        pass

    @abstractmethod
    def delete(self, demande_id: DemandeId) -> bool:
        """
        Supprime une demande
        """
        pass

    @abstractmethod
    def exists_demande_en_attente(
        self, produit_id: ProduitId, magasin_id: MagasinId
    ) -> bool:
        """
        Vérifie s'il existe déjà une demande en attente pour ce produit/magasin
        """
        pass
