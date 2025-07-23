"""
Service de communication avec le service-catalogue
Architecture microservices - Communication inter-services
"""

import uuid
import logging
import requests
from decimal import Decimal
from typing import Optional, Dict, Any
from django.conf import settings

from ...domain.exceptions import ProduitInexistantError

logger = logging.getLogger("panier")


class CatalogueService:
    """
    Service pour communiquer avec le microservice catalogue
    Responsable de récupérer les informations des produits
    """

    def __init__(self):
        self.catalogue_url = settings.SERVICES.get(
            "CATALOGUE", "http://catalogue-service:8000"
        )

    def obtenir_produit(self, produit_id: uuid.UUID) -> Dict[str, Any]:
        """
        Récupère les informations d'un produit depuis le service-catalogue

        Args:
            produit_id: UUID du produit à récupérer

        Returns:
            Dict contenant les informations du produit

        Raises:
            ProduitInexistantError: Si le produit n'existe pas
        """
        try:
            # Utiliser l'URL DDD réelle du service-catalogue
            url = f"{self.catalogue_url}/api/ddd/catalogue/produits/{produit_id}/"

            logger.debug(f"Récupération produit {produit_id} depuis catalogue: {url}")

            response = requests.get(url, timeout=5)

            if response.status_code == 404:
                logger.warning(f"Produit {produit_id} non trouvé dans le catalogue")
                raise ProduitInexistantError(
                    f"Produit {produit_id} n'existe pas dans le catalogue"
                )

            response.raise_for_status()
            produit_data = response.json()

            logger.debug(f"Produit récupéré: {produit_data.get('nom', 'N/A')}")

            # Normaliser les données pour le domaine panier
            return {
                "id": uuid.UUID(produit_data["id"]),
                "nom": produit_data["nom"],
                "prix": Decimal(str(produit_data["prix"])),
                "description": produit_data.get("description", ""),
                "actif": produit_data.get("actif", True),
            }

        except requests.RequestException as e:
            logger.error(f"Erreur communication avec service-catalogue: {str(e)}")
            raise ProduitInexistantError(
                f"Impossible de vérifier l'existence du produit {produit_id}"
            )
        except Exception as e:
            logger.error(
                f"Erreur lors de la récupération du produit {produit_id}: {str(e)}"
            )
            raise ProduitInexistantError(
                f"Erreur lors de la récupération du produit {produit_id}"
            )

    def verifier_produit_actif(self, produit_id: uuid.UUID) -> bool:
        """
        Vérifie qu'un produit existe et est actif

        Args:
            produit_id: UUID du produit à vérifier

        Returns:
            bool: True si le produit existe et est actif
        """
        try:
            produit = self.obtenir_produit(produit_id)
            return produit.get("actif", False)
        except ProduitInexistantError:
            return False
