"""
Value Objects du domaine Clients
Les value objects sont immuables et définissent des concepts métier
"""

import re
import uuid
import logging
from dataclasses import dataclass
from typing import NewType, Optional

logger = logging.getLogger("clients")

# Type Aliases pour la sécurité des types
ClientId = NewType("ClientId", uuid.UUID)


@dataclass(frozen=True)
class Email:
    """
    Value Object - Email avec validation métier
    """

    value: str

    def __post_init__(self):
        if not self.value:
            raise ValueError("L'email ne peut pas être vide")

        if not self._is_valid_email(self.value):
            raise ValueError("Format d'email invalide")

        # Normaliser l'email
        object.__setattr__(self, "value", self.value.lower().strip())

    def _is_valid_email(self, email: str) -> bool:
        """Validation regex de l'email"""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    def __str__(self):
        return self.value

    @property
    def domaine(self) -> str:
        """Retourne le domaine de l'email"""
        return self.value.split("@")[1]


@dataclass(frozen=True)
class NomComplet:
    """
    Value Object - Nom complet avec logique métier
    """

    prenom: str
    nom: str

    def __post_init__(self):
        if not self.prenom or not self.prenom.strip():
            raise ValueError("Le prénom ne peut pas être vide")

        if not self.nom or not self.nom.strip():
            raise ValueError("Le nom ne peut pas être vide")

        # Normaliser les noms (première lettre en majuscule)
        object.__setattr__(self, "prenom", self.prenom.strip().title())
        object.__setattr__(self, "nom", self.nom.strip().title())

    def affichage(self) -> str:
        """Retourne le nom complet formaté"""
        return f"{self.prenom} {self.nom}"

    def initiales(self) -> str:
        """Retourne les initiales"""
        return f"{self.prenom[0]}.{self.nom[0]}."

    def __str__(self):
        return self.affichage()


@dataclass(frozen=True)
class Adresse:
    """
    Value Object - Adresse avec validation canadienne
    """

    rue: str
    ville: str
    code_postal: str
    province: str = "Québec"
    pays: str = "Canada"

    def __post_init__(self):
        if not self.rue or not self.rue.strip():
            raise ValueError("L'adresse rue ne peut pas être vide")

        if not self.ville or not self.ville.strip():
            raise ValueError("La ville ne peut pas être vide")

        if not self.code_postal or not self.code_postal.strip():
            raise ValueError("Le code postal ne peut pas être vide")

        # Valider le code postal canadien
        if not self._is_valid_canadian_postal_code(self.code_postal):
            raise ValueError("Code postal canadien invalide (format: A1A 1A1)")

        # Normaliser les données
        object.__setattr__(self, "rue", self.rue.strip().title())
        object.__setattr__(self, "ville", self.ville.strip().title())
        object.__setattr__(
            self, "code_postal", self._format_postal_code(self.code_postal)
        )
        object.__setattr__(self, "province", self.province.strip().title())
        object.__setattr__(self, "pays", self.pays.strip().title())

    def _is_valid_canadian_postal_code(self, postal_code: str) -> bool:
        """Valide le format du code postal canadien"""
        # Enlever les espaces et mettre en majuscule
        clean_code = postal_code.replace(" ", "").upper()
        # Format canadien: A1A1A1
        pattern = r"^[A-Z]\d[A-Z]\d[A-Z]\d$"
        return bool(re.match(pattern, clean_code))

    def _format_postal_code(self, postal_code: str) -> str:
        """Formate le code postal au format A1A 1A1"""
        clean_code = postal_code.replace(" ", "").upper()
        return f"{clean_code[:3]} {clean_code[3:]}"

    def adresse_complete(self) -> str:
        """Retourne l'adresse complète formatée"""
        return (
            f"{self.rue}, {self.ville}, {self.province} {self.code_postal}, {self.pays}"
        )

    def pour_livraison(self) -> str:
        """Retourne l'adresse formatée pour la livraison"""
        return f"{self.rue}\n{self.ville}, {self.province}\n{self.code_postal}\n{self.pays}"

    def __str__(self):
        return self.adresse_complete()


@dataclass(frozen=True)
class CommandeCreationClient:
    """
    Value Object - Commande de création de client
    """

    nom_complet: NomComplet
    email: Email
    adresse: Adresse
    telephone: Optional[str] = None

    def __post_init__(self):
        # Validation du téléphone si fourni
        if self.telephone and not self._is_valid_phone(self.telephone):
            raise ValueError("Format de téléphone invalide")

    def _is_valid_phone(self, phone: str) -> bool:
        """Validation basique du numéro de téléphone"""
        # Enlever tous les caractères non numériques
        numbers_only = re.sub(r"\D", "", phone)
        # Vérifier qu'il reste 10 chiffres (format nord-américain)
        return len(numbers_only) == 10
