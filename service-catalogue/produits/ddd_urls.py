"""
URLs DDD pour le service Catalogue
Nouvelles routes orientées Use Cases métier
"""

from django.urls import path
from .interfaces.catalogue_views import (
    DDDCatalogueAPI,
    catalogue_health_check,
    get_produit_by_id,
)

app_name = "catalogue_ddd"

urlpatterns = [
    # Health Check DDD
    path("health/", catalogue_health_check, name="health-check"),
    # API Catalogue DDD - Orchestration des Use Cases
    path("rechercher/", DDDCatalogueAPI.as_view(), name="rechercher-produits"),
    path("ajouter/", DDDCatalogueAPI.as_view(), name="ajouter-produit"),
    # Récupération d'un produit par ID (pour communication inter-services)
    path("produits/<uuid:produit_id>/", get_produit_by_id, name="get-produit-by-id"),
]
