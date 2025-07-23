"""
Use Case: Vider le panier d'un client
Fonctionnalité de remise à zéro du panier
"""

import uuid
import logging
from typing import Dict, Any

from ..repositories.panier_repository import PanierRepository
from ...domain.exceptions import PanierVideError

logger = logging.getLogger("panier")


class ViderPanierUseCase:
    """
    Use Case: Vider complètement le panier d'un client

    Retire tous les produits du panier
    """

    def __init__(self, panier_repository: PanierRepository):
        self._panier_repo = panier_repository

    def execute(self, client_id: uuid.UUID) -> Dict[str, Any]:
        """
        Vide complètement le panier du client

        Args:
            client_id: UUID du client

        Returns:
            Dict contenant les informations de l'opération
        """

        logger.info(f"Vidage panier pour client {client_id}")

        # Récupérer le panier
        panier = self._panier_repo.get_by_client_id(client_id)

        if not panier or panier.est_vide():
            logger.debug(f"Panier déjà vide pour client {client_id}")
            return {
                "success": True,
                "message": "Panier déjà vide",
                "client_id": str(client_id),
                "articles_supprimes": 0,
                "panier_resume": {
                    "nombre_articles": 0,
                    "prix_total": 0.0,
                    "nombre_produits_differents": 0,
                },
            }

        # Sauvegarder les statistiques avant vidage
        articles_avant = panier.nombre_articles()
        produits_avant = len(panier.produits)
        prix_avant = panier.prix_total()

        # Vider le panier
        panier.vider()
        self._panier_repo.save(panier)

        logger.info(f"Panier {panier.id} vidé: {articles_avant} articles supprimés")

        return {
            "success": True,
            "message": "Panier vidé avec succès",
            "client_id": str(client_id),
            "panier_id": str(panier.id),
            "articles_supprimes": articles_avant,
            "produits_supprimes": produits_avant,
            "valeur_supprimee": float(prix_avant),
            "panier_resume": {
                "nombre_articles": panier.nombre_articles(),
                "prix_total": float(panier.prix_total()),
                "nombre_produits_differents": len(panier.produits),
            },
        }
