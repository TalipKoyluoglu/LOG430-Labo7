"""
Service de communication avec le service-inventaire
Pour la décrémentation des stocks centraux lors du check-out
"""

import requests
import logging
from typing import Dict, Any
from uuid import UUID

logger = logging.getLogger("commandes")


class StockService:
    """
    Service pour communiquer avec le service-inventaire
    Gère la décrémentation des stocks centraux lors des commandes e-commerce
    """

    def __init__(self, inventaire_base_url: str = "http://inventaire-service:8000"):
        self.base_url = inventaire_base_url.rstrip("/")

    def verifier_stock_central(self, produit_id: str) -> Dict[str, Any]:
        """
        Vérifie le stock central disponible pour un produit

        Args:
            produit_id: UUID du produit

        Returns:
            Dict avec les infos de stock {quantite, niveau, nom_produit}
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/ddd/inventaire/stock-central/{produit_id}/",
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "quantite": data.get("quantite", 0),
                    "niveau": data.get("niveau", "Indisponible"),
                    "nom_produit": data.get("nom_produit", "Produit inconnu"),
                }
            else:
                logger.warning(f"Produit {produit_id} non trouvé dans stock central")
                return {
                    "success": False,
                    "quantite": 0,
                    "niveau": "Indisponible",
                    "error": "Produit non trouvé",
                }

        except requests.RequestException as e:
            logger.error(f"Erreur communication service-inventaire: {e}")
            return {
                "success": False,
                "quantite": 0,
                "niveau": "Indisponible",
                "error": f"Erreur réseau: {str(e)}",
            }

    def diminuer_stock_central(self, produit_id: str, quantite: int) -> Dict[str, Any]:
        """
        Diminue le stock central d'un produit

        Args:
            produit_id: UUID du produit
            quantite: Quantité à décrémenter

        Returns:
            Dict avec le résultat de l'opération
        """
        try:
            response = requests.post(
                f"{self.base_url}/api/ddd/inventaire/diminuer-stock/",
                json={"produit_id": produit_id, "quantite": quantite},
                headers={"Content-Type": "application/json"},
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                logger.info(
                    f"Stock diminué: {produit_id} -{quantite} = {data.get('nouvelle_quantite')}"
                )
                return {
                    "success": True,
                    "message": data.get("message", "Stock diminué"),
                    "nouvelle_quantite": data.get("nouvelle_quantite"),
                    "niveau": data.get("niveau"),
                }
            else:
                error_data = (
                    response.json()
                    if response.headers.get("content-type") == "application/json"
                    else {}
                )
                error_msg = error_data.get("error", f"HTTP {response.status_code}")
                logger.error(f"Erreur diminution stock {produit_id}: {error_msg}")
                return {"success": False, "error": error_msg}

        except requests.RequestException as e:
            logger.error(f"Erreur réseau diminution stock {produit_id}: {e}")
            return {"success": False, "error": f"Erreur réseau: {str(e)}"}

    def valider_stocks_suffisants(self, produits_demandes: list) -> Dict[str, Any]:
        """
        Valide que tous les produits demandés ont un stock suffisant

        Args:
            produits_demandes: [{'produit_id': str, 'quantite': int, 'nom_produit': str}]

        Returns:
            Dict avec le résultat de validation
        """
        stocks_insuffisants = []
        stocks_valides = []

        for produit in produits_demandes:
            produit_id = produit["produit_id"]
            quantite_demandee = produit["quantite"]

            stock_info = self.verifier_stock_central(produit_id)

            if not stock_info["success"]:
                stocks_insuffisants.append(
                    {
                        "produit_id": produit_id,
                        "nom_produit": produit.get("nom_produit", "Produit inconnu"),
                        "quantite_demandee": quantite_demandee,
                        "quantite_disponible": 0,
                        "raison": stock_info.get("error", "Stock indisponible"),
                    }
                )
            elif stock_info["quantite"] < quantite_demandee:
                stocks_insuffisants.append(
                    {
                        "produit_id": produit_id,
                        "nom_produit": produit.get(
                            "nom_produit", stock_info["nom_produit"]
                        ),
                        "quantite_demandee": quantite_demandee,
                        "quantite_disponible": stock_info["quantite"],
                        "raison": "Quantité insuffisante",
                    }
                )
            else:
                stocks_valides.append(
                    {
                        "produit_id": produit_id,
                        "nom_produit": produit.get(
                            "nom_produit", stock_info["nom_produit"]
                        ),
                        "quantite_demandee": quantite_demandee,
                        "quantite_disponible": stock_info["quantite"],
                    }
                )

        return {
            "tous_suffisants": len(stocks_insuffisants) == 0,
            "stocks_valides": stocks_valides,
            "stocks_insuffisants": stocks_insuffisants,
            "resume": {
                "produits_ok": len(stocks_valides),
                "produits_ko": len(stocks_insuffisants),
                "total_produits": len(produits_demandes),
            },
        }
