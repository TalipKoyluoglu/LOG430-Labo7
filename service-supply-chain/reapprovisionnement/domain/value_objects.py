"""
Value Objects du domaine Réapprovisionnement
Objets valeur avec validation et logique métier intégrée.
"""

from dataclasses import dataclass
from typing import Union
from datetime import datetime
import uuid
import re


@dataclass(frozen=True)
class DemandeId:
    """Identifiant unique d'une demande de réapprovisionnement"""

    valeur: str

    def __post_init__(self):
        if not self.valeur:
            raise ValueError("L'ID de la demande ne peut pas être vide")

        # Validation UUID
        try:
            uuid.UUID(self.valeur)
        except ValueError:
            raise ValueError(
                f"L'ID de la demande doit être un UUID valide: {self.valeur}"
            )

    @classmethod
    def from_string(cls, value: str) -> "DemandeId":
        return cls(value)

    def __str__(self) -> str:
        return self.valeur


@dataclass(frozen=True)
class ProduitId:
    """Identifiant unique d'un produit"""

    valeur: str

    def __post_init__(self):
        if not self.valeur:
            raise ValueError("L'ID du produit ne peut pas être vide")

        # Validation UUID
        try:
            uuid.UUID(self.valeur)
        except ValueError:
            raise ValueError(f"L'ID du produit doit être un UUID valide: {self.valeur}")

    @classmethod
    def from_string(cls, value: str) -> "ProduitId":
        return cls(value)

    def __str__(self) -> str:
        return self.valeur


@dataclass(frozen=True)
class MagasinId:
    """Identifiant unique d'un magasin"""

    valeur: str

    def __post_init__(self):
        if not self.valeur:
            raise ValueError("L'ID du magasin ne peut pas être vide")

        # Validation UUID
        try:
            uuid.UUID(self.valeur)
        except ValueError:
            raise ValueError(f"L'ID du magasin doit être un UUID valide: {self.valeur}")

    @classmethod
    def from_string(cls, value: str) -> "MagasinId":
        return cls(value)

    def __str__(self) -> str:
        return self.valeur


@dataclass(frozen=True)
class Quantite:
    """Quantité de produits avec validation métier"""

    valeur: int

    def __post_init__(self):
        if not isinstance(self.valeur, int):
            raise ValueError("La quantité doit être un nombre entier")

        if self.valeur <= 0:
            raise ValueError("La quantité doit être positive")

        if self.valeur > 10000:
            raise ValueError("La quantité ne peut pas dépasser 10 000 unités")

    @classmethod
    def from_int(cls, value: int) -> "Quantite":
        return cls(value)

    def est_importante(self) -> bool:
        """Règle métier : quantité importante si > 100"""
        return self.valeur > 100

    def est_critique(self) -> bool:
        """Règle métier : quantité critique si > 1000"""
        return self.valeur > 1000

    def __int__(self) -> int:
        return self.valeur

    def __str__(self) -> str:
        return str(self.valeur)


@dataclass(frozen=True)
class MotifRejet:
    """Motif de rejet d'une demande avec validation"""

    valeur: str

    def __post_init__(self):
        if not self.valeur or not self.valeur.strip():
            raise ValueError("Le motif de rejet ne peut pas être vide")

        if len(self.valeur.strip()) < 5:
            raise ValueError("Le motif de rejet doit contenir au moins 5 caractères")

        if len(self.valeur) > 500:
            raise ValueError("Le motif de rejet ne peut pas dépasser 500 caractères")

        # Vérifier que ce n'est pas juste de la ponctuation
        if not re.search(r"[a-zA-Z]", self.valeur):
            raise ValueError("Le motif de rejet doit contenir au moins une lettre")

    @classmethod
    def from_string(cls, value: str) -> "MotifRejet":
        return cls(value.strip())

    def est_detaille(self) -> bool:
        """Vérifie si le motif est détaillé (> 50 caractères)"""
        return len(self.valeur) > 50

    def __str__(self) -> str:
        return self.valeur


@dataclass(frozen=True)
class LogValidation:
    """Entrée de log pour le processus de validation"""

    timestamp: datetime
    message: str
    statut: str

    def __post_init__(self):
        if not self.message or not self.message.strip():
            raise ValueError("Le message de log ne peut pas être vide")

        if not self.statut:
            raise ValueError("Le statut ne peut pas être vide")

        if self.timestamp > datetime.now():
            raise ValueError("Le timestamp ne peut pas être dans le futur")

    @classmethod
    def creer(cls, message: str, statut: str) -> "LogValidation":
        return cls(timestamp=datetime.now(), message=message.strip(), statut=statut)

    def format_log(self) -> str:
        """Formate le log pour affichage"""
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {self.statut}: {self.message}"

    def __str__(self) -> str:
        return self.format_log()


@dataclass(frozen=True)
class StatutValidation:
    """Statut d'une étape de validation"""

    nom_etape: str
    reussie: bool
    message: str = ""

    def __post_init__(self):
        if not self.nom_etape or not self.nom_etape.strip():
            raise ValueError("Le nom de l'étape ne peut pas être vide")

        if not self.reussie and not self.message:
            raise ValueError("Un message d'erreur est requis si l'étape a échoué")

    @classmethod
    def succes(cls, nom_etape: str) -> "StatutValidation":
        return cls(nom_etape=nom_etape, reussie=True)

    @classmethod
    def echec(cls, nom_etape: str, message_erreur: str) -> "StatutValidation":
        return cls(nom_etape=nom_etape, reussie=False, message=message_erreur)

    def __str__(self) -> str:
        status = "✅" if self.reussie else "❌"
        return (
            f"{status} {self.nom_etape}: {self.message}"
            if self.message
            else f"{status} {self.nom_etape}"
        )
