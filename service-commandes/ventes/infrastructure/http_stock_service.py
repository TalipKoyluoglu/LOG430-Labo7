"""
Implémentation HTTP du service Stock
Interface concrète pour communiquer avec le service-inventaire via HTTP.
"""

import requests
from typing import List, Optional
from uuid import UUID
from django.conf import settings

from ..application.services.stock_service import StockService
from ..domain.value_objects import StockInfo, ProduitId, MagasinId


class HttpStockService(StockService):
    """Implémentation HTTP du service Stock pour communication inter-services"""

    def __init__(self, base_url: str = "http://inventaire-service:8000"):
        self.base_url = base_url.rstrip("/")

    def get_stock_local(self, magasin_id: UUID, produit_id: UUID) -> StockInfo:
        """Récupère les informations de stock local via l'API DDD du service-inventaire"""
        try:
            # Utilisation de l'API DDD du service-inventaire
            response = requests.get(
                f"{self.base_url}/api/ddd/inventaire/stock-local/{produit_id}/{magasin_id}/",
                timeout=30,
            )

            if response.status_code == 200:
                data = response.json()
                return StockInfo(
                    produit_id=ProduitId(produit_id),
                    magasin_id=MagasinId(magasin_id),
                    quantite_disponible=data.get("quantite", 0),
                )
            else:
                # Stock non trouvé
                return StockInfo(
                    produit_id=ProduitId(produit_id),
                    magasin_id=MagasinId(magasin_id),
                    quantite_disponible=0,
                )

        except requests.RequestException:
            # En cas d'erreur réseau, retourner stock indisponible
            return StockInfo(
                produit_id=ProduitId(produit_id),
                magasin_id=MagasinId(magasin_id),
                quantite_disponible=0,
            )

    def decrease_stock(self, magasin_id: UUID, produit_id: UUID, quantite: int) -> None:
        """Diminue le stock d'un produit dans un magasin"""
        try:
            # Utilisation de l'API DDD du service-inventaire
            response = requests.post(
                f"{self.base_url}/api/ddd/inventaire/diminuer-stock/",
                json={
                    "produit_id": str(produit_id),
                    "magasin_id": str(magasin_id),
                    "quantite": quantite,
                },
                timeout=30,
            )

            if response.status_code != 200:
                print(f"Erreur lors de la diminution de stock: {response.text}")

        except requests.RequestException as e:
            print(f"Erreur de communication avec le service inventaire: {e}")

    def increase_stock(self, magasin_id: UUID, produit_id: UUID, quantite: int) -> None:
        """Augmente le stock d'un produit dans un magasin (pour annulation)"""
        try:
            # Utilisation de l'API DDD du service-inventaire
            response = requests.post(
                f"{self.base_url}/api/ddd/inventaire/augmenter-stock/",
                json={
                    "produit_id": str(produit_id),
                    "magasin_id": str(magasin_id),
                    "quantite": quantite,
                },
                timeout=30,
            )

            if response.status_code != 200:
                print(f"Erreur lors de l'augmentation de stock: {response.text}")

        except requests.RequestException as e:
            print(f"Erreur de communication avec le service inventaire: {e}")

    def get_all_stock_local(self, magasin_id: UUID) -> List[StockInfo]:
        """Récupère tous les stocks locaux d'un magasin"""
        try:
            # Utilisation de l'API DDD du service-inventaire
            response = requests.get(
                f"{self.base_url}/api/ddd/inventaire/stocks-locaux/{magasin_id}/",
                timeout=30,
            )

            if response.status_code == 200:
                data = response.json()
                stocks = data.get("stocks", [])
                return [
                    StockInfo(
                        produit_id=ProduitId(UUID(stock.get("produit_id"))),
                        magasin_id=MagasinId(magasin_id),
                        quantite_disponible=stock.get("quantite", 0),
                    )
                    for stock in stocks
                ]
            else:
                return []

        except requests.RequestException:
            return []
