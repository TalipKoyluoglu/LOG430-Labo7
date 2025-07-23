"""
Implémentation HTTP du service Stock
Communication avec le service inventaire via requêtes HTTP.
"""

import requests
import logging
from django.conf import settings

from ..application.services.stock_service import StockService
from ..domain.value_objects import ProduitId, MagasinId, Quantite
from ..domain.exceptions import CommunicationServiceError

logger = logging.getLogger(__name__)


class HttpStockService(StockService):
    """Implémentation HTTP du service inventaire"""

    def __init__(self):
        self.stock_service_url = settings.STOCK_SERVICE_URL

    def diminuer_stock_central(self, produit_id: ProduitId, quantite: Quantite) -> bool:
        """Diminue le stock central d'un produit"""
        try:
            url = (
                f"{self.stock_service_url}/api/v1/stock/central/{produit_id}/decrease/"
            )
            data = {"quantite": int(quantite)}

            response = requests.put(url, json=data, timeout=10)

            if response.status_code == 200:
                logger.info(f"Stock central diminué: {produit_id} (-{quantite})")
                return True
            else:
                logger.error(f"Erreur diminution stock central: {response.text}")
                raise CommunicationServiceError(
                    f"Erreur lors de la diminution du stock central: {response.text}",
                    "service-inventaire",
                    response.status_code,
                )

        except requests.RequestException as e:
            logger.error(f"Erreur de connexion: {e}")
            raise CommunicationServiceError(
                f"Impossible de diminuer le stock central: {e}", "service-inventaire"
            )

    def augmenter_stock_central(
        self, produit_id: ProduitId, quantite: Quantite
    ) -> bool:
        """Augmente le stock central d'un produit (pour rollback)"""
        try:
            url = (
                f"{self.stock_service_url}/api/v1/stock/central/{produit_id}/increase/"
            )
            data = {"quantite": int(quantite)}

            response = requests.put(url, json=data, timeout=10)

            if response.status_code == 200:
                logger.info(
                    f"Stock central augmenté (rollback): {produit_id} (+{quantite})"
                )
                return True
            else:
                logger.error(f"Erreur augmentation stock central: {response.text}")
                raise CommunicationServiceError(
                    f"Erreur lors de l'augmentation du stock central: {response.text}",
                    "service-inventaire",
                    response.status_code,
                )

        except requests.RequestException as e:
            logger.error(f"Erreur de connexion: {e}")
            raise CommunicationServiceError(
                f"Impossible d'augmenter le stock central: {e}", "service-inventaire"
            )

    def augmenter_stock_local(
        self, produit_id: ProduitId, magasin_id: MagasinId, quantite: Quantite
    ) -> bool:
        """Augmente le stock local d'un magasin"""
        try:
            url = f"{self.stock_service_url}/api/v1/stock/local/{produit_id}/{magasin_id}/increase/"
            data = {"quantite": int(quantite)}

            response = requests.put(url, json=data, timeout=10)

            if response.status_code == 200:
                logger.info(
                    f"Stock local augmenté: {produit_id} magasin {magasin_id} (+{quantite})"
                )
                return True
            else:
                logger.error(f"Erreur augmentation stock local: {response.text}")
                raise CommunicationServiceError(
                    f"Erreur lors de l'augmentation du stock local: {response.text}",
                    "service-inventaire",
                    response.status_code,
                )

        except requests.RequestException as e:
            logger.error(f"Erreur de connexion: {e}")
            raise CommunicationServiceError(
                f"Impossible d'augmenter le stock local: {e}", "service-inventaire"
            )

    def diminuer_stock_local(
        self, produit_id: ProduitId, magasin_id: MagasinId, quantite: Quantite
    ) -> bool:
        """Diminue le stock local d'un magasin (pour rollback)"""
        try:
            url = f"{self.stock_service_url}/api/v1/stock/local/{produit_id}/{magasin_id}/decrease/"
            data = {"quantite": int(quantite)}

            response = requests.put(url, json=data, timeout=10)

            if response.status_code == 200:
                logger.info(
                    f"Stock local diminué (rollback): {produit_id} magasin {magasin_id} (-{quantite})"
                )
                return True
            else:
                logger.error(f"Erreur diminution stock local: {response.text}")
                raise CommunicationServiceError(
                    f"Erreur lors de la diminution du stock local: {response.text}",
                    "service-inventaire",
                    response.status_code,
                )

        except requests.RequestException as e:
            logger.error(f"Erreur de connexion: {e}")
            raise CommunicationServiceError(
                f"Impossible de diminuer le stock local: {e}", "service-inventaire"
            )
