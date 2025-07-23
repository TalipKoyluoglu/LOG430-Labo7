"""
Modèles Django pour la persistance du panier
Infrastructure layer - PostgreSQL
"""

import uuid
from django.db import models
from decimal import Decimal


class PanierModel(models.Model):
    """
    Modèle Django pour persister les paniers e-commerce
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client_id = models.UUIDField(db_index=True, help_text="UUID du client propriétaire")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "panier_paniers"
        ordering = ["-date_modification"]
        indexes = [
            models.Index(fields=["client_id"]),
            models.Index(fields=["date_creation"]),
        ]

    def __str__(self):
        return f"Panier {self.id} - Client {self.client_id}"


class ProduitPanierModel(models.Model):
    """
    Modèle Django pour persister les produits d'un panier
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    panier = models.ForeignKey(
        PanierModel,
        on_delete=models.CASCADE,
        related_name="produits",
        help_text="Panier contenant ce produit",
    )
    produit_id = models.UUIDField(
        db_index=True, help_text="UUID du produit depuis le service-catalogue"
    )
    nom_produit = models.CharField(
        max_length=255, help_text="Nom du produit (dénormalisé pour performance)"
    )
    prix_unitaire = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Prix unitaire au moment de l'ajout au panier",
    )
    quantite = models.PositiveIntegerField(
        help_text="Quantité de ce produit dans le panier"
    )
    date_ajout = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "panier_produits"
        unique_together = ["panier", "produit_id"]  # Un produit par panier
        indexes = [
            models.Index(fields=["produit_id"]),
            models.Index(fields=["panier", "produit_id"]),
        ]

    def prix_total(self) -> Decimal:
        """Calcule le prix total pour cette ligne"""
        return Decimal(str(self.prix_unitaire)) * Decimal(str(self.quantite))

    def __str__(self):
        return f"{self.nom_produit} x{self.quantite} - {self.prix_unitaire}€"
