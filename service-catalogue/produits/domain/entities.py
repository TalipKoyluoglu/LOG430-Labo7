"""
Entités du domaine Catalogue
Les entités contiennent l'identité et la logique métier
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from .value_objects import NomProduit, PrixMonetaire, ReferenceSKU, CategorieId
from .exceptions import (
    PrixInvalideError,
    NomProduitInvalideError,
    CategorieInexistanteError,
)


class Produit:
    """
    Entité Aggregate Root - Produit
    Contient toute la logique métier liée aux produits du catalogue
    """

    def __init__(
        self,
        id: uuid.UUID,
        nom: NomProduit,
        categorie_id: CategorieId,
        prix: PrixMonetaire,
        description: Optional[str] = None,
        sku: Optional[ReferenceSKU] = None,
        date_creation: Optional[datetime] = None,
    ):
        self._id = id
        self._nom = nom
        self._categorie_id = categorie_id
        self._prix = prix
        self._description = description or ""
        self._sku = sku
        self._date_creation = date_creation or datetime.now()
        self._date_modification = datetime.now()
        self._est_actif = True
        self._historique_prix: List[PrixMonetaire] = [prix]

    @property
    def id(self) -> uuid.UUID:
        return self._id

    @property
    def nom(self) -> NomProduit:
        return self._nom

    @property
    def categorie_id(self) -> CategorieId:
        return self._categorie_id

    @property
    def prix(self) -> PrixMonetaire:
        return self._prix

    @property
    def description(self) -> str:
        return self._description

    @property
    def sku(self) -> Optional[ReferenceSKU]:
        return self._sku

    @property
    def date_creation(self) -> datetime:
        return self._date_creation

    @property
    def date_modification(self) -> datetime:
        return self._date_modification

    @property
    def est_actif(self) -> bool:
        return self._est_actif

    @property
    def historique_prix(self) -> List[PrixMonetaire]:
        return self._historique_prix.copy()

    def modifier_prix(self, nouveau_prix: PrixMonetaire) -> None:
        """
        Modifie le prix du produit (logique métier avec historique)
        """
        if nouveau_prix.montant <= 0:
            raise PrixInvalideError("Le prix doit être strictement positif")

        # Règle métier : pas de modification si même prix
        if nouveau_prix.montant == self._prix.montant:
            return

        # Sauvegarde dans l'historique
        self._historique_prix.append(nouveau_prix)
        self._prix = nouveau_prix
        self._date_modification = datetime.now()

    def modifier_nom(self, nouveau_nom: NomProduit) -> None:
        """
        Modifie le nom du produit (logique métier avec validation)
        """
        if not nouveau_nom.valeur.strip():
            raise NomProduitInvalideError("Le nom ne peut pas être vide")

        self._nom = nouveau_nom
        self._date_modification = datetime.now()

    def modifier_description(self, nouvelle_description: str) -> None:
        """
        Modifie la description du produit
        """
        self._description = nouvelle_description or ""
        self._date_modification = datetime.now()

    def changer_categorie(self, nouvelle_categorie_id: CategorieId) -> None:
        """
        Change la catégorie du produit (logique métier)
        """
        self._categorie_id = nouvelle_categorie_id
        self._date_modification = datetime.now()

    def archiver(self) -> None:
        """
        Archive le produit (logique métier)
        Un produit archivé ne peut plus être vendu
        """
        self._est_actif = False
        self._date_modification = datetime.now()

    def reactiver(self) -> None:
        """
        Réactive le produit
        """
        self._est_actif = True
        self._date_modification = datetime.now()

    def calculer_evolution_prix(self) -> Decimal:
        """
        Calcule l'évolution du prix depuis la création (logique métier)
        """
        if len(self._historique_prix) < 2:
            return Decimal("0")

        prix_initial = self._historique_prix[0].montant
        prix_actuel = self._prix.montant

        return ((prix_actuel - prix_initial) / prix_initial) * 100

    def est_premium(self) -> bool:
        """
        Détermine si le produit est premium (logique métier)
        Règle : prix > 100€
        """
        return self._prix.montant > Decimal("100.00")

    def peut_etre_supprime(self) -> bool:
        """
        Vérifie si le produit peut être supprimé (invariant métier)
        Règle : Seuls les produits archivés peuvent être supprimés
        """
        return not self._est_actif

    def __str__(self):
        return f"Produit({self._nom.valeur} - {self._prix.montant}€)"


class Categorie:
    """
    Entité Catégorie avec logique métier
    """

    def __init__(
        self,
        id: CategorieId,
        nom: str,
        description: Optional[str] = None,
        parent_id: Optional[CategorieId] = None,
    ):
        self._id = id
        self._nom = nom
        self._description = description or ""
        self._parent_id = parent_id
        self._est_active = True
        self._sous_categories: List[CategorieId] = []

    @property
    def id(self) -> CategorieId:
        return self._id

    @property
    def nom(self) -> str:
        return self._nom

    @property
    def description(self) -> str:
        return self._description

    @property
    def parent_id(self) -> Optional[CategorieId]:
        return self._parent_id

    @property
    def est_active(self) -> bool:
        return self._est_active

    @property
    def sous_categories(self) -> List[CategorieId]:
        return self._sous_categories.copy()

    def ajouter_sous_categorie(self, sous_categorie_id: CategorieId) -> None:
        """
        Ajoute une sous-catégorie (logique métier)
        """
        if sous_categorie_id not in self._sous_categories:
            self._sous_categories.append(sous_categorie_id)

    def supprimer_sous_categorie(self, sous_categorie_id: CategorieId) -> None:
        """
        Supprime une sous-catégorie
        """
        if sous_categorie_id in self._sous_categories:
            self._sous_categories.remove(sous_categorie_id)

    def est_racine(self) -> bool:
        """
        Vérifie si la catégorie est une catégorie racine (logique métier)
        """
        return self._parent_id is None

    def a_des_sous_categories(self) -> bool:
        """
        Vérifie si la catégorie a des sous-catégories
        """
        return len(self._sous_categories) > 0

    def peut_etre_supprimee(self) -> bool:
        """
        Vérifie si la catégorie peut être supprimée (invariant métier)
        Règle : Pas de sous-catégories et pas de produits
        """
        return not self.a_des_sous_categories()

    def desactiver(self) -> None:
        """
        Désactive la catégorie (logique métier)
        """
        self._est_active = False

    def activer(self) -> None:
        """
        Active la catégorie
        """
        self._est_active = True

    def __str__(self):
        return f"Categorie({self._nom})"
