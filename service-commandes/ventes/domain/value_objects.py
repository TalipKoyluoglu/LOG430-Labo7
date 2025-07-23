"""
Value Objects du domaine Ventes
Les value objects sont immuables et définissent des concepts métier
"""

import uuid
from enum import Enum
from decimal import Decimal
from dataclasses import dataclass
from typing import NewType, Optional


# Type Aliases pour la sécurité des types
ProduitId = NewType("ProduitId", uuid.UUID)
MagasinId = NewType("MagasinId", uuid.UUID)
ClientId = NewType("ClientId", uuid.UUID)


class StatutVente(Enum):
    """
    Enumération des statuts de vente (concept métier)
    """

    ACTIVE = "active"
    ANNULEE = "annulee"
    REMBOURSEE = "remboursee"


class StatutCommande(Enum):
    """
    Enumération des statuts de commande e-commerce (concept métier)
    """

    EN_ATTENTE = "en_attente"
    VALIDEE = "validee"
    PAYEE = "payee"
    EXPEDIEE = "expediee"
    LIVREE = "livree"
    ANNULEE = "annulee"


@dataclass(frozen=True)
class LigneVenteVO:
    """
    Value Object - Ligne de vente
    Immuable et contient la logique de calcul
    """

    id: uuid.UUID
    produit_id: ProduitId
    quantite: int
    prix_unitaire: Decimal

    def __post_init__(self):
        if self.quantite <= 0:
            raise ValueError("La quantité doit être positive")
        if self.prix_unitaire <= 0:
            raise ValueError("Le prix unitaire doit être positif")

    @property
    def sous_total(self) -> Decimal:
        """
        Calcule le sous-total de la ligne (logique métier)
        """
        return self.quantite * self.prix_unitaire


@dataclass(frozen=True)
class ProduitInfo:
    """
    Value Object - Informations produit
    """

    id: ProduitId
    nom: str
    prix: Decimal

    def __post_init__(self):
        if not self.nom.strip():
            raise ValueError("Le nom du produit ne peut pas être vide")
        if self.prix <= 0:
            raise ValueError("Le prix doit être positif")


@dataclass(frozen=True)
class StockInfo:
    """
    Value Object - Informations de stock
    """

    produit_id: ProduitId
    magasin_id: MagasinId
    quantite_disponible: int

    def est_suffisant_pour(self, quantite_demandee: int) -> bool:
        """
        Vérifie si le stock est suffisant (logique métier)
        """
        return self.quantite_disponible >= quantite_demandee

    def quantite_manquante(self, quantite_demandee: int) -> int:
        """
        Calcule la quantité manquante
        """
        return max(0, quantite_demandee - self.quantite_disponible)


@dataclass(frozen=True)
class CommandeVente:
    """
    Value Object - Commande de création de vente
    """

    magasin_id: MagasinId
    produit_id: ProduitId
    quantite: int
    client_id: ClientId  # Rendu obligatoire pour tracer les transactions

    def __post_init__(self):
        if self.quantite <= 0:
            raise ValueError("La quantité doit être positive")


@dataclass(frozen=True)
class Money:
    """
    Value Object - Montant monétaire
    """

    amount: Decimal
    currency: str = "CAD"

    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Le montant ne peut pas être négatif")

    def __add__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError("Impossible d'additionner des devises différentes")
        return Money(self.amount + other.amount, self.currency)

    def __mul__(self, factor: int) -> "Money":
        return Money(self.amount * factor, self.currency)
