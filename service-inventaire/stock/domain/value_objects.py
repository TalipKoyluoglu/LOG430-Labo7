"""
Value Objects du domaine Inventaire
Objets de valeur avec validation pour l'intégrité des données métier.
"""

from dataclasses import dataclass
from typing import Any
import uuid
import re
from .exceptions import QuantiteInvalideError, InventaireDomainError


@dataclass(frozen=True)
class StockId:
    """Value Object pour l'identifiant unique d'un stock"""

    value: str

    def __post_init__(self):
        if not self.value:
            raise InventaireDomainError("StockId ne peut pas être vide")
        if not isinstance(self.value, str):
            raise InventaireDomainError("StockId doit être une chaîne")

    @classmethod
    def generate(cls) -> "StockId":
        """Génère un nouvel identifiant unique pour un stock"""
        return cls(str(uuid.uuid4()))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class ProduitId:
    """Value Object pour l'identifiant d'un produit (UUID ou entier)"""

    value: str

    def __post_init__(self):
        if not isinstance(self.value, (str, int)):
            raise InventaireDomainError("ProduitId doit être une string ou un entier")
        # Convertir en string si c'est un entier
        if isinstance(self.value, int):
            object.__setattr__(self, "value", str(self.value))
        if not self.value:
            raise InventaireDomainError("ProduitId ne peut pas être vide")

    def __str__(self) -> str:
        return str(self.value)

    def __int__(self) -> int:
        # Pour compatibilité avec l'existant
        try:
            return int(self.value)
        except ValueError:
            # Si c'est un UUID, retourner un hash stable
            return hash(self.value) % (10**9)


@dataclass(frozen=True)
class MagasinId:
    """Value Object pour l'identifiant d'un magasin (UUID ou entier)"""

    value: str

    def __post_init__(self):
        if not isinstance(self.value, (str, int)):
            raise InventaireDomainError("MagasinId doit être une string ou un entier")
        # Convertir en string si c'est un entier
        if isinstance(self.value, int):
            object.__setattr__(self, "value", str(self.value))
        if not self.value:
            raise InventaireDomainError("MagasinId ne peut pas être vide")

    def __str__(self) -> str:
        return str(self.value)

    def __int__(self) -> int:
        # Pour compatibilité avec l'existant
        try:
            return int(self.value)
        except ValueError:
            # Si c'est un UUID, retourner un hash stable
            return hash(self.value) % (10**9)


@dataclass(frozen=True)
class DemandeId:
    """Value Object pour l'identifiant d'une demande de réapprovisionnement"""

    value: str

    def __post_init__(self):
        if not self.value:
            raise InventaireDomainError("DemandeId ne peut pas être vide")
        if not isinstance(self.value, str):
            raise InventaireDomainError("DemandeId doit être une chaîne")
        # Validation format UUID
        try:
            uuid.UUID(self.value)
        except ValueError:
            raise InventaireDomainError(
                f"DemandeId '{self.value}' n'est pas un UUID valide"
            )

    @classmethod
    def generate(cls) -> "DemandeId":
        """Génère un nouvel identifiant unique pour une demande"""
        return cls(str(uuid.uuid4()))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Quantite:
    """
    Value Object pour les quantités avec règles métier de validation.
    Garantit qu'une quantité est toujours valide dans le contexte inventaire.
    """

    value: int

    def __post_init__(self):
        if not isinstance(self.value, int):
            raise QuantiteInvalideError("La quantité doit être un entier")
        if self.value < 0:
            raise QuantiteInvalideError("La quantité ne peut pas être négative")
        if self.value > 10000:
            raise QuantiteInvalideError(
                "La quantité ne peut pas dépasser 10 000 unités"
            )

    @classmethod
    def from_int(cls, value: int) -> "Quantite":
        """Crée une quantité à partir d'un entier avec validation"""
        return cls(value)

    @classmethod
    def zero(cls) -> "Quantite":
        """Retourne une quantité nulle"""
        return cls(0)

    def est_nulle(self) -> bool:
        """Vérifie si la quantité est nulle"""
        return self.value == 0

    def est_positive(self) -> bool:
        """Vérifie si la quantité est positive"""
        return self.value > 0

    def est_critique(self, seuil: int = 5) -> bool:
        """Règle métier : détermine si la quantité est critique"""
        return self.value <= seuil

    def est_faible(self, seuil: int = 10) -> bool:
        """Règle métier : détermine si la quantité est faible"""
        return self.value <= seuil

    def est_importante(self, seuil: int = 100) -> bool:
        """Règle métier : détermine si la quantité est importante"""
        return self.value >= seuil

    def __str__(self) -> str:
        return str(self.value)

    def __int__(self) -> int:
        return self.value

    def __add__(self, other: "Quantite") -> "Quantite":
        """Addition de quantités avec validation"""
        return Quantite.from_int(self.value + other.value)

    def __sub__(self, other: "Quantite") -> "Quantite":
        """Soustraction de quantités avec validation"""
        return Quantite.from_int(self.value - other.value)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Quantite):
            return self.value == other.value
        if isinstance(other, int):
            return self.value == other
        return False

    def __lt__(self, other: "Quantite") -> bool:
        return self.value < other.value

    def __le__(self, other: "Quantite") -> bool:
        return self.value <= other.value

    def __gt__(self, other: "Quantite") -> bool:
        return self.value > other.value

    def __ge__(self, other: "Quantite") -> bool:
        return self.value >= other.value


