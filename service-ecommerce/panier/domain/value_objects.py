"""
Value Objects du domaine Panier
Les value objects sont immuables et définissent des concepts métier
"""

import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import NewType


@dataclass(frozen=True)
class QuantiteProduit:
    """
    Value Object - Quantité d'un produit avec validation métier
    """

    valeur: int

    def __post_init__(self):
        if self.valeur < 0:
            raise ValueError("La quantité ne peut pas être négative")

        if self.valeur > 99:
            raise ValueError("La quantité maximum par produit est de 99")


@dataclass(frozen=True)
class ProduitPanier:
    """
    Value Object - Produit dans le panier avec ses informations
    """

    produit_id: uuid.UUID
    nom_produit: str
    prix_unitaire: Decimal
    quantite: QuantiteProduit

    def __post_init__(self):
        if not self.nom_produit or not self.nom_produit.strip():
            raise ValueError("Le nom du produit ne peut pas être vide")

        if self.prix_unitaire < Decimal("0"):
            raise ValueError("Le prix unitaire ne peut pas être négatif")

        # Normaliser le nom du produit
        object.__setattr__(self, "nom_produit", self.nom_produit.strip())

    def prix_total(self) -> Decimal:
        """Calcule le prix total pour cette ligne de panier"""
        return self.prix_unitaire * Decimal(str(self.quantite.valeur))

    def __str__(self):
        return f"{self.nom_produit} - Qté: {self.quantite.valeur} - Prix: {self.prix_unitaire}$"


@dataclass(frozen=True)
class CommandeAjoutPanier:
    """
    Value Object - Commande pour ajouter un produit au panier
    """

    produit_id: uuid.UUID
    quantite: QuantiteProduit

    def __post_init__(self):
        if self.quantite.valeur <= 0:
            raise ValueError("La quantité doit être positive pour ajouter au panier")
