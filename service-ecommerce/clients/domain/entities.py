"""
Entités du domaine Clients E-commerce
Les entités contiennent l'identité et la logique métier
"""

import uuid
from datetime import datetime
from typing import Optional
from .value_objects import Email, Adresse, NomComplet
from .exceptions import ClientInactifError, EmailDejaUtiliseError


class Client:
    """
    Entité Aggregate Root - Client
    Contient toute la logique métier liée aux clients
    """

    def __init__(
        self,
        id: uuid.UUID,
        nom_complet: NomComplet,
        email: Email,
        adresse: Adresse,
        telephone: Optional[str] = None,
        date_creation: Optional[datetime] = None,
    ):
        self._id = id
        self._nom_complet = nom_complet
        self._email = email
        self._adresse = adresse
        self._telephone = telephone
        self._date_creation = date_creation or datetime.now()
        self._date_modification = datetime.now()
        self._actif = True

    @property
    def id(self) -> uuid.UUID:
        return self._id

    @property
    def nom_complet(self) -> NomComplet:
        return self._nom_complet

    @property
    def email(self) -> Email:
        return self._email

    @property
    def adresse(self) -> Adresse:
        return self._adresse

    @property
    def telephone(self) -> Optional[str]:
        return self._telephone

    @property
    def date_creation(self) -> datetime:
        return self._date_creation

    @property
    def date_modification(self) -> datetime:
        return self._date_modification

    @property
    def actif(self) -> bool:
        return self._actif

    def modifier_adresse(self, nouvelle_adresse: Adresse) -> None:
        """
        Modifie l'adresse du client (logique métier)
        """
        if not self._actif:
            raise ClientInactifError("Impossible de modifier un client inactif")

        self._adresse = nouvelle_adresse
        self._date_modification = datetime.now()

    def modifier_telephone(self, nouveau_telephone: Optional[str]) -> None:
        """
        Modifie le téléphone du client (logique métier)
        """
        if not self._actif:
            raise ClientInactifError("Impossible de modifier un client inactif")

        self._telephone = nouveau_telephone
        self._date_modification = datetime.now()

    def desactiver(self) -> None:
        """
        Désactive le compte client (logique métier avec invariants)
        """
        if not self._actif:
            raise ClientInactifError("Le client est déjà inactif")

        self._actif = False
        self._date_modification = datetime.now()

    def reactiver(self) -> None:
        """
        Réactive le compte client (logique métier)
        """
        if self._actif:
            return  # Déjà actif, pas d'erreur

        self._actif = True
        self._date_modification = datetime.now()

    def peut_passer_commande(self) -> bool:
        """
        Vérifie si le client peut passer une commande (logique métier)
        """
        return self._actif

    def valider_pour_commande(self) -> dict:
        """
        Retourne les informations de validation pour une commande
        """
        if not self.peut_passer_commande():
            raise ClientInactifError("Client inactif ne peut pas passer de commande")

        return {
            "client_id": str(self._id),
            "nom_complet": self._nom_complet.affichage(),
            "email": str(self._email),
            "adresse_livraison": self._adresse.adresse_complete(),
            "telephone": self._telephone,
        }

    def __str__(self):
        return f"Client {self._nom_complet.affichage()} ({self._email})"
