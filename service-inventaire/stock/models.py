import uuid
from django.db import models

# Create your models here.


class StockCentral(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    produit_id = models.UUIDField()
    quantite = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"StockCentral {self.produit_id} - {self.quantite}"


class StockLocal(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    produit_id = models.UUIDField()
    magasin_id = models.UUIDField()
    quantite = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"StockLocal {self.produit_id} - {self.magasin_id} - {self.quantite}"


class DemandeReapprovisionnement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    produit_id = models.UUIDField()
    magasin_id = models.UUIDField()
    quantite = models.PositiveIntegerField()
    date = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=20, default="En attente", editable=False)

    def __str__(self):
        return f"Demande {self.id} - Produit {self.produit_id} - Magasin {self.magasin_id} - {self.statut}"
