"""
Configuration de l'interface d'administration pour les clients
"""

from django.contrib import admin
from .models import ClientModel


@admin.register(ClientModel)
class ClientAdmin(admin.ModelAdmin):
    """
    Configuration de l'administration des clients
    """

    list_display = [
        "nom_complet_display",
        "email",
        "adresse_ville",
        "actif",
        "date_creation",
    ]
    list_filter = ["actif", "adresse_province", "date_creation"]
    search_fields = ["prenom", "nom", "email", "adresse_ville"]
    readonly_fields = ["id", "date_creation", "date_modification"]

    fieldsets = (
        (
            "Informations personnelles",
            {"fields": ("prenom", "nom", "email", "telephone")},
        ),
        (
            "Adresse",
            {
                "fields": (
                    "adresse_rue",
                    "adresse_ville",
                    "adresse_code_postal",
                    "adresse_province",
                    "adresse_pays",
                )
            },
        ),
        (
            "Métadonnées",
            {
                "fields": ("id", "actif", "date_creation", "date_modification"),
                "classes": ("collapse",),
            },
        ),
    )

    def nom_complet_display(self, obj):
        return f"{obj.prenom} {obj.nom}"

    nom_complet_display.short_description = "Nom complet"
