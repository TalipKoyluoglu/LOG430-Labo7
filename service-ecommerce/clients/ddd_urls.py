"""
URLs DDD pour le module Clients E-commerce
"""

from django.urls import path
from rest_framework.routers import DefaultRouter
from .interfaces.ddd_views import DDDClientViewSet, ValiderClientView

# Router pour les ViewSets DDD
router = DefaultRouter()
router.register(r"", DDDClientViewSet, basename="clients-ddd")

# URLs patterns DDD
urlpatterns = [
    # Endpoint pour valider l'existence d'un client (service-commandes)
    path(
        "<uuid:client_id>/valider/",
        ValiderClientView.as_view(),
        name="valider-client-ddd",
    ),
] + router.urls

# Les URLs du router incluent automatiquement :
# POST /api/clients/ - Créer un compte client (Use Case DDD)
# GET /api/clients/{id}/valider/ - Valider client pour commande
