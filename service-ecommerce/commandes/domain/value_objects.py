"""
Value Objects du domaine Check-out
Les value objects sont immuables et définissent des concepts métier
"""

import uuid
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Dict, Any, Optional


class StatutCheckout(Enum):
    """
    Enumération des statuts du processus de check-out
    """

    INITIALISE = "initialise"
    PANIER_VALIDE = "panier_valide"
    ADRESSE_DEFINIE = "adresse_definie"
    STOCKS_VALIDES = "stocks_valides"
    FINALISE = "finalise"
    ECHEC = "echec"


@dataclass(frozen=True)
class LigneCommande:
    """
    Value Object - Ligne de commande avec validation métier
    """

    produit_id: uuid.UUID
    nom_produit: str
    quantite: int
    prix_unitaire: Decimal

    def __post_init__(self):
        if not self.nom_produit or not self.nom_produit.strip():
            raise ValueError("Le nom du produit ne peut pas être vide")

        if self.quantite <= 0:
            raise ValueError("La quantité doit être positive")

        if self.quantite > 99:
            raise ValueError("La quantité maximum par produit est de 99")

        if self.prix_unitaire < Decimal("0"):
            raise ValueError("Le prix unitaire ne peut pas être négatif")

    def prix_total(self) -> Decimal:
        """Calcule le prix total pour cette ligne"""
        return self.prix_unitaire * Decimal(str(self.quantite))

    def __str__(self):
        return f"{self.nom_produit} x{self.quantite} = {self.prix_total()}€"


@dataclass(frozen=True)
class AdresseLivraison:
    """
    Value Object - Adresse de livraison avec validation
    """

    nom_destinataire: str
    rue: str
    ville: str
    code_postal: str
    province: str
    pays: str
    instructions_livraison: Optional[str] = None
    livraison_express: bool = False

    def __post_init__(self):
        # Validation des champs obligatoires
        champs_requis = [
            ("nom_destinataire", self.nom_destinataire),
            ("rue", self.rue),
            ("ville", self.ville),
            ("code_postal", self.code_postal),
            ("province", self.province),
            ("pays", self.pays),
        ]

        for nom_champ, valeur in champs_requis:
            if not valeur or not valeur.strip():
                raise ValueError(f"Le champ {nom_champ} est obligatoire")

        # Validation du code postal (format québécois basique)
        if len(self.code_postal.replace(" ", "")) < 6:
            raise ValueError("Code postal invalide")

    def adresse_complete(self) -> str:
        """Retourne l'adresse formatée complète"""
        return (
            f"{self.rue}, {self.ville}, {self.province} {self.code_postal}, {self.pays}"
        )

    def est_livraison_express(self) -> bool:
        """Vérifie si c'est une livraison express"""
        return self.livraison_express

    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire pour sérialisation"""
        return {
            "nom_destinataire": self.nom_destinataire,
            "rue": self.rue,
            "ville": self.ville,
            "code_postal": self.code_postal,
            "province": self.province,
            "pays": self.pays,
            "adresse_complete": self.adresse_complete(),
            "instructions_livraison": self.instructions_livraison,
            "livraison_express": self.livraison_express,
        }

    def __str__(self):
        return f"{self.nom_destinataire} - {self.adresse_complete()}"


@dataclass(frozen=True)
class CommandeEcommerce:
    """
    Value Object - Commande e-commerce pour création externe
    """

    client_id: uuid.UUID
    lignes_commande: tuple  # Tuple pour immutabilité
    adresse_livraison: AdresseLivraison
    sous_total: Decimal
    frais_livraison: Decimal
    total: Decimal
    notes: Optional[str] = None

    def __post_init__(self):
        if not self.lignes_commande:
            raise ValueError("Une commande doit contenir au moins une ligne")

        if self.sous_total < Decimal("0"):
            raise ValueError("Le sous-total ne peut pas être négatif")

        if self.frais_livraison < Decimal("0"):
            raise ValueError("Les frais de livraison ne peuvent pas être négatifs")

        # Vérifier la cohérence des calculs
        total_calcule = self.sous_total + self.frais_livraison
        if abs(self.total - total_calcule) > Decimal("0.01"):
            raise ValueError("Incohérence dans les calculs de total")

    def to_dict_for_service(self) -> Dict[str, Any]:
        """Convertit en dictionnaire pour envoi au service-commandes"""
        return {
            "client_id": str(self.client_id),
            "lignes": [
                {
                    "produit_id": str(ligne.produit_id),
                    "nom_produit": ligne.nom_produit,
                    "quantite": ligne.quantite,
                    "prix_unitaire": float(ligne.prix_unitaire),
                }
                for ligne in self.lignes_commande
            ],
            "adresse_livraison": self.adresse_livraison.to_dict(),
            "calculs": {
                "sous_total": float(self.sous_total),
                "frais_livraison": float(self.frais_livraison),
                "total": float(self.total),
            },
            "notes": self.notes,
        }

    def nombre_articles(self) -> int:
        """Retourne le nombre total d'articles"""
        return sum(ligne.quantite for ligne in self.lignes_commande)

    def nombre_produits_differents(self) -> int:
        """Retourne le nombre de produits différents"""
        return len(self.lignes_commande)


@dataclass(frozen=True)
class DemandeCheckout:
    """
    Value Object - Demande de check-out depuis l'API
    """

    client_id: uuid.UUID
    panier_id: uuid.UUID
    adresse_livraison: AdresseLivraison
    livraison_express: bool = False
    notes: Optional[str] = None

    def __post_init__(self):
        if not self.client_id:
            raise ValueError("L'ID client est obligatoire")

        if not self.panier_id:
            raise ValueError("L'ID panier est obligatoire")
