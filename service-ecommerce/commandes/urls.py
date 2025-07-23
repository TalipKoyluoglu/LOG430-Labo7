"""
URLs pour le module Check-out E-commerce
"""

from django.urls import path
from . import views

urlpatterns = [
    # API principale de check-out
    path(
        "clients/<uuid:client_id>/checkout/",
        views.checkout_ecommerce,
        name="checkout_ecommerce",
    ),
    # Vérification des prérequis pour check-out
    path(
        "clients/<uuid:client_id>/checkout/prerequis/",
        views.verifier_prerequis_checkout,
        name="verifier_prerequis_checkout",
    ),
]
