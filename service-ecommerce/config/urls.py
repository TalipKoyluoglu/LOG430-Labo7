"""
URL configuration for service-ecommerce project - Architecture DDD
"""

from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.http import JsonResponse, HttpResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Configuration Swagger/OpenAPI
schema_view = get_schema_view(
    openapi.Info(
        title="Service E-commerce API",
        default_version="v1",
        description="API REST pour le service e-commerce avec architecture DDD microservices",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@ecommerce.local"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    # Redirection racine vers Swagger
    path("", lambda request: redirect("schema-swagger-ui", permanent=False)),
    # Administration Django
    path("admin/", admin.site.urls),
    # Documentation API
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    path("swagger.json", schema_view.without_ui(cache_timeout=0), name="schema-json"),
    # APIs DDD des modules e-commerce
    path("api/clients/", include("clients.ddd_urls")),
    path("api/panier/", include("panier.ddd_urls")),
    path("api/commandes/", include("commandes.ddd_urls")),
    # Prometheus metrics
    path("metrics", lambda request: HttpResponse(generate_latest(), content_type=CONTENT_TYPE_LATEST)),
    # Health check
    path(
        "health/",
        lambda request: JsonResponse(
            {
                "status": "healthy",
                "service": "ecommerce-ddd",
                "modules": ["clients", "panier", "commandes"],
            }
        ),
    ),
]
