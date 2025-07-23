"""
Implémentation Django du Repository Panier
Infrastructure - Persistance en base PostgreSQL
"""

import uuid
import json
import logging
from typing import Optional, List
from django.db import transaction

from ..models import PanierModel, ProduitPanierModel
from ..application.repositories.panier_repository import PanierRepository
from ..domain.entities import Panier
from ..domain.value_objects import ProduitPanier, QuantiteProduit
from decimal import Decimal

logger = logging.getLogger("panier")


class DjangoPanierRepository(PanierRepository):
    """
    Implémentation Django du repository Panier
    Convertit entre entités DDD et modèles Django
    """

    def save(self, panier: Panier) -> None:
        """
        Sauvegarde un panier avec ses produits
        """
        with transaction.atomic():
            # Créer ou mettre à jour le panier
            panier_model, created = PanierModel.objects.update_or_create(
                id=panier.id,
                defaults={
                    "client_id": panier.client_id,
                    "date_creation": panier.date_creation,
                    "date_modification": panier.date_modification,
                },
            )

            # Supprimer les anciens produits
            ProduitPanierModel.objects.filter(panier=panier_model).delete()

            # Ajouter les nouveaux produits
            for produit in panier.produits:
                ProduitPanierModel.objects.create(
                    panier=panier_model,
                    produit_id=produit.produit_id,
                    nom_produit=produit.nom_produit,
                    prix_unitaire=produit.prix_unitaire,
                    quantite=produit.quantite.valeur,
                )

            logger.debug(
                f"Panier {panier.id} sauvegardé avec {len(panier.produits)} produits"
            )

    def get_by_id(self, panier_id: uuid.UUID) -> Optional[Panier]:
        """
        Récupère un panier par son ID avec ses produits
        """
        try:
            panier_model = PanierModel.objects.get(id=panier_id)
            return self._model_to_entity(panier_model)
        except PanierModel.DoesNotExist:
            return None

    def get_by_client_id(self, client_id: uuid.UUID) -> Optional[Panier]:
        """
        Récupère le panier actuel d'un client (le plus récent)
        """
        try:
            panier_model = (
                PanierModel.objects.filter(client_id=client_id)
                .order_by("-date_modification")
                .first()
            )

            if panier_model:
                return self._model_to_entity(panier_model)
            return None
        except Exception as e:
            logger.error(f"Erreur récupération panier client {client_id}: {str(e)}")
            return None

    def delete(self, panier_id: uuid.UUID) -> bool:
        """
        Supprime un panier et ses produits
        """
        try:
            with transaction.atomic():
                panier_model = PanierModel.objects.get(id=panier_id)
                panier_model.delete()  # Cascade supprime aussi les produits
                logger.debug(f"Panier {panier_id} supprimé")
                return True
        except PanierModel.DoesNotExist:
            return False
        except Exception as e:
            logger.error(f"Erreur suppression panier {panier_id}: {str(e)}")
            return False

    def get_all_by_client(self, client_id: uuid.UUID) -> List[Panier]:
        """
        Récupère tous les paniers d'un client
        """
        try:
            paniers_models = PanierModel.objects.filter(client_id=client_id).order_by(
                "-date_creation"
            )

            return [self._model_to_entity(model) for model in paniers_models]
        except Exception as e:
            logger.error(f"Erreur récupération paniers client {client_id}: {str(e)}")
            return []

    def _model_to_entity(self, panier_model: PanierModel) -> Panier:
        """
        Convertit un modèle Django en entité DDD
        """
        # Créer l'entité panier
        panier = Panier(
            id=panier_model.id,
            client_id=panier_model.client_id,
            date_creation=panier_model.date_creation,
        )

        # Ajouter les produits
        for produit_model in panier_model.produits.all():
            produit_panier = ProduitPanier(
                produit_id=produit_model.produit_id,
                nom_produit=produit_model.nom_produit,
                prix_unitaire=produit_model.prix_unitaire,
                quantite=QuantiteProduit(produit_model.quantite),
            )

            # Accès direct à la liste interne pour la reconstruction
            panier._produits.append(produit_panier)

        # Mettre à jour la date de modification
        panier._date_modification = panier_model.date_modification

        return panier
