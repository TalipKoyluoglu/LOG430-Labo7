import uuid
from django.db import models


class Produit(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=100)
    categorie = models.CharField(max_length=100)
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    # quantite_stock supprimé - n'appartient pas au domaine Catalogue (c'est du domaine Inventaire)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nom

    class Meta:
        db_table = "produits"
        verbose_name = "Produit"
        verbose_name_plural = "Produits"
