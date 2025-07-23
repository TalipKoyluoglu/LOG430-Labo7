"""
URL Configuration for service_ecommerce project.
"""

from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    # Django Admin
    path("admin/", admin.site.urls),
    # API Schema et Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    # Modules E-commerce
    path("api/clients/", include("clients.urls")),
    path("api/panier/", include("panier.urls")),
    path("api/commandes/", include("commandes.urls")),  # Module check-out e-commerce
]
