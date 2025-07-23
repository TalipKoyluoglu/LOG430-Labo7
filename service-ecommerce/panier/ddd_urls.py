"""
URLs du module Panier - API REST DDD
Routes pour la gestion du panier d'achat e-commerce
"""

from django.urls import path
from .interfaces.ddd_views import PanierView, PanierProduitView

urlpatterns = [
    # API Panier complet
    path(
        "clients/<uuid:client_id>/panier/", PanierView.as_view(), name="panier-detail"
    ),
    # API Produit spécifique dans le panier
    path(
        "clients/<uuid:client_id>/panier/produits/<uuid:produit_id>/",
        PanierProduitView.as_view(),
        name="panier-produit",
    ),
]
