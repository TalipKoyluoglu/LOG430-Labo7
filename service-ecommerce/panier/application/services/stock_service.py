"""
Service de communication avec le service-inventaire
Architecture microservices - Gestion du stock e-commerce
"""

import uuid
import logging
import requests
from typing import Dict, Any
from django.conf import settings

from ...domain.exceptions import StockInsuffisantError

logger = logging.getLogger("panier")


class StockService:
    """
    Service pour communiquer avec le microservice inventaire
    Responsable de vérifier et réserver le stock e-commerce
    """

    def __init__(self):
        self.inventaire_url = settings.SERVICES.get(
            "INVENTAIRE", "http://inventaire-service:8002"
        )

    def verifier_stock_disponible(
        self, produit_id: uuid.UUID, quantite_demandee: int
    ) -> bool:
        """
        Vérifie si le stock e-commerce est suffisant pour la quantité demandée

        Args:
            produit_id: UUID du produit
            quantite_demandee: Quantité souhaitée

        Returns:
            bool: True si le stock est suffisant
        """
        try:
            # Utiliser l'URL DDD réelle pour le stock central
            url = (
                f"{self.inventaire_url}/api/ddd/inventaire/stock-central/{produit_id}/"
            )

            logger.debug(
                f"Vérification stock pour produit {produit_id}, quantité: {quantite_demandee}"
            )

            response = requests.get(url, timeout=5)

            if response.status_code == 404:
                logger.warning(f"Aucun stock trouvé pour le produit {produit_id}")
                return False

            response.raise_for_status()
            stock_data = response.json()

            # Le service inventaire retourne 'quantite' pour le stock central
            stock_disponible = stock_data.get("quantite", 0)

            logger.debug(f"Stock central disponible: {stock_disponible}")

            return stock_disponible >= quantite_demandee

        except requests.RequestException as e:
            logger.error(f"Erreur communication avec service-inventaire: {str(e)}")
            # En cas d'erreur, on refuse pour sécurité
            return False
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du stock: {str(e)}")
            return False

    def obtenir_stock_disponible(self, produit_id: uuid.UUID) -> int:
        """
        Récupère la quantité de stock central disponible

        Args:
            produit_id: UUID du produit

        Returns:
            int: Quantité disponible en stock central
        """
        try:
            url = (
                f"{self.inventaire_url}/api/ddd/inventaire/stock-central/{produit_id}/"
            )

            response = requests.get(url, timeout=5)

            if response.status_code == 404:
                return 0

            response.raise_for_status()
            stock_data = response.json()

            return stock_data.get("quantite", 0)

        except Exception as e:
            logger.error(f"Erreur lors de la récupération du stock: {str(e)}")
            return 0

    def reserver_stock(self, produit_id: uuid.UUID, quantite: int) -> bool:
        """
        Réserve temporairement du stock e-commerce (pour le checkout)

        Args:
            produit_id: UUID du produit
            quantite: Quantité à réserver

        Returns:
            bool: True si la réservation a réussi
        """
        try:
            url = f"{self.inventaire_url}/api/stocks/{produit_id}/reserver/"

            data = {"quantite": quantite, "type_reservation": "ecommerce"}

            logger.debug(
                f"Réservation stock: {quantite} unités du produit {produit_id}"
            )

            response = requests.post(url, json=data, timeout=5)

            if response.status_code == 400:
                # Stock insuffisant
                logger.warning(f"Stock insuffisant pour produit {produit_id}")
                return False

            response.raise_for_status()

            logger.debug(f"Réservation réussie pour produit {produit_id}")
            return True

        except Exception as e:
            logger.error(f"Erreur lors de la réservation du stock: {str(e)}")
            return False
