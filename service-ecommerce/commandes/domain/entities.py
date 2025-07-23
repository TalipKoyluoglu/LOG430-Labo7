"""
Entités du domaine Check-out E-commerce
Les entités contiennent l'identité et la logique métier
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict
from decimal import Decimal

from .value_objects import (
    CommandeEcommerce as CommandeEcommerceVO,
    LigneCommande,
    StatutCheckout,
    AdresseLivraison,
)
from .exceptions import CheckoutInvalideError, PanierVideError, StockInsuffisantError


class ProcessusCheckout:
    """
    Entité Aggregate Root - Processus de validation de commande e-commerce
    Orchestre toute la logique métier du check-out
    """

    def __init__(
        self,
        id: uuid.UUID,
        client_id: uuid.UUID,
        panier_id: uuid.UUID,
        date_creation: Optional[datetime] = None,
    ):
        self._id = id
        self._client_id = client_id
        self._panier_id = panier_id
        self._date_creation = date_creation or datetime.now()
        self._statut = StatutCheckout.INITIALISE
        self._lignes_commande: List[LigneCommande] = []
        self._adresse_livraison: Optional[AdresseLivraison] = None
        self._sous_total = Decimal("0.00")
        self._frais_livraison = Decimal("0.00")
        self._total = Decimal("0.00")
        self._commande_externe_id: Optional[uuid.UUID] = None
        self._erreurs: List[str] = []
        self._date_finalisation: Optional[datetime] = None

    @property
    def id(self) -> uuid.UUID:
        return self._id

    @property
    def client_id(self) -> uuid.UUID:
        return self._client_id

    @property
    def panier_id(self) -> uuid.UUID:
        return self._panier_id

    @property
    def statut(self) -> StatutCheckout:
        return self._statut

    @property
    def lignes_commande(self) -> List[LigneCommande]:
        return self._lignes_commande.copy()

    @property
    def adresse_livraison(self) -> Optional[AdresseLivraison]:
        return self._adresse_livraison

    @property
    def sous_total(self) -> Decimal:
        return self._sous_total

    @property
    def frais_livraison(self) -> Decimal:
        return self._frais_livraison

    @property
    def total(self) -> Decimal:
        return self._total

    @property
    def commande_externe_id(self) -> Optional[uuid.UUID]:
        return self._commande_externe_id

    @property
    def erreurs(self) -> List[str]:
        return self._erreurs.copy()

    @property
    def date_creation(self) -> datetime:
        return self._date_creation

    @property
    def date_finalisation(self) -> Optional[datetime]:
        return self._date_finalisation

    def valider_panier(self, lignes_panier: List[Dict]) -> None:
        """
        Valide et convertit les lignes du panier en lignes de commande
        """
        if not lignes_panier:
            self._erreurs.append("Le panier est vide")
            self._statut = StatutCheckout.ECHEC
            raise PanierVideError(
                "Impossible de procéder au check-out avec un panier vide"
            )

        self._lignes_commande.clear()
        self._sous_total = Decimal("0.00")

        for ligne_panier in lignes_panier:
            ligne_commande = LigneCommande(
                produit_id=uuid.UUID(ligne_panier["produit_id"]),
                nom_produit=ligne_panier["nom_produit"],
                quantite=ligne_panier["quantite"],
                prix_unitaire=Decimal(str(ligne_panier["prix_unitaire"])),
            )
            self._lignes_commande.append(ligne_commande)
            self._sous_total += ligne_commande.prix_total()

        self._statut = StatutCheckout.PANIER_VALIDE

    def definir_adresse_livraison(self, adresse: AdresseLivraison) -> None:
        """
        Définit l'adresse de livraison et calcule les frais
        """
        self._adresse_livraison = adresse
        self._calculer_frais_livraison()
        self._statut = StatutCheckout.ADRESSE_DEFINIE

    def valider_stocks(self, stocks_disponibles: Dict[uuid.UUID, int]) -> None:
        """
        Valide que tous les produits sont disponibles en stock
        """
        stocks_insuffisants = []

        for ligne in self._lignes_commande:
            stock_disponible = stocks_disponibles.get(ligne.produit_id, 0)
            if stock_disponible < ligne.quantite:
                stocks_insuffisants.append(
                    {
                        "produit_id": ligne.produit_id,
                        "nom_produit": ligne.nom_produit,
                        "quantite_demandee": ligne.quantite,
                        "stock_disponible": stock_disponible,
                    }
                )

        if stocks_insuffisants:
            for stock in stocks_insuffisants:
                self._erreurs.append(
                    f"Stock insuffisant pour {stock['nom_produit']}: "
                    f"demandé {stock['quantite_demandee']}, disponible {stock['stock_disponible']}"
                )
            self._statut = StatutCheckout.ECHEC
            raise StockInsuffisantError(
                "Stocks insuffisants pour certains produits", stocks_insuffisants
            )

        self._statut = StatutCheckout.STOCKS_VALIDES

    def finaliser_commande(self, commande_externe_id: uuid.UUID) -> None:
        """
        Finalise le processus de check-out avec l'ID de la commande créée
        """
        if self._statut != StatutCheckout.STOCKS_VALIDES:
            raise CheckoutInvalideError(
                f"Impossible de finaliser: statut actuel {self._statut.value}"
            )

        self._commande_externe_id = commande_externe_id
        self._date_finalisation = datetime.now()
        self._statut = StatutCheckout.FINALISE

    def marquer_echec(self, erreur: str) -> None:
        """
        Marque le processus comme échoué avec une erreur
        """
        self._erreurs.append(erreur)
        self._statut = StatutCheckout.ECHEC

    def peut_etre_finalise(self) -> bool:
        """
        Vérifie si le processus peut être finalisé
        """
        return (
            self._statut == StatutCheckout.STOCKS_VALIDES
            and self._adresse_livraison is not None
            and len(self._lignes_commande) > 0
            and len(self._erreurs) == 0
        )

    def obtenir_resume(self) -> Dict:
        """
        Retourne un résumé complet du processus de check-out
        """
        return {
            "checkout_id": str(self._id),
            "client_id": str(self._client_id),
            "panier_id": str(self._panier_id),
            "statut": self._statut.value,
            "date_creation": self._date_creation.isoformat(),
            "date_finalisation": (
                self._date_finalisation.isoformat() if self._date_finalisation else None
            ),
            "adresse_livraison": (
                self._adresse_livraison.to_dict() if self._adresse_livraison else None
            ),
            "commande_externe_id": (
                str(self._commande_externe_id) if self._commande_externe_id else None
            ),
            "lignes_commande": [
                {
                    "produit_id": str(ligne.produit_id),
                    "nom_produit": ligne.nom_produit,
                    "quantite": ligne.quantite,
                    "prix_unitaire": float(ligne.prix_unitaire),
                    "prix_total": float(ligne.prix_total()),
                }
                for ligne in self._lignes_commande
            ],
            "calculs": {
                "sous_total": float(self._sous_total),
                "frais_livraison": float(self._frais_livraison),
                "total": float(self._total),
                "nombre_articles": sum(
                    ligne.quantite for ligne in self._lignes_commande
                ),
                "nombre_produits": len(self._lignes_commande),
            },
            "erreurs": self._erreurs,
        }

    def _calculer_frais_livraison(self) -> None:
        """
        Calcule les frais de livraison selon la logique métier
        """
        if self._sous_total >= Decimal("100.00"):
            # Livraison gratuite si commande >= 100€
            self._frais_livraison = Decimal("0.00")
        elif (
            self._adresse_livraison and self._adresse_livraison.est_livraison_express()
        ):
            # Livraison express
            self._frais_livraison = Decimal("15.00")
        else:
            # Livraison standard
            self._frais_livraison = Decimal("7.50")

        self._total = self._sous_total + self._frais_livraison

    def __str__(self):
        return f"Checkout {self._id} - Client {self._client_id} - Statut {self._statut.value}"


class CommandeEcommerce:
    """
    Entité - Commande e-commerce finalisée et persistée
    Représente une commande validée avec toutes ses informations
    """

    def __init__(
        self,
        id: uuid.UUID,
        client_id: uuid.UUID,
        checkout_id: uuid.UUID,
        statut: str = "validee",
        date_commande: Optional[datetime] = None,
    ):
        self._id = id
        self._client_id = client_id
        self._checkout_id = checkout_id
        self._statut = statut
        self._date_commande = date_commande or datetime.now()
        self._date_modification = datetime.now()

        # Calculs financiers
        self._sous_total = Decimal("0.00")
        self._frais_livraison = Decimal("0.00")
        self._total = Decimal("0.00")

        # Adresse de livraison
        self._adresse_livraison: Optional[AdresseLivraison] = None

        # Lignes de commande
        self._lignes: List[LigneCommande] = []

        # Métadonnées
        self._notes: Optional[str] = None
        self._nombre_articles = 0
        self._nombre_produits = 0

    @property
    def id(self) -> uuid.UUID:
        return self._id

    @property
    def client_id(self) -> uuid.UUID:
        return self._client_id

    @property
    def checkout_id(self) -> uuid.UUID:
        return self._checkout_id

    @property
    def statut(self) -> str:
        return self._statut

    @property
    def date_commande(self) -> datetime:
        return self._date_commande

    @property
    def date_modification(self) -> datetime:
        return self._date_modification

    @property
    def sous_total(self) -> Decimal:
        return self._sous_total

    @property
    def frais_livraison(self) -> Decimal:
        return self._frais_livraison

    @property
    def total(self) -> Decimal:
        return self._total

    @property
    def adresse_livraison(self) -> Optional[AdresseLivraison]:
        return self._adresse_livraison

    @property
    def lignes(self) -> List[LigneCommande]:
        return self._lignes.copy()

    @property
    def notes(self) -> Optional[str]:
        return self._notes

    @property
    def nombre_articles(self) -> int:
        return self._nombre_articles

    @property
    def nombre_produits(self) -> int:
        return self._nombre_produits

    def definir_details_financiers(
        self, sous_total: Decimal, frais_livraison: Decimal
    ) -> None:
        """Définit les montants de la commande"""
        self._sous_total = sous_total
        self._frais_livraison = frais_livraison
        self._total = sous_total + frais_livraison
        self._date_modification = datetime.now()

    def definir_adresse_livraison(self, adresse: AdresseLivraison) -> None:
        """Définit l'adresse de livraison"""
        self._adresse_livraison = adresse
        self._date_modification = datetime.now()

    def ajouter_ligne(self, ligne: LigneCommande) -> None:
        """Ajoute une ligne à la commande"""
        self._lignes.append(ligne)
        self._recalculer_statistiques()

    def definir_notes(self, notes: str) -> None:
        """Définit les notes de la commande"""
        self._notes = notes
        self._date_modification = datetime.now()

    def changer_statut(self, nouveau_statut: str) -> None:
        """Change le statut de la commande"""
        self._statut = nouveau_statut
        self._date_modification = datetime.now()

    def _recalculer_statistiques(self) -> None:
        """Recalcule les statistiques de la commande"""
        self._nombre_articles = sum(ligne.quantite for ligne in self._lignes)
        self._nombre_produits = len(self._lignes)

    def to_dict(self) -> Dict:
        """Convertit la commande en dictionnaire"""
        return {
            "id": str(self._id),
            "client_id": str(self._client_id),
            "checkout_id": str(self._checkout_id),
            "statut": self._statut,
            "date_commande": self._date_commande.isoformat(),
            "date_modification": self._date_modification.isoformat(),
            "sous_total": float(self._sous_total),
            "frais_livraison": float(self._frais_livraison),
            "total": float(self._total),
            "adresse_livraison": (
                self._adresse_livraison.to_dict() if self._adresse_livraison else None
            ),
            "lignes": [
                {
                    "produit_id": str(ligne.produit_id),
                    "nom_produit": ligne.nom_produit,
                    "quantite": ligne.quantite,
                    "prix_unitaire": float(ligne.prix_unitaire),
                    "prix_total": float(ligne.prix_total()),
                }
                for ligne in self._lignes
            ],
            "notes": self._notes,
            "nombre_articles": self._nombre_articles,
            "nombre_produits": self._nombre_produits,
        }

    def __str__(self):
        return f"CommandeEcommerce {self._id} - Client {self._client_id} - {self._total}€ - {self._statut}"
