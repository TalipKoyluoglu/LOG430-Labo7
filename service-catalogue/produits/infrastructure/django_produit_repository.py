"""
Implémentation Django du ProduitRepository
Convertit entre modèles Django et entités domain
"""

from typing import List, Optional
from decimal import Decimal

from django.db import transaction

from ..application.repositories.produit_repository import ProduitRepository
from ..domain.entities import Produit
from ..domain.value_objects import (
    ProduitId,
    CategorieId,
    NomProduit,
    PrixMonetaire,
    ReferenceSKU,
)
from ..models import Produit as ProduitDjango


class DjangoProduitRepository(ProduitRepository):
    """
    Implémentation Django du repository Produit
    Gère la conversion entre modèles Django et entités domain
    """

    @transaction.atomic
    def save(self, produit: Produit) -> Produit:
        """
        Sauvegarde un produit (création ou mise à jour)
        """
        try:
            # Tentative de récupération pour mise à jour
            produit_django = ProduitDjango.objects.get(id=produit.id)
            # Mise à jour des champs
            self._update_django_from_domain(produit_django, produit)
        except ProduitDjango.DoesNotExist:
            # Création d'un nouveau produit
            produit_django = self._create_django_from_domain(produit)

        produit_django.save()

        # Retour de l'entité domain mise à jour
        return self._to_domain_entity(produit_django)

    def get_by_id(self, produit_id: ProduitId) -> Optional[Produit]:
        """
        Récupère un produit par son ID
        """
        try:
            produit_django = ProduitDjango.objects.get(id=produit_id)
            return self._to_domain_entity(produit_django)
        except ProduitDjango.DoesNotExist:
            return None

    def get_by_nom(self, nom: str) -> Optional[Produit]:
        """
        Récupère un produit par son nom
        """
        try:
            produit_django = ProduitDjango.objects.get(nom=nom)
            return self._to_domain_entity(produit_django)
        except ProduitDjango.DoesNotExist:
            return None

    def get_by_sku(self, sku: str) -> Optional[Produit]:
        """
        Récupère un produit par son SKU
        Note: Le modèle Django actuel n'a pas de champ SKU
        """
        # TODO: Ajouter le champ SKU au modèle Django
        return None

    def get_all(self) -> List[Produit]:
        """
        Récupère tous les produits
        """
        produits_django = ProduitDjango.objects.all()
        return [self._to_domain_entity(p) for p in produits_django]

    def get_produits_actifs(self) -> List[Produit]:
        """
        Récupère tous les produits actifs
        Note: Le modèle Django actuel n'a pas de champ est_actif
        """
        # TODO: Ajouter le champ est_actif au modèle Django
        # Pour l'instant, retourne tous les produits
        return self.get_all()

    def get_by_categorie(self, categorie_id: CategorieId) -> List[Produit]:
        """
        Récupère tous les produits d'une catégorie
        """
        produits_django = ProduitDjango.objects.filter(categorie=str(categorie_id))
        return [self._to_domain_entity(p) for p in produits_django]

    def get_produits_premium(self) -> List[Produit]:
        """
        Récupère tous les produits premium (prix > 100€)
        """
        produits_django = ProduitDjango.objects.filter(prix__gt=100)
        return [self._to_domain_entity(p) for p in produits_django]

    def search_by_nom(self, terme: str) -> List[Produit]:
        """
        Recherche de produits par nom
        """
        produits_django = ProduitDjango.objects.filter(
            nom__icontains=terme
        ) | ProduitDjango.objects.filter(description__icontains=terme)
        return [self._to_domain_entity(p) for p in produits_django]

    def delete(self, produit_id: ProduitId) -> bool:
        """
        Supprime un produit
        """
        try:
            produit_django = ProduitDjango.objects.get(id=produit_id)
            produit_django.delete()
            return True
        except ProduitDjango.DoesNotExist:
            return False

    def exists_by_nom(self, nom: str) -> bool:
        """
        Vérifie si un produit avec ce nom existe
        """
        return ProduitDjango.objects.filter(nom=nom).exists()

    def exists_by_sku(self, sku: str) -> bool:
        """
        Vérifie si un produit avec ce SKU existe
        """
        # TODO: Implémenter quand le champ SKU sera ajouté
        return False

    def _to_domain_entity(self, produit_django: ProduitDjango) -> Produit:
        """
        Convertit un modèle Django en entité domain
        """
        # Conversion des value objects
        nom = NomProduit(produit_django.nom)
        prix = PrixMonetaire(produit_django.prix)

        # Note: Le modèle Django actuel utilise categorie (string)
        # au lieu de categorie_id (UUID)
        # TODO: Refactorer le modèle Django pour utiliser des UUID
        try:
            import uuid

            categorie_id = CategorieId(uuid.UUID(produit_django.categorie))
        except ValueError:
            # Fallback si la catégorie n'est pas un UUID valide
            categorie_id = CategorieId(uuid.uuid4())

        # Création de l'entité domain
        produit = Produit(
            id=produit_django.id,
            nom=nom,
            categorie_id=categorie_id,
            prix=prix,
            description=produit_django.description or "",
            sku=None,  # TODO: Ajouter SKU au modèle Django
            date_creation=produit_django.created_at,
        )

        # Mise à jour manuelle de la date de modification
        produit._date_modification = produit_django.updated_at

        return produit

    def _create_django_from_domain(self, produit: Produit) -> ProduitDjango:
        """
        Crée un nouveau modèle Django à partir d'une entité domain
        """
        return ProduitDjango(
            id=produit.id,
            nom=produit.nom.valeur,
            categorie=str(produit.categorie_id),  # TODO: Changer pour FK
            prix=produit.prix.montant,
            description=produit.description,
            # quantite_stock=0,  # Supprimé car pas dans le domain Catalogue
        )

    def _update_django_from_domain(
        self, produit_django: ProduitDjango, produit: Produit
    ) -> None:
        """
        Met à jour un modèle Django existant avec les données domain
        """
        produit_django.nom = produit.nom.valeur
        produit_django.categorie = str(produit.categorie_id)
        produit_django.prix = produit.prix.montant
        produit_django.description = produit.description
