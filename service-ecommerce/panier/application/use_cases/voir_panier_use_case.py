"""
Use Case: Voir le contenu du panier
Fonctionnalité de consultation du panier client
"""

import uuid
import logging
from typing import Dict, Any, Optional

from ..repositories.panier_repository import PanierRepository
from ...domain.exceptions import PanierVideError

logger = logging.getLogger("panier")


class VoirPanierUseCase:
    """
    Use Case: Consulter le contenu du panier d'un client

    Affiche tous les produits, quantités, prix et totaux
    """

    def __init__(self, panier_repository: PanierRepository):
        self._panier_repo = panier_repository

    def execute(self, client_id: uuid.UUID) -> Dict[str, Any]:
        """
        Récupère et formate le contenu du panier d'un client

        Args:
            client_id: UUID du client

        Returns:
            Dict contenant le contenu détaillé du panier
        """

        logger.debug(f"Consultation panier pour client {client_id}")

        # Récupérer le panier du client
        panier = self._panier_repo.get_by_client_id(client_id)

        if not panier or panier.est_vide():
            logger.debug(f"Panier vide ou inexistant pour client {client_id}")
            return {
                "panier_existe": False,
                "est_vide": True,
                "panier_id": None,
                "client_id": str(client_id),
                "produits": [],
                "resume": {
                    "nombre_articles": 0,
                    "prix_total": 0.0,
                    "nombre_produits_differents": 0,
                },
            }

        # Formater les produits du panier
        produits_detail = []
        for produit in panier.produits:
            produits_detail.append(
                {
                    "produit_id": str(produit.produit_id),
                    "nom_produit": produit.nom_produit,
                    "prix_unitaire": float(produit.prix_unitaire),
                    "quantite": produit.quantite.valeur,
                    "prix_ligne": float(produit.prix_total()),
                }
            )

        logger.debug(
            f"Panier {panier.id} consulté: {len(produits_detail)} produits différents"
        )

        return {
            "panier_existe": True,
            "est_vide": False,
            "panier_id": str(panier.id),
            "client_id": str(client_id),
            "date_creation": panier.date_creation.isoformat(),
            "date_modification": panier.date_modification.isoformat(),
            "produits": produits_detail,
            "resume": {
                "nombre_articles": panier.nombre_articles(),
                "prix_total": float(panier.prix_total()),
                "nombre_produits_differents": len(panier.produits),
            },
        }
