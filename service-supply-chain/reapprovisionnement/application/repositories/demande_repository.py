"""
Repository abstrait pour les demandes de réapprovisionnement
Interface pour la persistance des entités du domaine.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from ...domain.value_objects import DemandeId
from ...domain.entities import StatutDemande


class DemandeRepository(ABC):
    """Interface abstraite pour la gestion des demandes"""

    @abstractmethod
    def get_by_id(self, demande_id: DemandeId) -> Optional[Dict[str, Any]]:
        """Récupère une demande par son ID"""
        pass

    @abstractmethod
    def get_demandes_en_attente(self) -> List[Dict[str, Any]]:
        """Récupère toutes les demandes en attente"""
        pass

    @abstractmethod
    def mettre_a_jour_statut(
        self, demande_id: DemandeId, statut: StatutDemande
    ) -> bool:
        """Met à jour le statut d'une demande"""
        pass

    @abstractmethod
    def approuver_demande(self, demande_id: DemandeId) -> bool:
        """Approuve une demande avec transfert de stock automatique"""
        pass

    @abstractmethod
    def rejeter_demande(self, demande_id: DemandeId) -> bool:
        """Rejette une demande sans transfert de stock"""
        pass
