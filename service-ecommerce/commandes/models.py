"""
Modèles Django pour la persistance du check-out e-commerce
Infrastructure layer - PostgreSQL
"""

import uuid
from django.db import models
from decimal import Decimal

# Modèles Django pour le module commandes


class ProcessusCheckoutModel(models.Model):
    """
    Modèle Django pour persister les processus de check-out
    """

    STATUT_CHOICES = [
        ("initialise", "Initialisé"),
        ("panier_valide", "Panier Validé"),
        ("adresse_definie", "Adresse Définie"),
        ("stocks_valides", "Stocks Validés"),
        ("finalise", "Finalisé"),
        ("echec", "Échec"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client_id = models.UUIDField(db_index=True, help_text="UUID du client")
    panier_id = models.UUIDField(db_index=True, help_text="UUID du panier")

    # Statut du processus
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default="initialise",
        help_text="Statut actuel du processus de check-out",
    )

    # Calculs financiers
    sous_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Sous-total des produits",
    )
    frais_livraison = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Frais de livraison",
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Total de la commande",
    )

    # Adresse de livraison
    adresse_nom_destinataire = models.CharField(
        max_length=200, help_text="Nom du destinataire"
    )
    adresse_rue = models.TextField(help_text="Adresse rue")
    adresse_ville = models.CharField(max_length=100, help_text="Ville")
    adresse_code_postal = models.CharField(max_length=20, help_text="Code postal")
    adresse_province = models.CharField(max_length=50, help_text="Province")
    adresse_pays = models.CharField(max_length=50, default="Canada", help_text="Pays")
    adresse_instructions = models.TextField(
        null=True, blank=True, help_text="Instructions de livraison"
    )
    livraison_express = models.BooleanField(
        default=False, help_text="Livraison express"
    )

    # Références externes
    commande_externe_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="ID de la commande créée dans le service-commandes",
    )

    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True)
    date_finalisation = models.DateTimeField(null=True, blank=True)
    erreurs = models.JSONField(default=list, help_text="Liste des erreurs rencontrées")
    notes = models.TextField(null=True, blank=True, help_text="Notes additionnelles")

    class Meta:
        db_table = "commandes_processus_checkout"
        ordering = ["-date_creation"]
        indexes = [
            models.Index(fields=["client_id"]),
            models.Index(fields=["statut"]),
            models.Index(fields=["date_creation"]),
        ]

    def __str__(self):
        return f"Checkout {self.id} - Client {self.client_id} - {self.get_statut_display()}"


class LigneCheckoutModel(models.Model):
    """
    Modèle Django pour persister les lignes de produits du check-out
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    processus_checkout = models.ForeignKey(
        ProcessusCheckoutModel,
        on_delete=models.CASCADE,
        related_name="lignes",
        help_text="Processus de check-out parent",
    )

    # Informations produit
    produit_id = models.UUIDField(db_index=True, help_text="UUID du produit")
    nom_produit = models.CharField(max_length=255, help_text="Nom du produit")
    quantite = models.PositiveIntegerField(help_text="Quantité commandée")
    prix_unitaire = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Prix unitaire au moment du check-out",
    )

    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "commandes_lignes_checkout"
        unique_together = ["processus_checkout", "produit_id"]
        indexes = [
            models.Index(fields=["produit_id"]),
            models.Index(fields=["processus_checkout", "produit_id"]),
        ]

    def prix_total(self) -> Decimal:
        """Calcule le prix total pour cette ligne"""
        return Decimal(str(self.prix_unitaire)) * Decimal(str(self.quantite))

    def __str__(self):
        return f"{self.nom_produit} x{self.quantite} = {self.prix_total()}€"


class CommandeEcommerce(models.Model):
    """
    Modèle Django pour les commandes e-commerce finalisées
    """

    STATUT_CHOICES = [
        ("en_attente", "En attente"),
        ("validee", "Validée"),
        ("payee", "Payée"),
        ("expediee", "Expédiée"),
        ("livree", "Livrée"),
        ("annulee", "Annulée"),
    ]

    # Identifiants
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client_id = models.UUIDField(db_index=True)  # Référence au service clients
    checkout_id = models.UUIDField(unique=True)  # ID du processus de checkout

    # Détails commande
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="validee")
    date_commande = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    # Calculs financiers
    sous_total = models.DecimalField(max_digits=10, decimal_places=2)
    frais_livraison = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    total = models.DecimalField(max_digits=10, decimal_places=2)

    # Adresse de livraison
    nom_destinataire = models.CharField(max_length=255)
    rue = models.CharField(max_length=255)
    ville = models.CharField(max_length=100)
    code_postal = models.CharField(max_length=20)
    province = models.CharField(max_length=50)
    pays = models.CharField(max_length=50, default="Canada")
    instructions_livraison = models.TextField(blank=True, null=True)
    livraison_express = models.BooleanField(default=False)

    # Métadonnées
    notes = models.TextField(blank=True, null=True)
    nombre_articles = models.PositiveIntegerField()
    nombre_produits = models.PositiveIntegerField()

    class Meta:
        db_table = "ecommerce_commandes"
        ordering = ["-date_commande"]
        indexes = [
            models.Index(fields=["client_id", "-date_commande"]),
            models.Index(fields=["statut"]),
            models.Index(fields=["date_commande"]),
        ]

    def __str__(self):
        return f"Commande {self.id} - Client {self.client_id} - {self.total}€"

    @property
    def adresse_complete(self):
        return (
            f"{self.rue}, {self.ville}, {self.province} {self.code_postal}, {self.pays}"
        )


class LigneCommandeEcommerce(models.Model):
    """
    Modèle Django pour les lignes de commande e-commerce
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    commande = models.ForeignKey(
        CommandeEcommerce, on_delete=models.CASCADE, related_name="lignes"
    )

    # Informations produit
    produit_id = models.UUIDField()  # Référence au service catalogue
    nom_produit = models.CharField(max_length=255)
    quantite = models.PositiveIntegerField()
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)
    prix_total = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = "ecommerce_lignes_commandes"
        indexes = [
            models.Index(fields=["commande"]),
            models.Index(fields=["produit_id"]),
        ]

    def __str__(self):
        return f"{self.nom_produit} x{self.quantite} = {self.prix_total}€"
