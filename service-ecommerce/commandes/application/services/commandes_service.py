"""
Service de communication avec le service-commandes externe
Architecture microservices - Création de commandes finales
"""

import uuid
import logging
import requests
from typing import Dict, Any
from django.conf import settings

from ...domain.value_objects import CommandeEcommerce
from ...domain.exceptions import (
    ServiceExterneIndisponibleError,
    CreationCommandeEchecError,
)

logger = logging.getLogger("commandes")


class CommandesService:
    """
    Service pour communiquer avec le service-commandes externe (port 8003)
    Responsable de créer les commandes finales après validation
    """

    def __init__(self):
        self.commandes_url = settings.SERVICES.get(
            "COMMANDES", "http://commandes-service:8003"
        )

    def creer_commande_ecommerce(
        self, commande_ecommerce: CommandeEcommerce
    ) -> uuid.UUID:
        """
        Crée une commande dans le service-commandes externe

        Args:
            commande_ecommerce: Value Object contenant les données de commande

        Returns:
            UUID de la commande créée

        Raises:
            CreationCommandeEchecError: Si la création échoue
            ServiceExterneIndisponibleError: Si le service est indisponible
        """
        try:
            # Préparer les données pour l'API du service-commandes
            # Note: Adaptation aux APIs existantes du service-commandes

            # D'abord, vérifier si on peut utiliser l'API de création de vente
            # pour les commandes e-commerce

            # Pour l'instant, créer une vente standard avec un magasin virtuel "E-commerce"
            magasin_ecommerce_id = (
                "11111111-1111-1111-1111-111111111111"  # Magasin virtuel
            )

            # Créer une commande par ligne de produit (limitation API actuelle)
            commandes_creees = []

            for ligne in commande_ecommerce.lignes_commande:
                vente_data = {
                    "magasin_id": magasin_ecommerce_id,
                    "produit_id": str(ligne.produit_id),
                    "quantite": ligne.quantite,
                    "client_id": str(commande_ecommerce.client_id),
                }

                commande_id = self._creer_vente_simple(vente_data)
                commandes_creees.append(commande_id)

                logger.debug(
                    f"Vente créée pour produit {ligne.produit_id}: {commande_id}"
                )

            # Retourner l'ID de la première commande comme référence principale
            # Dans un vraie implémentation, on créerait une commande composite
            commande_principale_id = (
                commandes_creees[0] if commandes_creees else uuid.uuid4()
            )

            logger.info(
                f"Commande e-commerce créée avec succès: {commande_principale_id}"
            )
            logger.info(
                f"Total de {len(commandes_creees)} ventes créées dans le service-commandes"
            )

            return commande_principale_id

        except Exception as e:
            logger.error(f"Erreur lors de la création de commande e-commerce: {str(e)}")
            raise CreationCommandeEchecError(
                f"Impossible de créer la commande: {str(e)}"
            )

    def _creer_vente_simple(self, vente_data: Dict[str, Any]) -> uuid.UUID:
        """
        Crée une vente simple via l'API existante du service-commandes

        Args:
            vente_data: Données de la vente

        Returns:
            UUID de la vente créée
        """
        try:
            url = f"{self.commandes_url}/api/ddd/ventes/enregistrer/"

            logger.debug(f"Création vente via URL: {url}")
            logger.debug(f"Données envoyées: {vente_data}")

            response = requests.post(
                url,
                json=vente_data,
                timeout=10,
                headers={"Content-Type": "application/json"},
            )

            logger.debug(f"Réponse status: {response.status_code}")
            logger.debug(f"Réponse contenu: {response.text}")

            if response.status_code not in [200, 201]:
                raise CreationCommandeEchecError(
                    f"Échec création vente: {response.status_code} - {response.text}"
                )

            response_data = response.json()

            if not response_data.get("success"):
                raise CreationCommandeEchecError(
                    f"Création vente échouée: {response_data.get('error', 'Erreur inconnue')}"
                )

            vente_id = response_data["vente"]["id"]
            return uuid.UUID(vente_id)

        except requests.RequestException as e:
            logger.error(f"Erreur communication avec service-commandes: {str(e)}")
            raise ServiceExterneIndisponibleError("commandes", str(e))
        except Exception as e:
            logger.error(f"Erreur lors de la création de vente: {str(e)}")
            raise CreationCommandeEchecError(f"Erreur technique: {str(e)}")

    def verifier_disponibilite_service(self) -> bool:
        """
        Vérifie si le service-commandes est disponible

        Returns:
            bool: True si le service répond
        """
        try:
            # Utiliser un endpoint de health check si disponible
            url = f"{self.commandes_url}/health/"  # Ou une URL de status

            response = requests.get(url, timeout=3)
            return response.status_code == 200

        except Exception as e:
            logger.warning(f"Service-commandes indisponible: {str(e)}")
            return False