@dataclass(frozen=True)
class SeuilStock:
    """
    Value Object pour les seuils de stock avec règles métier.
    Définit les niveaux critiques et de réapprovisionnement.
    """

    seuil_critique: int
    seuil_reapprovisionnement: int
    seuil_maximum: int

    def __post_init__(self):
        if self.seuil_critique < 0:
            raise InventaireDomainError("Le seuil critique ne peut pas être négatif")
        if self.seuil_reapprovisionnement < 0:
            raise InventaireDomainError(
                "Le seuil de réapprovisionnement ne peut pas être négatif"
            )
        if self.seuil_maximum < 0:
            raise InventaireDomainError("Le seuil maximum ne peut pas être négatif")

        if self.seuil_critique >= self.seuil_reapprovisionnement:
            raise InventaireDomainError(
                "Le seuil critique doit être inférieur au seuil de réapprovisionnement"
            )

        if self.seuil_reapprovisionnement >= self.seuil_maximum:
            raise InventaireDomainError(
                "Le seuil de réapprovisionnement doit être inférieur au seuil maximum"
            )

    @classmethod
    def defaut(cls) -> "SeuilStock":
        """Seuils par défaut pour la gestion de stock"""
        return cls(seuil_critique=2, seuil_reapprovisionnement=5, seuil_maximum=100)

    def evaluer_niveau(self, quantite: Quantite) -> str:
        """
        Règle métier : Évalue le niveau de stock par rapport aux seuils
        """
        qty = int(quantite)
        if qty <= self.seuil_critique:
            return "Critique"
        elif qty <= self.seuil_reapprovisionnement:
            return "Bas"
        elif qty >= self.seuil_maximum:
            return "Surstockage"
        else:
            return "Normal"

    def necessite_action(self, quantite: Quantite) -> bool:
        """
        Règle métier : Détermine si le niveau de stock nécessite une action
        """
        return int(quantite) <= self.seuil_reapprovisionnement

    def est_critique(self, quantite: Quantite) -> bool:
        """
        Règle métier : Détermine si le stock est à un niveau critique
        """
        return int(quantite) <= self.seuil_critique


@dataclass(frozen=True)
class TypeMouvement:
    """Value Object pour le type de mouvement de stock"""

    value: str

    ENTREE = "ENTREE"
    SORTIE = "SORTIE"
    TRANSFERT = "TRANSFERT"
    AJUSTEMENT = "AJUSTEMENT"

    TYPES_VALIDES = {ENTREE, SORTIE, TRANSFERT, AJUSTEMENT}

    def __post_init__(self):
        if not self.value:
            raise InventaireDomainError("Type de mouvement ne peut pas être vide")
        if self.value not in self.TYPES_VALIDES:
            raise InventaireDomainError(
                f"Type de mouvement '{self.value}' invalide. "
                f"Types valides: {', '.join(self.TYPES_VALIDES)}"
            )

    @classmethod
    def entree(cls) -> "TypeMouvement":
        return cls(cls.ENTREE)

    @classmethod
    def sortie(cls) -> "TypeMouvement":
        return cls(cls.SORTIE)

    @classmethod
    def transfert(cls) -> "TypeMouvement":
        return cls(cls.TRANSFERT)

    @classmethod
    def ajustement(cls) -> "TypeMouvement":
        return cls(cls.AJUSTEMENT)

    def est_entree(self) -> bool:
        return self.value == self.ENTREE

    def est_sortie(self) -> bool:
        return self.value == self.SORTIE

    def est_transfert(self) -> bool:
        return self.value == self.TRANSFERT

    def __str__(self) -> str:
        return self.value
