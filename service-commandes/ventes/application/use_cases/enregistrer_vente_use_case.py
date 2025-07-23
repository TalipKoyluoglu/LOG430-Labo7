"""
Use Case: Enregistrer une Vente
Fonctionnalité métier complète pour créer une nouvelle vente
"""

import uuid
from decimal import Decimal
from typing import Dict, Any

from ..repositories.vente_repository import VenteRepository
from ..repositories.magasin_repository import MagasinRepository
from ..services.produit_service import ProduitService
from ..services.stock_service import StockService
from ...domain.entities import Vente, Magasin
from ...domain.value_objects import CommandeVente, ProduitId, MagasinId, ClientId
from ...domain.exceptions import (
    MagasinInexistantError,
    ProduitInexistantError,
    StockInsuffisantError,
)


class EnregistrerVenteUseCase:
    """
    Use Case: Enregistrer une nouvelle vente

    Orchestration complète de la fonctionnalité métier:
    1. Validation du magasin
    2. Récupération des infos produit
    3. Vérification du stock
    4. Création de la vente (entité riche)
    5. Mise à jour du stock
    6. Persistance
    """

    def __init__(
        self,
        vente_repository: VenteRepository,
        magasin_repository: MagasinRepository,
        produit_service: ProduitService,
        stock_service: StockService,
    ):
        self._vente_repo = vente_repository
        self._magasin_repo = magasin_repository
        self._produit_service = produit_service
        self._stock_service = stock_service

    def execute(self, commande: CommandeVente) -> Dict[str, Any]:
        """
        Exécute le cas d'usage d'enregistrement de vente

        Args:
            commande: CommandeVente contenant les détails de la vente

        Returns:
            Dict contenant les détails de la vente créée

        Raises:
            MagasinInexistantError: Si le magasin n'existe pas
            ProduitInexistantError: Si le produit n'existe pas
            StockInsuffisantError: Si le stock est insuffisant
        """

        # 1. Validation du magasin (règle métier)
        magasin = self._magasin_repo.get_by_id(commande.magasin_id)
        if not magasin:
            raise MagasinInexistantError(f"Magasin {commande.magasin_id} non trouvé")

        # 2. Récupération des informations produit
        produit_info = self._produit_service.get_produit_details(commande.produit_id)
        if not produit_info:
            raise ProduitInexistantError(f"Produit {commande.produit_id} non trouvé")

        # 3. Vérification du stock (règle métier déléguée au magasin)
        stock_info = self._stock_service.get_stock_local(
            commande.magasin_id, commande.produit_id
        )
        if not magasin.peut_vendre(
            commande.produit_id, commande.quantite, stock_info.quantite_disponible
        ):
            raise StockInsuffisantError(
                str(commande.produit_id),
                commande.quantite,
                stock_info.quantite_disponible,
            )

        # 4. Création de la vente (entité riche avec logique métier)
        vente_id = uuid.uuid4()
        vente = Vente(
            id=vente_id, magasin_id=commande.magasin_id, client_id=commande.client_id
        )

        # Ajouter la ligne de vente (logique métier dans l'entité)
        vente.ajouter_ligne(
            produit_id=commande.produit_id,
            quantite=commande.quantite,
            prix_unitaire=produit_info.prix,
        )

        # 5. Mise à jour du stock (effet de bord)
        self._stock_service.decrease_stock(
            commande.magasin_id, commande.produit_id, commande.quantite
        )

        # 6. Persistance de la vente
        self._vente_repo.save(vente)

        # 7. Retour des données pour la réponse API
        return {
            "success": True,
            "vente": {
                "id": str(vente.id),
                "magasin": magasin.nom,
                "date_vente": vente.date_vente.isoformat(),
                "total": float(vente.calculer_total()),
                "client_id": str(vente.client_id) if vente.client_id else None,
                "statut": vente.statut.value,
                "lignes": [
                    {
                        "produit_id": str(ligne.produit_id),
                        "produit_nom": produit_info.nom,
                        "quantite": ligne.quantite,
                        "prix_unitaire": float(ligne.prix_unitaire),
                        "sous_total": float(ligne.sous_total),
                    }
                    for ligne in vente.lignes
                ],
            },
        }
