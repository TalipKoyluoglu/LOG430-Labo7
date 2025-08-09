"""
URLs DDD pour le module Commandes Check-out E-commerce
"""

from django.urls import path
from .views import (
    checkout_ecommerce,
    verifier_prerequis_checkout,
    historique_commandes_client,
    checkout_ecommerce_choreo,
)

urlpatterns = [
    # API principale de check-out e-commerce
    path(
        "clients/<uuid:client_id>/checkout/",
        checkout_ecommerce,
        name="checkout-ecommerce",
    ),
    # Variante chorégraphiée (publie uniquement l'initiation et laisse les consommateurs orchestrer)
    path(
        "clients/<uuid:client_id>/checkout/choreo/",
        checkout_ecommerce_choreo,
        name="checkout-ecommerce-choreo",
    ),
    # API de vérification des prérequis pour check-out
    path(
        "clients/<uuid:client_id>/checkout/prerequis/",
        verifier_prerequis_checkout,
        name="verifier-prerequis-checkout",
    ),
    # API d'historique des commandes client
    path(
        "clients/<uuid:client_id>/historique/",
        historique_commandes_client,
        name="historique-commandes-client",
    ),
]
