"""
Implémentation HTTP du repository des demandes
Communication avec le service inventaire pour la persistance des demandes.
"""

import requests
import logging
from typing import List, Optional, Dict, Any
from django.conf import settings

from ..application.repositories.demande_repository import DemandeRepository
from ..domain.entities import DemandeReapprovisionnement
from ..domain.value_objects import DemandeId, ProduitId, MagasinId, Quantite
from ..domain.entities import StatutDemande
from ..domain.exceptions import CommunicationServiceError

logger = logging.getLogger(__name__)


class HttpDemandeRepository(DemandeRepository):
    """Repository HTTP pour les demandes de réapprovisionnement"""

    def __init__(self):
        self.stock_service_url = settings.STOCK_SERVICE_URL

    def sauvegarder(self, demande: DemandeReapprovisionnement) -> None:
        """Sauvegarde une demande via le service inventaire"""
        try:
            url = f"{self.stock_service_url}/api/v1/demandes/"
            data = {
                "id": str(demande.id),
                "produit_id": str(demande.produit_id),
                "magasin_id": str(demande.magasin_id),
                "quantite": int(demande.quantite),
                "statut": demande.statut.value,
                "justification": demande.justification,
                "date_creation": demande.date_creation.isoformat(),
                "date_traitement": (
                    demande.date_traitement.isoformat()
                    if demande.date_traitement
                    else None
                ),
            }

            response = requests.post(url, json=data, timeout=10)

            if response.status_code in [200, 201]:
                logger.info(f"Demande sauvegardée: {demande.id}")
            else:
                logger.error(f"Erreur sauvegarde demande: {response.text}")
                raise CommunicationServiceError(
                    f"Erreur lors de la sauvegarde de la demande: {response.text}",
                    "service-inventaire",
                    response.status_code,
                )

        except requests.RequestException as e:
            logger.error(f"Erreur de connexion: {e}")
            raise CommunicationServiceError(
                f"Impossible de sauvegarder la demande: {e}", "service-inventaire"
            )

    def get_by_id(self, demande_id: DemandeId) -> Optional[Dict[str, Any]]:
        """Récupère une demande par son ID depuis le service inventaire"""
        try:
            url = f"{self.stock_service_url}/api/ddd/inventaire/demandes/{demande_id}/"

            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                logger.info(f"Demande récupérée: {demande_id}")
                return data
            elif response.status_code == 404:
                logger.warning(f"Demande {demande_id} non trouvée")
                return None
            else:
                logger.error(f"Erreur récupération demande: {response.text}")
                raise CommunicationServiceError(
                    f"Erreur lors de la récupération de la demande: {response.text}",
                    "service-inventaire",
                    response.status_code,
                )

        except requests.RequestException as e:
            logger.error(f"Erreur de connexion: {e}")
            raise CommunicationServiceError(
                f"Impossible de récupérer la demande: {e}", "service-inventaire"
            )

    def get_demandes_en_attente(self) -> List[Dict[str, Any]]:
        """Liste toutes les demandes en attente via le service inventaire"""
        try:
            url = f"{self.stock_service_url}/api/ddd/inventaire/demandes/en-attente/"

            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                # Extraire les résultats de la structure DDD
                if "demandes" in data:
                    return data["demandes"]
                elif "results" in data:
                    return data["results"]
                elif isinstance(data, list):
                    return data
                else:
                    return []
            else:
                logger.error(f"Erreur listing demandes: {response.text}")
                raise CommunicationServiceError(
                    f"Erreur lors du listing des demandes: {response.text}",
                    "service-inventaire",
                    response.status_code,
                )

        except requests.RequestException as e:
            logger.error(f"Erreur de connexion: {e}")
            raise CommunicationServiceError(
                f"Impossible de lister les demandes: {e}", "service-inventaire"
            )

    def approuver_demande(self, demande_id: DemandeId) -> bool:
        """Approuve une demande via le service inventaire"""
        try:
            url = f"{self.stock_service_url}/api/ddd/inventaire/demandes/{demande_id}/approuver/"

            response = requests.put(url, timeout=10)

            if response.status_code == 200:
                logger.info(f"Demande approuvée: {demande_id}")
                return True
            else:
                logger.error(f"Erreur approbation demande: {response.text}")
                raise CommunicationServiceError(
                    f"Erreur lors de l'approbation de la demande: {response.text}",
                    "service-inventaire",
                    response.status_code,
                )

        except requests.RequestException as e:
            logger.error(f"Erreur de connexion: {e}")
            raise CommunicationServiceError(
                f"Impossible d'approuver la demande: {e}", "service-inventaire"
            )

    def rejeter_demande(self, demande_id: DemandeId) -> bool:
        """Rejette une demande via le service inventaire"""
        try:
            url = f"{self.stock_service_url}/api/ddd/inventaire/demandes/{demande_id}/rejeter/"

            response = requests.put(url, timeout=10)

            if response.status_code == 200:
                logger.info(f"Demande rejetée: {demande_id}")
                return True
            else:
                logger.error(f"Erreur rejet demande: {response.text}")
                raise CommunicationServiceError(
                    f"Erreur lors du rejet de la demande: {response.text}",
                    "service-inventaire",
                    response.status_code,
                )

        except requests.RequestException as e:
            logger.error(f"Erreur de connexion: {e}")
            raise CommunicationServiceError(
                f"Impossible de rejeter la demande: {e}", "service-inventaire"
            )

    def _mapper_vers_entite(self, data: dict) -> DemandeReapprovisionnement:
        """Mappe les données JSON vers une entité DemandeReapprovisionnement"""
        from datetime import datetime

        return DemandeReapprovisionnement(
            id=DemandeId(data["id"]),
            produit_id=ProduitId(data["produit_id"]),
            magasin_id=MagasinId(data["magasin_id"]),
            quantite=Quantite(data["quantite"]),
            statut=StatutDemande(data["statut"]),
            justification=data.get("justification"),
            date_creation=datetime.fromisoformat(data["date_creation"]),
            date_traitement=(
                datetime.fromisoformat(data["date_traitement"])
                if data.get("date_traitement")
                else None
            ),
        )

    def mettre_a_jour_statut(self, demande_id, nouveau_statut):
        """
        Implémentation temporaire pour satisfaire l'interface abstraite.
        """
        logger.warning(
            "Appel de mettre_a_jour_statut (dummy) : à implémenter selon la logique métier."
        )
        return True
