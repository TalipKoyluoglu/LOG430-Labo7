"""
Use Case principal pour le check-out e-commerce
Orchestration complète du processus de commande avec validation panier et décrémentation stocks
"""

import uuid
import logging
from decimal import Decimal
from datetime import datetime
from typing import Dict, Any

from ..services.panier_service import PanierService
from ..services.stock_service import StockService
from ..repositories.commande_ecommerce_repository import CommandeEcommerceRepository
from ...infrastructure.django_commande_ecommerce_repository import (
    DjangoCommandeEcommerceRepository,
)
from ...domain.value_objects import (
    DemandeCheckout,
    CommandeEcommerce as CommandeEcommerceVO,
    LigneCommande,
    AdresseLivraison,
)
from ...domain.entities import CommandeEcommerce as CommandeEcommerceDomain
from ...domain.exceptions import (
    CheckoutError,
    PanierVideError,
    StockInsuffisantError,
    AdresseInvalideError,
    ServiceExterneIndisponibleError,
)

logger = logging.getLogger("commandes")


class CheckoutEcommerceUseCase:
    """
    Use Case principal pour le check-out e-commerce

    Workflow complet :
    1. Validation du client (simple vérification UUID)
    2. Récupération et validation du panier
    3. Vérification des stocks centraux
    4. Calcul des frais de livraison
    5. Décrémentation des stocks
    6. Vidage du panier
    7. Retour des détails de commande
    """

    def __init__(self):
        self.panier_service = PanierService()
        self.stock_service = StockService()
        self.commande_repository = DjangoCommandeEcommerceRepository()

    def execute(self, demande_checkout: DemandeCheckout) -> Dict[str, Any]:
        """
        Exécute le processus complet de check-out e-commerce

        Args:
            demande_checkout: Value Object contenant tous les détails du checkout

        Returns:
            Dict avec les détails de la commande créée

        Raises:
            CheckoutError: Si le checkout échoue à une étape
        """
        checkout_id = uuid.uuid4()
        client_id = str(demande_checkout.client_id)

        logger.info(f"Début checkout {checkout_id} pour client {client_id}")

        try:
            # 1. Validation et récupération du panier
            panier_validation = self._valider_panier(client_id)
            if not panier_validation["valide"]:
                raise PanierVideError(panier_validation["details"])

            panier_info = panier_validation["panier"]

            # 2. Vérification des stocks centraux
            stock_validation = self._verifier_stocks_centraux(panier_info)
            if not stock_validation["tous_suffisants"]:
                raise StockInsuffisantError(
                    f"Stocks insuffisants pour {stock_validation['resume']['produits_ko']} produits",
                    stock_validation.get("stocks_insuffisants", []),
                )

            # 3. Calcul des frais de livraison
            sous_total = Decimal(str(panier_info["total"]))
            frais_livraison = self._calculer_frais_livraison(
                sous_total, demande_checkout.adresse_livraison.livraison_express
            )
            total = sous_total + frais_livraison

            # 4. Décrémentation des stocks (action critique)
            self._decrémenter_stocks_centraux(panier_info)

            # 5. Vidage du panier après succès
            vidage_result = self.panier_service.vider_panier_apres_commande(client_id)
            if not vidage_result["success"]:
                logger.warning(
                    f"Échec vidage panier {client_id}: {vidage_result.get('error')}"
                )

            # 6. Construction de la commande finale
            commande_id = uuid.uuid4()
            commande_data = self._construire_commande_finale(
                commande_id=commande_id,
                checkout_id=checkout_id,
                client_id=client_id,
                panier_info=panier_info,
                adresse_livraison=demande_checkout.adresse_livraison,
                sous_total=sous_total,
                frais_livraison=frais_livraison,
                total=total,
                notes=demande_checkout.notes or "",
            )

            logger.info(
                f"Checkout {checkout_id} terminé avec succès - Commande {commande_id}"
            )

            return commande_data

        except (PanierVideError, StockInsuffisantError, AdresseInvalideError) as e:
            logger.error(f"Échec checkout {checkout_id}: {str(e)}")
            raise CheckoutError(f"Échec checkout: {str(e)}")

        except Exception as e:
            logger.error(f"Erreur inattendue checkout {checkout_id}: {str(e)}")
            raise CheckoutError(f"Erreur lors du checkout: {str(e)}")

    def _valider_panier(self, client_id: str) -> Dict[str, Any]:
        """Valide que le panier existe et n'est pas vide"""
        return self.panier_service.valider_panier_pour_checkout(client_id)

    def _verifier_stocks_centraux(self, panier_info: Dict[str, Any]) -> Dict[str, Any]:
        """Vérifie que tous les produits du panier ont un stock suffisant"""
        produits_panier = self.panier_service.obtenir_produits_pour_stock(
            panier_info["client_id"]
        )
        return self.stock_service.valider_stocks_suffisants(produits_panier)

    def _calculer_frais_livraison(
        self, sous_total: Decimal, livraison_express: bool
    ) -> Decimal:
        """
        Calcule les frais de livraison selon la logique métier e-commerce
        """
        if sous_total >= Decimal("100.00"):
            # Livraison gratuite pour commandes ≥ 100€
            return Decimal("0.00")
        elif livraison_express:
            # Livraison express
            return Decimal("15.00")
        else:
            # Livraison standard
            return Decimal("7.50")

    def _decrémenter_stocks_centraux(self, panier_info: Dict[str, Any]) -> None:
        """
        Décrémente les stocks centraux pour tous les produits du panier
        """
        for produit in panier_info["produits"]:
            produit_id = produit["produit_id"]
            quantite = produit["quantite"]

            result = self.stock_service.diminuer_stock_central(produit_id, quantite)

            if not result["success"]:
                error_msg = (
                    f"Échec décrémentation stock {produit_id}: {result.get('error')}"
                )
                logger.error(error_msg)
                raise ServiceExterneIndisponibleError("inventaire", error_msg)

            logger.info(
                f"Stock décrementé: {produit['nom_produit']} -{quantite} = {result['nouvelle_quantite']}"
            )

    def _construire_commande_finale(
        self,
        commande_id: uuid.UUID,
        checkout_id: uuid.UUID,
        client_id: str,
        panier_info: Dict[str, Any],
        adresse_livraison: AdresseLivraison,
        sous_total: Decimal,
        frais_livraison: Decimal,
        total: Decimal,
        notes: str = "",
    ) -> Dict[str, Any]:
        """
        Construit la réponse finale avec toutes les informations de commande
        ET sauvegarde la commande en base de données
        """
        # Créer l'entité commande e-commerce
        commande_domaine = CommandeEcommerceDomain(
            id=commande_id,
            client_id=uuid.UUID(client_id),
            checkout_id=checkout_id,
            statut="validee",
        )

        # Définir les détails financiers
        commande_domaine.definir_details_financiers(sous_total, frais_livraison)

        # Définir l'adresse de livraison
        commande_domaine.definir_adresse_livraison(adresse_livraison)

        # Ajouter les lignes de commande
        for produit in panier_info["produits"]:
            ligne = LigneCommande(
                produit_id=uuid.UUID(produit["produit_id"]),
                nom_produit=produit["nom_produit"],
                quantite=produit["quantite"],
                prix_unitaire=Decimal(str(produit["prix_unitaire"])),
            )
            commande_domaine.ajouter_ligne(ligne)

        # Définir les notes
        if notes:
            commande_domaine.definir_notes(notes)

        # Sauvegarder la commande en base de données
        commande_sauvee = self.commande_repository.save(commande_domaine)

        logger.info(f"Commande {commande_id} sauvegardée pour client {client_id}")

        return {
            "success": True,
            "checkout_id": str(checkout_id),
            "commande_id": str(commande_id),
            "statut": "finalise",
            "message": "Check-out terminé avec succès",
            "timestamp": datetime.now().isoformat(),
            "commande": {
                "client_id": client_id,
                "total": float(total),
                "sous_total": float(sous_total),
                "frais_livraison": float(frais_livraison),
                "livraison_gratuite": frais_livraison == Decimal("0.00"),
                "adresse_livraison": {
                    "nom_destinataire": adresse_livraison.nom_destinataire,
                    "adresse_complete": adresse_livraison.adresse_complete(),
                    "livraison_express": adresse_livraison.livraison_express,
                    "instructions": adresse_livraison.instructions_livraison,
                },
                "nombre_articles": panier_info["nombre_articles"],
                "nombre_produits": panier_info["nombre_produits"],
                "notes": notes,
            },
            "produits": [
                {
                    "produit_id": produit["produit_id"],
                    "nom_produit": produit["nom_produit"],
                    "quantite": produit["quantite"],
                    "prix_unitaire": produit["prix_unitaire"],
                    "prix_total": produit["prix_total"],
                }
                for produit in panier_info["produits"]
            ],
            "operations": {
                "panier_vide": True,
                "stocks_decremente": True,
                "commande_creee": True,
                "commande_sauvee": True,
            },
        }
