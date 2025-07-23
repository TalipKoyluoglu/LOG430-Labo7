"""
Use Case: Ajouter un Produit
Fonctionnalité métier complète pour ajouter un produit au catalogue
"""

import uuid
from typing import Dict, Any

from ..repositories.produit_repository import ProduitRepository
from ..repositories.categorie_repository import CategorieRepository
from ...domain.entities import Produit
from ...domain.value_objects import (
    CommandeProduitSimple,
    NomProduit,
    PrixMonetaire,
    CategorieId,
)
from ...domain.exceptions import (
    ProduitDejaExistantError,
    CategorieInexistanteError,
    NomProduitInvalideError,
)


class AjouterProduitUseCase:
    """
    Use Case: Ajouter un nouveau produit au catalogue

    Orchestration complète de la fonctionnalité métier:
    1. Validation de la commande (VO)
    2. Vérification unicité du nom
    3. Vérification unicité du SKU (si fourni)
    4. Validation existence catégorie
    5. Création entité Produit (avec logique métier)
    6. Persistance
    """

    def __init__(
        self,
        produit_repository: ProduitRepository,
        categorie_repository: CategorieRepository,
    ):
        self._produit_repo = produit_repository
        self._categorie_repo = categorie_repository

    def execute(self, commande: CommandeProduitSimple) -> Dict[str, Any]:
        """
        Exécute l'ajout d'un produit au catalogue

        Args:
            commande: CommandeProduitSimple avec les données du produit (catégorie en string)

        Returns:
            Dict contenant les détails du produit créé

        Raises:
            ProduitDejaExistantError: Si nom ou SKU déjà existant
            CategorieInexistanteError: Si la catégorie n'existe pas
            NomProduitInvalideError: Si le nom est invalide
        """

        # 1. Validation de la commande (déjà fait par les VO)
        if not commande.est_valide():
            raise ValueError("Commande produit invalide")

        # 2. Vérification unicité du nom (règle métier)
        self._verifier_unicite_nom(commande.nom)

        # 3. Vérification unicité du SKU (règle métier)
        if commande.sku:
            self._verifier_unicite_sku(commande.sku)

        # 4. Conversion du nom de catégorie en UUID (adaptation technique)
        categorie_id = self._convertir_nom_vers_uuid(commande.categorie)

        # 5. Validation existence et état de la catégorie (règle métier)
        self._valider_categorie(categorie_id)

        # 6. Création de l'entité Produit (logique métier dans l'entité)
        produit_id = uuid.uuid4()
        produit = Produit(
            id=produit_id,
            nom=commande.nom,
            categorie_id=categorie_id,
            prix=commande.prix,
            description=commande.description,
            sku=commande.sku,
        )

        # 7. Persistance via repository
        produit_sauvegarde = self._produit_repo.save(produit)

        # 8. Retour avec données enrichies (format simplifié)
        return self._produit_to_dict_simple(produit_sauvegarde, commande.categorie)

    def _verifier_unicite_nom(self, nom: NomProduit) -> None:
        """
        Vérifie l'unicité du nom de produit (règle métier)
        """
        produit_existant = self._produit_repo.get_by_nom(nom.valeur)
        if produit_existant:
            raise ProduitDejaExistantError(
                f"Un produit avec le nom '{nom.valeur}' existe déjà (ID: {produit_existant.id})"
            )

    def _verifier_unicite_sku(self, sku) -> None:
        """
        Vérifie l'unicité du SKU (règle métier)
        """
        produit_existant = self._produit_repo.get_by_sku(sku.code)
        if produit_existant:
            raise ProduitDejaExistantError(
                f"Un produit avec le SKU '{sku.code}' existe déjà (ID: {produit_existant.id})"
            )

    def _valider_categorie(self, categorie_id: CategorieId) -> None:
        """
        Valide l'existence et l'état de la catégorie (règle métier)
        """
        categorie = self._categorie_repo.get_by_id(categorie_id)

        if not categorie:
            raise CategorieInexistanteError(str(categorie_id))

        if not categorie.est_active:
            raise CategorieInexistanteError(
                f"La catégorie {categorie_id} est désactivée, impossible d'y ajouter des produits"
            )

    def _convertir_nom_vers_uuid(self, nom_categorie: str) -> CategorieId:
        """
        Convertit un nom de catégorie en UUID
        Solution temporaire en attendant une refactorisation complète
        """
        # Génération d'UUID déterministe basé sur le nom
        # (solution temporaire pour maintenir la cohérence)
        import hashlib

        namespace_uuid = uuid.UUID("12345678-1234-5678-1234-123456789abc")
        categorie_uuid = uuid.uuid5(namespace_uuid, nom_categorie)
        return CategorieId(categorie_uuid)

    def _produit_to_dict_simple(
        self, produit: Produit, nom_categorie: str
    ) -> Dict[str, Any]:
        """
        Convertit le produit créé en dictionnaire simplifié pour la réponse
        """
        return {
            "id": str(produit.id),
            "nom": produit.nom.valeur,
            "categorie": nom_categorie,  # Nom lisible au lieu d'UUID
            "prix": float(produit.prix.montant),
            "description": produit.description,
            "date_creation": produit.date_creation.isoformat(),
            "date_modification": produit.date_modification.isoformat(),
            "message": "Produit ajouté avec succès au catalogue",
        }

    def _produit_to_dict(self, produit: Produit) -> Dict[str, Any]:
        """
        Convertit le produit créé en dictionnaire pour la réponse (format complet - obsolète)
        """
        return {
            "id": str(produit.id),
            "nom": produit.nom.valeur,
            "categorie_id": str(produit.categorie_id),
            "prix": float(produit.prix.montant),
            "devise": produit.prix.devise,
            "description": produit.description,
            "sku": produit.sku.code if produit.sku else None,
            "est_actif": produit.est_actif,
            "est_premium": produit.est_premium(),
            "date_creation": produit.date_creation.isoformat(),
            "date_modification": produit.date_modification.isoformat(),
            "message": "Produit ajouté avec succès au catalogue",
        }
