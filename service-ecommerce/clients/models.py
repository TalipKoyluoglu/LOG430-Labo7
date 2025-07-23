"""
Modèles Django pour la persistance des clients
Infrastructure layer - mapping vers la base de données
"""

import uuid
from django.db import models
from django.core.validators import EmailValidator


class ClientModel(models.Model):
    """
    Modèle Django pour la persistance des clients
    Infrastructure - ne contient PAS de logique métier
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Nom complet
    prenom = models.CharField(max_length=100, help_text="Prénom du client")
    nom = models.CharField(max_length=100, help_text="Nom du client")

    # Email unique
    email = models.EmailField(
        unique=True, validators=[EmailValidator()], help_text="Email unique du client"
    )

    # Téléphone optionnel
    telephone = models.CharField(
        max_length=20, null=True, blank=True, help_text="Numéro de téléphone"
    )

    # Adresse
    adresse_rue = models.TextField(help_text="Adresse rue")
    adresse_ville = models.CharField(max_length=100, help_text="Ville")
    adresse_code_postal = models.CharField(max_length=10, help_text="Code postal")
    adresse_province = models.CharField(
        max_length=50, default="Québec", help_text="Province"
    )
    adresse_pays = models.CharField(max_length=50, default="Canada", help_text="Pays")

    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    actif = models.BooleanField(default=True, help_text="Compte actif ou non")

    class Meta:
        db_table = "clients"
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        ordering = ["-date_creation"]

    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.email})"
