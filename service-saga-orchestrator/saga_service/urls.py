"""
Configuration des URLs principales pour le service Saga Orchestrator
"""

from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Configuration Swagger/OpenAPI
schema_view = get_schema_view(
    openapi.Info(
        title="Service Saga Orchestrator API",
        default_version="v1",
        description="""
        **Service Saga Orchestrator - Architecture DDD**
        
        Ce service implémente des Sagas orchestrées synchrones pour coordonner 
        les transactions distribuées entre microservices.
        
        **Architecture Saga :**
        • Orchestration centralisée et synchrone
        • Machine d'état explicite avec transitions contrôlées
        • Compensation automatique en cas d'échec
        • Observabilité complète avec métriques et logs
        
        **Workflow de commande orchestrée :**
        1. **Vérification du stock** (service-inventaire)
        2. **Réservation du stock** (service-inventaire)
        3. **Création de la commande** (service-commandes)
        4. **Confirmation** ou **Compensation automatique**
        
        **Services intégrés via Kong API Gateway :**
        • Service Catalogue (port 8001) : informations produits
        • Service Inventaire (port 8002) : gestion des stocks
        • Service Commandes (port 8003) : création des ventes
        
        **APIs principales :**
        • `POST /api/saga/commandes/` - Démarrer une saga de commande
        • `GET /api/saga/commandes/{saga_id}/` - Consulter le statut
        • `POST /api/saga/test/echec-stock/` - Simuler des échecs
        
        **Fonctionnalités avancées :**
        • Gestion des états : EN_ATTENTE → VERIFICATION_STOCK → STOCK_RESERVE → COMMANDE_CREEE → SAGA_TERMINEE
        • Compensation : Libération automatique du stock en cas d'échec
        • Observabilité : Métriques de durée, tentatives, et traçabilité complète
        """,
        terms_of_service="https://www.example.com/policies/terms/",
        contact=openapi.Contact(email="admin@lab430.ca"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


def redirect_to_swagger(request):
    """Redirection automatique vers Swagger UI"""
    return redirect("schema-swagger-ui")


urlpatterns = [
    # Administration Django
    path("admin/", admin.site.urls),
    
    # Redirection racine vers documentation
    path("", redirect_to_swagger, name="home"),
    
    # APIs Saga
    path("", include("interfaces.urls")),
    
    # Documentation Swagger/OpenAPI
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path(
        "redoc/",
        schema_view.with_ui("redoc", cache_timeout=0),
        name="schema-redoc"
    ),
    path(
        "swagger.json",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json"
    ),
] 