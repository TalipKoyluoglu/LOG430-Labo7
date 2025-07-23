"""
Client HTTP pour le Service Supply Chain via Kong API Gateway
Communication avec les endpoints DDD du service-supply-chain
"""

import requests
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

BASE_URL = "http://kong:8000/api/supply-chain"


class SupplyChainClient:
    """
    Client HTTP pour communiquer avec le service-supply-chain
    Encapsule tous les appels REST vers les endpoints DDD
    """

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-API-Key": "magasin-secret-key-2025",  # Clé API Kong
            }
        )

    def lister_demandes_en_attente(self) -> Dict[str, Any]:
        """
        GET /api/ddd/supply-chain/demandes-en-attente/
        Use Case: ListerDemandesUseCase
        Récupère toutes les demandes de réapprovisionnement en attente
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/ddd/supply-chain/demandes-en-attente/"
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur liste demandes en attente supply-chain: {e}")
            return {
                "success": False,
                "count": 0,
                "demandes": [],
                "error": f"Erreur lors de la récupération des demandes: {str(e)}",
            }

    def valider_demande(self, demande_id: str) -> Dict[str, Any]:
        """
        POST /api/ddd/supply-chain/valider-demande/<id>/
        Use Case: ValiderDemandeUseCase
        Valide une demande avec workflow complexe et rollback automatique

        Args:
            demande_id: UUID de la demande à valider

        Returns:
            Dict avec le résultat de la validation (workflow 3 étapes)
        """
        logger.info("✅ Client API: Validation demande supply-chain %s", demande_id)
        try:
            response = self.session.post(
                f"{self.base_url}/api/ddd/supply-chain/valider-demande/{demande_id}/"
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur validation demande {demande_id}: {e}")
            return {
                "success": False,
                "use_case": "ValiderDemandeUseCase",
                "demande_id": demande_id,
                "error": f"Erreur lors de la validation: {str(e)}",
                "type": "communication_error",
            }

    def rejeter_demande(self, demande_id: str, motif: str) -> Dict[str, Any]:
        """
        POST /api/ddd/supply-chain/rejeter-demande/<id>/
        Use Case: RejeterDemandeUseCase
        Rejette une demande avec motif validé

        Args:
            demande_id: UUID de la demande à rejeter
            motif: Motif de rejet (minimum 5 caractères)

        Returns:
            Dict avec le résultat du rejet
        """
        logger.info("❌ Client API: Rejet demande supply-chain %s", demande_id)
        try:
            data = {"motif": motif}

            response = self.session.post(
                f"{self.base_url}/api/ddd/supply-chain/rejeter-demande/{demande_id}/",
                json=data,
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur rejet demande {demande_id}: {e}")
            return {
                "success": False,
                "use_case": "RejeterDemandeUseCase",
                "demande_id": demande_id,
                "error": f"Erreur lors du rejet: {str(e)}",
                "type": "communication_error",
            }

    def obtenir_statistiques_workflow(self) -> Dict[str, Any]:
        """
        Calcule des statistiques sur le workflow des demandes
        Utilise lister_demandes_en_attente pour analyser les données

        Returns:
            Dict avec statistiques sur les demandes et le workflow
        """
        try:
            demandes_data = self.lister_demandes_en_attente()

            if not demandes_data.get("success", False):
                return {
                    "error": "Impossible de récupérer les demandes",
                    "total_demandes": 0,
                }

            demandes = demandes_data.get("demandes", [])

            # Analyse des demandes
            total_demandes = len(demandes)
            demandes_importantes = [
                d for d in demandes if d.get("est_quantite_importante", False)
            ]
            quantite_totale = sum(d.get("quantite", 0) for d in demandes)

            # Analyse par produit
            produits_demandes = {}
            for demande in demandes:
                produit_id = demande.get("produit_id")
                if produit_id:
                    if produit_id not in produits_demandes:
                        produits_demandes[produit_id] = {
                            "count": 0,
                            "quantite_totale": 0,
                        }
                    produits_demandes[produit_id]["count"] += 1
                    produits_demandes[produit_id]["quantite_totale"] += demande.get(
                        "quantite", 0
                    )

            return {
                "success": True,
                "total_demandes": total_demandes,
                "demandes_importantes": len(demandes_importantes),
                "quantite_totale_demandee": quantite_totale,
                "produits_uniques": len(produits_demandes),
                "produits_les_plus_demandes": sorted(
                    produits_demandes.items(), key=lambda x: x[1]["count"], reverse=True
                )[:5],
            }

        except Exception as e:
            logger.error(f"Erreur calcul statistiques workflow: {e}")
            return {"success": False, "error": f"Erreur calcul statistiques: {str(e)}"}
