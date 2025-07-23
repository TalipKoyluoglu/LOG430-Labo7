import uuid
from django.db import models

# Create your models here.


class Magasin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=100)
    adresse = models.TextField()

    def __str__(self):
        return self.nom


class Vente(models.Model):
    STATUT_CHOICES = [
        ("active", "Active"),
        ("annulee", "Annulée"),
        ("remboursee", "Remboursée"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    magasin = models.ForeignKey(
        Magasin, on_delete=models.CASCADE, related_name="ventes"
    )
    date_vente = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    client_id = models.UUIDField(null=True, blank=True)  # Référence au service client
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="active")
    date_annulation = models.DateTimeField(null=True, blank=True)
    motif_annulation = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Vente {self.id} - {self.date_vente.date()} [{self.statut}]"


class LigneVente(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vente = models.ForeignKey(Vente, on_delete=models.CASCADE, related_name="lignes")
    produit_id = models.UUIDField()  # Référence au service produits
    quantite = models.IntegerField()
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantite} x Produit {self.produit_id}"
