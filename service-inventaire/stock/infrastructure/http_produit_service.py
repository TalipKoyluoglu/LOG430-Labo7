"""
Implémentation HTTP du service Produit
Communique avec le service-catalogue via HTTP pour valider les produits.
"""

import requests
import logging
from typing import Optional

from ..application.services.produit_service import ProduitService
from ..domain.value_objects import ProduitId
from ..domain.exceptions import ProduitInexistantError

logger = logging.getLogger(__name__)


class HttpProduitService(ProduitService):
    """Implémentation concrète du service Produit utilisant HTTP"""

    def __init__(self, catalogue_base_url: str = "http://catalogue-service:8000"):
        self.catalogue_base_url = catalogue_base_url.rstrip("/")
        logger.debug(
            f"HttpProduitService initialisé avec URL: {self.catalogue_base_url}"
        )

    def produit_existe(self, produit_id: ProduitId) -> bool:
        """Vérifie si un produit existe dans le service catalogue"""
        logger.debug(f"Vérification de l'existence du produit: {produit_id}")

        try:
            url = f"{self.catalogue_base_url}/api/ddd/catalogue/produits/{produit_id}/"
            logger.debug(f"Appel HTTP GET: {url}")

            response = requests.get(url, timeout=5)

            exists = response.status_code == 200
            logger.debug(
                f"Produit {produit_id} existe: {exists} (status: {response.status_code})"
            )
            return exists

        except requests.RequestException as e:
            logger.warning(
                f"Erreur réseau lors de la vérification du produit {produit_id}: {e}"
            )
            # En cas d'erreur réseau, on assume que le produit n'existe pas
            return False

    def valider_produit_existe(self, produit_id: ProduitId) -> None:
        """
        Valide qu'un produit existe, lève une exception sinon
        """
        logger.debug(f"Validation de l'existence du produit: {produit_id}")

        if not self.produit_existe(produit_id):
            logger.error(f"Produit inexistant: {produit_id}")
            raise ProduitInexistantError(f"Le produit {produit_id} n'existe pas")

        logger.debug(f"Produit validé avec succès: {produit_id}")

    def get_nom_produit(self, produit_id: ProduitId) -> str:
        """Récupère le nom d'un produit pour l'affichage"""
        logger.debug(f"Récupération du nom du produit: {produit_id}")

        try:
            url = f"{self.catalogue_base_url}/api/ddd/catalogue/produits/{produit_id}/"
            logger.debug(f"Appel HTTP GET: {url}")

            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                data = response.json()
                nom = data.get("nom", f"Produit {produit_id}")
                logger.debug(f"Nom du produit {produit_id} récupéré: {nom}")
                return nom
            else:
                logger.warning(
                    f"Impossible de récupérer le nom du produit {produit_id} (status: {response.status_code})"
                )
                return f"Produit {produit_id}"

        except requests.RequestException as e:
            logger.warning(
                f"Erreur réseau lors de la récupération du nom du produit {produit_id}: {e}"
            )
            return f"Produit {produit_id}"
