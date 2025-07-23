"""
Value Objects du domaine Catalogue
Les value objects sont immuables et définissent des concepts métier
"""

import uuid
import re
from decimal import Decimal
from dataclasses import dataclass
from typing import NewType
from .exceptions import NomProduitInvalideError, PrixInvalideError, SKUInvalideError


# Type Aliases pour la sécurité des types
ProduitId = NewType("ProduitId", uuid.UUID)
CategorieId = NewType("CategorieId", uuid.UUID)


@dataclass(frozen=True)
class NomProduit:
    """
    Value Object - Nom de produit avec validation métier
    """

    valeur: str

    def __post_init__(self):
        if not self.valeur or not self.valeur.strip():
            raise NomProduitInvalideError("Le nom du produit ne peut pas être vide")

        if len(self.valeur.strip()) < 2:
            raise NomProduitInvalideError(
                "Le nom du produit doit contenir au moins 2 caractères"
            )

        if len(self.valeur) > 100:
            raise NomProduitInvalideError(
                "Le nom du produit ne peut pas dépasser 100 caractères"
            )

        # Pas de caractères spéciaux dangereux
        if re.search(r'[<>"\'\&]', self.valeur):
            raise NomProduitInvalideError("Le nom contient des caractères interdits")

        # Remplace la valeur par la version nettoyée
        object.__setattr__(self, "valeur", self.valeur.strip())

    def est_similaire_a(self, autre_nom: "NomProduit") -> bool:
        """
        Vérifie si deux noms sont similaires (logique métier)
        """
        return self.valeur.lower() == autre_nom.valeur.lower()


@dataclass(frozen=True)
class PrixMonetaire:
    """
    Value Object - Prix avec logique métier monétaire
    """

    montant: Decimal
    devise: str = "EUR"

    def __post_init__(self):
        if self.montant < Decimal("0"):
            raise PrixInvalideError("Le prix ne peut pas être négatif")

        if self.montant > Decimal("999999.99"):
            raise PrixInvalideError("Le prix ne peut pas dépasser 999,999.99")

        # Arrondir à 2 décimales
        object.__setattr__(self, "montant", self.montant.quantize(Decimal("0.01")))

        if self.devise not in ["EUR", "USD", "CAD"]:
            raise PrixInvalideError(f"Devise non supportée: {self.devise}")

    def appliquer_remise(self, pourcentage: Decimal) -> "PrixMonetaire":
        """
        Applique une remise et retourne un nouveau prix (logique métier)
        """
        if pourcentage < 0 or pourcentage > 100:
            raise ValueError("Le pourcentage de remise doit être entre 0 et 100")

        nouveau_montant = self.montant * (Decimal("100") - pourcentage) / Decimal("100")
        return PrixMonetaire(nouveau_montant, self.devise)

    def est_gratuit(self) -> bool:
        """
        Vérifie si le produit est gratuit
        """
        return self.montant == Decimal("0")

    def est_premium(self) -> bool:
        """
        Détermine si le prix est considéré comme premium
        """
        return self.montant > Decimal("100.00")

    def comparer_avec(self, autre_prix: "PrixMonetaire") -> str:
        """
        Compare avec un autre prix (logique métier)
        """
        if self.devise != autre_prix.devise:
            raise ValueError(
                "Impossible de comparer des prix dans des devises différentes"
            )

        if self.montant > autre_prix.montant:
            return "plus_cher"
        elif self.montant < autre_prix.montant:
            return "moins_cher"
        else:
            return "identique"

    def __str__(self):
        return f"{self.montant} {self.devise}"


