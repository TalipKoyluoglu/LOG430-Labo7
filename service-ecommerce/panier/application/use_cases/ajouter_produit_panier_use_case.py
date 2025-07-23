"""
Use Case: Ajouter un produit au panier
Fonctionnalité métier avec communications inter-services
"""

import uuid
import logging
from typing import Dict, Any

from ..repositories.panier_repository import PanierRepository
from ..services.catalogue_service import CatalogueService
from ..services.stock_service import StockService
from ...domain.entities import Panier
from ...domain.value_objects import ProduitPanier, QuantiteProduit, CommandeAjoutPanier
from ...domain.exceptions import (
    ProduitInexistantError,
    StockInsuffisantError,
    QuantiteInvalideError,
)

logger = logging.getLogger("panier")


class AjouterProduitPanierUseCase:
    """
    Use Case: Ajouter un produit au panier d'un client

    Logique métier avec vérifications:
    - Produit existe dans le catalogue
    - Produit est actif
    - Stock e-commerce suffisant
    - Quantité valide
    """

    def __init__(
        self,
        panier_repository: PanierRepository,
        catalogue_service: CatalogueService,
        stock_service: StockService,
    ):
        self._panier_repo = panier_repository
        self._catalogue_service = catalogue_service
        self._stock_service = stock_service

    def execute(
        self, client_id: uuid.UUID, commande_ajout: CommandeAjoutPanier
    ) -> Dict[str, Any]:
        """
        Ajoute un produit au panier du client

        Args:
            client_id: UUID du client
            commande_ajout: Commande d'ajout avec produit_id et quantité

        Returns:
            Dict contenant les informations du panier mis à jour

        Raises:
            ProduitInexistantError: Si le produit n'existe pas ou n'est pas actif
            StockInsuffisantError: Si le stock e-commerce est insuffisant
            QuantiteInvalideError: Si la quantité est invalide
        """

        logger.info(
            f"Ajout produit {commande_ajout.produit_id} au panier client {client_id}"
        )

        # 1. Vérifier que le produit existe et est actif (service-catalogue)
        try:
            produit_info = self._catalogue_service.obtenir_produit(
                commande_ajout.produit_id
            )
            if not produit_info.get("actif", False):
                raise ProduitInexistantError(
                    f"Produit {commande_ajout.produit_id} n'est pas actif"
                )
        except ProduitInexistantError:
            logger.warning(
                f"Tentative d'ajout d'un produit inexistant: {commande_ajout.produit_id}"
            )
            raise

        # 2. Récupérer ou créer le panier du client
        panier = self._panier_repo.get_by_client_id(client_id)
        if not panier:
            panier = Panier(id=uuid.uuid4(), client_id=client_id)

        # 3. Calculer la quantité totale après ajout
        produit_existant = panier.obtenir_produit(commande_ajout.produit_id)
        quantite_actuelle = produit_existant.quantite.valeur if produit_existant else 0
        quantite_totale = quantite_actuelle + commande_ajout.quantite.valeur

        # 4. Vérifier le stock e-commerce disponible (service-inventaire)
        if not self._stock_service.verifier_stock_disponible(
            commande_ajout.produit_id, quantite_totale
        ):
            stock_disponible = self._stock_service.obtenir_stock_disponible(
                commande_ajout.produit_id
            )
            logger.warning(
                f"Stock insuffisant pour produit {commande_ajout.produit_id}: "
                f"demandé {quantite_totale}, disponible {stock_disponible}"
            )
            raise StockInsuffisantError(
                f"Stock e-commerce insuffisant. Disponible: {stock_disponible}, "
                f"demandé: {quantite_totale}"
            )

        # 5. Créer le ProduitPanier et l'ajouter
        produit_panier = ProduitPanier(
            produit_id=commande_ajout.produit_id,
            nom_produit=produit_info["nom"],
            prix_unitaire=produit_info["prix"],
            quantite=commande_ajout.quantite,
        )

        panier.ajouter_produit(produit_panier)

        # 6. Sauvegarder le panier
        self._panier_repo.save(panier)

        logger.info(
            f"Produit {commande_ajout.produit_id} ajouté avec succès au panier {panier.id}"
        )

        # 7. Retourner les informations du panier
        return {
            "success": True,
            "panier_id": str(panier.id),
            "client_id": str(client_id),
            "produit_ajoute": {
                "produit_id": str(commande_ajout.produit_id),
                "nom_produit": produit_info["nom"],
                "quantite_ajoutee": commande_ajout.quantite.valeur,
                "prix_unitaire": float(produit_info["prix"]),
            },
            "panier_resume": {
                "nombre_articles": panier.nombre_articles(),
                "prix_total": float(panier.prix_total()),
                "nombre_produits_differents": len(panier.produits),
            },
        }
