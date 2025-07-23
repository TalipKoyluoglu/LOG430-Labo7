"""
Use Case: Modifier la quantité d'un produit dans le panier
Fonctionnalité de modification avec vérification stock
"""

import uuid
import logging
from typing import Dict, Any

from ..repositories.panier_repository import PanierRepository
from ..services.stock_service import StockService
from ...domain.value_objects import QuantiteProduit
from ...domain.exceptions import ProduitNonTrouveError, StockInsuffisantError

logger = logging.getLogger("panier")


class ModifierQuantitePanierUseCase:
    """
    Use Case: Modifier la quantité d'un produit dans le panier

    Vérifications:
    - Produit existe dans le panier
    - Nouvelle quantité respecte le stock disponible
    - Si quantité = 0, retire le produit
    """

    def __init__(
        self, panier_repository: PanierRepository, stock_service: StockService
    ):
        self._panier_repo = panier_repository
        self._stock_service = stock_service

    def execute(
        self, client_id: uuid.UUID, produit_id: uuid.UUID, nouvelle_quantite: int
    ) -> Dict[str, Any]:
        """
        Modifie la quantité d'un produit dans le panier

        Args:
            client_id: UUID du client
            produit_id: UUID du produit à modifier
            nouvelle_quantite: Nouvelle quantité (0 = retirer)

        Returns:
            Dict contenant les informations de la modification
        """

        logger.info(
            f"Modification quantité produit {produit_id} dans panier client {client_id}"
        )

        # Valider la quantité
        if nouvelle_quantite < 0:
            raise ValueError("La quantité ne peut pas être négative")

        # Récupérer le panier
        panier = self._panier_repo.get_by_client_id(client_id)
        if not panier:
            raise ProduitNonTrouveError("Aucun panier trouvé pour ce client")

        # Vérifier que le produit existe dans le panier
        produit_existant = panier.obtenir_produit(produit_id)
        if not produit_existant:
            raise ProduitNonTrouveError(
                f"Produit {produit_id} non trouvé dans le panier"
            )

        # Si quantité 0, retirer le produit
        if nouvelle_quantite == 0:
            panier.retirer_produit(produit_id)
            self._panier_repo.save(panier)

            logger.info(f"Produit {produit_id} retiré du panier {panier.id}")

            return {
                "success": True,
                "action": "removed",
                "produit_id": str(produit_id),
                "nom_produit": produit_existant.nom_produit,
                "ancienne_quantite": produit_existant.quantite.valeur,
                "nouvelle_quantite": 0,
                "panier_resume": {
                    "nombre_articles": panier.nombre_articles(),
                    "prix_total": float(panier.prix_total()),
                    "nombre_produits_differents": len(panier.produits),
                },
            }

        # Vérifier le stock pour la nouvelle quantité
        if not self._stock_service.verifier_stock_disponible(
            produit_id, nouvelle_quantite
        ):
            stock_disponible = self._stock_service.obtenir_stock_disponible(produit_id)
            raise StockInsuffisantError(
                f"Stock e-commerce insuffisant. Disponible: {stock_disponible}, "
                f"demandé: {nouvelle_quantite}"
            )

        # Modifier la quantité
        nouvelle_quantite_obj = QuantiteProduit(nouvelle_quantite)
        ancienne_quantite = produit_existant.quantite.valeur

        panier.modifier_quantite(produit_id, nouvelle_quantite_obj)
        self._panier_repo.save(panier)

        logger.info(
            f"Quantité produit {produit_id} modifiée: {ancienne_quantite} -> {nouvelle_quantite}"
        )

        return {
            "success": True,
            "action": "updated",
            "produit_id": str(produit_id),
            "nom_produit": produit_existant.nom_produit,
            "ancienne_quantite": ancienne_quantite,
            "nouvelle_quantite": nouvelle_quantite,
            "panier_resume": {
                "nombre_articles": panier.nombre_articles(),
                "prix_total": float(panier.prix_total()),
                "nombre_produits_differents": len(panier.produits),
            },
        }
