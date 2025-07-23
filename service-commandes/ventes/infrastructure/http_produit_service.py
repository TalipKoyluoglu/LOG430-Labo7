"""
Implémentation HTTP du ProduitService
Infrastructure layer - communication avec le service externe produits
"""

import os
import requests
from typing import Optional
from uuid import UUID
from decimal import Decimal

from ..application.services.produit_service import ProduitService
from ..domain.value_objects import ProduitInfo, ProduitId


class HttpProduitService(ProduitService):
    """
    Implémentation concrète du ProduitService utilisant HTTP
    Responsabilité: Communication réseau avec le service produits externe
    """

    def __init__(self, base_url: Optional[str] = None):
        if base_url is None:
            # Utilise la variable d'environnement configurée dans docker-compose
            base_url = os.environ.get(
                "PRODUCT_SERVICE_URL", "http://catalogue-service:8000"
            )
        self.base_url = base_url

    def get_produit_details(self, produit_id: UUID) -> Optional[ProduitInfo]:
        """
        Récupère les détails d'un produit depuis le service externe via HTTP

        Args:
            produit_id: ID du produit à récupérer

        Returns:
            ProduitInfo si trouvé, None si erreur réseau ou produit inexistant
        """
        try:
            # Utilisation de l'API DDD du service-catalogue
            response = requests.get(
                f"{self.base_url}/api/ddd/catalogue/produits/{produit_id}/", timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                return ProduitInfo(
                    id=ProduitId(produit_id),
                    nom=data["nom"],
                    prix=Decimal(str(data["prix"])),
                )
            elif response.status_code == 404:
                return None
            else:
                # Log de l'erreur en production
                print(f"Erreur service produits: {response.status_code}")
                return None

        except (requests.RequestException, KeyError, ValueError) as e:
            # Log de l'erreur en production
            print(f"Erreur communication service produits: {e}")
            return None
