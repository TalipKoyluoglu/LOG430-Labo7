"""
Entités du domaine Panier E-commerce
Les entités contiennent l'identité et la logique métier
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict
from decimal import Decimal

from .value_objects import ProduitPanier, QuantiteProduit
from .exceptions import PanierVideError, ProduitNonTrouveError, QuantiteInvalideError


class Panier:
    """
    Entité Aggregate Root - Panier d'achat
    Contient toute la logique métier liée au panier e-commerce
    """

    def __init__(
        self,
        id: uuid.UUID,
        client_id: uuid.UUID,
        date_creation: Optional[datetime] = None,
    ):
        self._id = id
        self._client_id = client_id
        self._produits: List[ProduitPanier] = []
        self._date_creation = date_creation or datetime.now()
        self._date_modification = datetime.now()

    @property
    def id(self) -> uuid.UUID:
        return self._id

    @property
    def client_id(self) -> uuid.UUID:
        return self._client_id

    @property
    def produits(self) -> List[ProduitPanier]:
        return self._produits.copy()  # Retourner une copie pour l'immutabilité

    @property
    def date_creation(self) -> datetime:
        return self._date_creation

    @property
    def date_modification(self) -> datetime:
        return self._date_modification

    def ajouter_produit(self, produit_panier: ProduitPanier) -> None:
        """
        Ajoute un produit au panier ou augmente sa quantité s'il existe déjà
        """
        # Vérifier si le produit existe déjà
        for i, produit_existant in enumerate(self._produits):
            if produit_existant.produit_id == produit_panier.produit_id:
                # Augmenter la quantité
                nouvelle_quantite = QuantiteProduit(
                    produit_existant.quantite.valeur + produit_panier.quantite.valeur
                )
                # Remplacer par un nouveau ProduitPanier avec la nouvelle quantité
                self._produits[i] = ProduitPanier(
                    produit_id=produit_existant.produit_id,
                    nom_produit=produit_existant.nom_produit,
                    prix_unitaire=produit_existant.prix_unitaire,
                    quantite=nouvelle_quantite,
                )
                self._date_modification = datetime.now()
                return

        # Produit non trouvé, l'ajouter
        self._produits.append(produit_panier)
        self._date_modification = datetime.now()

    def retirer_produit(self, produit_id: uuid.UUID) -> None:
        """
        Retire complètement un produit du panier
        """
        for i, produit in enumerate(self._produits):
            if produit.produit_id == produit_id:
                self._produits.pop(i)
                self._date_modification = datetime.now()
                return

        raise ProduitNonTrouveError(f"Produit {produit_id} non trouvé dans le panier")

    def modifier_quantite(
        self, produit_id: uuid.UUID, nouvelle_quantite: QuantiteProduit
    ) -> None:
        """
        Modifie la quantité d'un produit dans le panier
        """
        if nouvelle_quantite.valeur <= 0:
            self.retirer_produit(produit_id)
            return

        for i, produit in enumerate(self._produits):
            if produit.produit_id == produit_id:
                # Remplacer par un nouveau ProduitPanier avec la nouvelle quantité
                self._produits[i] = ProduitPanier(
                    produit_id=produit.produit_id,
                    nom_produit=produit.nom_produit,
                    prix_unitaire=produit.prix_unitaire,
                    quantite=nouvelle_quantite,
                )
                self._date_modification = datetime.now()
                return

        raise ProduitNonTrouveError(f"Produit {produit_id} non trouvé dans le panier")

    def vider(self) -> None:
        """
        Vide complètement le panier
        """
        self._produits.clear()
        self._date_modification = datetime.now()

    def est_vide(self) -> bool:
        """
        Vérifie si le panier est vide
        """
        return len(self._produits) == 0

    def nombre_articles(self) -> int:
        """
        Retourne le nombre total d'articles dans le panier
        """
        return sum(produit.quantite.valeur for produit in self._produits)

    def prix_total(self) -> Decimal:
        """
        Calcule le prix total du panier
        """
        if not self._produits:
            return Decimal("0")
        return sum(produit.prix_total() for produit in self._produits)

    def obtenir_produit(self, produit_id: uuid.UUID) -> Optional[ProduitPanier]:
        """
        Récupère un produit spécifique du panier
        """
        for produit in self._produits:
            if produit.produit_id == produit_id:
                return produit
        return None

    def valider_pour_commande(self) -> Dict[str, any]:
        """
        Valide que le panier peut être transformé en commande
        """
        if self.est_vide():
            raise PanierVideError("Impossible de passer commande avec un panier vide")

        return {
            "panier_id": str(self._id),
            "client_id": str(self._client_id),
            "nombre_articles": self.nombre_articles(),
            "prix_total": float(self.prix_total()),
            "produits": [
                {
                    "produit_id": str(p.produit_id),
                    "nom_produit": p.nom_produit,
                    "quantite": p.quantite.valeur,
                    "prix_unitaire": float(p.prix_unitaire),
                    "prix_total": float(p.prix_total()),
                }
                for p in self._produits
            ],
        }

    def __str__(self):
        return f"Panier {self._id} - Client {self._client_id} - {self.nombre_articles()} articles"