@dataclass(frozen=True)
class ReferenceSKU:
    """
    Value Object - SKU (Stock Keeping Unit) avec validation
    """

    code: str

    def __post_init__(self):
        if not self.code or not self.code.strip():
            raise SKUInvalideError("Le SKU ne peut pas être vide")

        # Format : 3 lettres + 4 chiffres (ex: ABC1234)
        pattern = r"^[A-Z]{3}\d{4}$"
        if not re.match(pattern, self.code.upper()):
            raise SKUInvalideError(
                "Le SKU doit avoir le format ABC1234 (3 lettres + 4 chiffres)"
            )

        # Normalise en majuscules
        object.__setattr__(self, "code", self.code.upper())

    def est_valide(self) -> bool:
        """
        Vérifie si le SKU est valide
        """
        return bool(re.match(r"^[A-Z]{3}\d{4}$", self.code))

    def extraire_categorie(self) -> str:
        """
        Extrait le code catégorie (les 3 premières lettres)
        """
        return self.code[:3]

    def extraire_numero(self) -> str:
        """
        Extrait le numéro de série (les 4 derniers chiffres)
        """
        return self.code[3:]


@dataclass(frozen=True)
class CritereRecherche:
    """
    Value Object - Critères de recherche produits
    """

    nom: str = ""
    categorie_id: CategorieId = None
    prix_min: Decimal = None
    prix_max: Decimal = None
    actifs_seulement: bool = True

    def __post_init__(self):
        # Validation des prix
        if self.prix_min is not None and self.prix_min < 0:
            raise ValueError("Le prix minimum ne peut pas être négatif")

        if self.prix_max is not None and self.prix_max < 0:
            raise ValueError("Le prix maximum ne peut pas être négatif")

        if (
            self.prix_min is not None
            and self.prix_max is not None
            and self.prix_min > self.prix_max
        ):
            raise ValueError(
                "Le prix minimum ne peut pas être supérieur au prix maximum"
            )

    def a_filtre_prix(self) -> bool:
        """
        Vérifie si des filtres de prix sont appliqués
        """
        return self.prix_min is not None or self.prix_max is not None

    def a_filtre_nom(self) -> bool:
        """
        Vérifie si un filtre de nom est appliqué
        """
        return bool(self.nom and self.nom.strip())

    def a_filtre_categorie(self) -> bool:
        """
        Vérifie si un filtre de catégorie est appliqué
        """
        return self.categorie_id is not None


@dataclass(frozen=True)
class CommandeProduit:
    """
    Value Object - Commande de création/modification de produit (version UUID - obsolète)
    """

    nom: NomProduit
    categorie_id: CategorieId
    prix: PrixMonetaire
    description: str = ""
    sku: ReferenceSKU = None

    def est_valide(self) -> bool:
        """
        Vérifie si la commande est valide (toutes les validations sont dans les VO)
        """
        return True  # Si on arrive ici, les VO ont validé leurs données


@dataclass(frozen=True)
class CommandeProduitSimple:
    """
    Value Object - Commande simplifiée avec nom de catégorie string
    Version simplifiée pour une meilleure UX
    """

    nom: NomProduit
    categorie: str  # Nom de catégorie comme "Informatique", "Boissons", etc.
    prix: PrixMonetaire
    description: str = ""
    sku: ReferenceSKU = None

    def __post_init__(self):
        # Validation du nom de catégorie
        if not self.categorie or not self.categorie.strip():
            raise ValueError("Le nom de catégorie ne peut pas être vide")

        # Validation que la catégorie est dans les catégories connues
        categories_valides = {
            "Informatique",
            "Boissons",
            "Confiserie",
            "Électronique",
            "Meubles",
            "Vêtements",
        }
        if self.categorie not in categories_valides:
            raise ValueError(
                f"Catégorie '{self.categorie}' non valide. Catégories acceptées: {', '.join(categories_valides)}"
            )

        # Nettoyer le nom de catégorie
        object.__setattr__(self, "categorie", self.categorie.strip())

    def est_valide(self) -> bool:
        """
        Vérifie si la commande est valide (toutes les validations sont dans les VO)
        """
        return True  # Si on arrive ici, les VO ont validé leurs données
