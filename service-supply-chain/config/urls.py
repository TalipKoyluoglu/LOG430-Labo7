"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include, re_path
from django.shortcuts import redirect
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Service Supply Chain DDD API",
        default_version="v1",
        description="""
        **Service Supply-Chain - Architecture Domain-Driven Design**
        
        Ce service gère le domaine métier "Workflow de Réapprovisionnement" avec une architecture DDD complète.
        
        **Bounded Context : "Supply Chain Management"**
        • Demandes de réapprovisionnement avec workflow de validation
        • Value Objects avec validation métier stricte  
        • Entités riches avec logique domaine
        • Use Cases orchestrant les processus métier
        
        **APIs DDD disponibles :**
        • `/api/ddd/supply-chain/` - APIs orientées métier
        • Workflow complet de validation des demandes
        • Gestion des exceptions domaine
        
        **Communication avec autres services :**
        • Service Catalogue : validation produits existants
        • Service Inventaire : orchestration stocks et demandes
        • Infrastructure Layer : Communication HTTP avec service-inventaire
        
        **Architecture DDD :**
        • Domain Layer : Entités WorkflowValidation, DemandeReapprovisionnement
        • Application Layer : Use Cases orchestrant les workflows complexes
        • Interface Layer : APIs REST orientées métier
        
        **Use Cases disponibles :**
        • ListerDemandesUseCase : Récupération avec règles métier
        • ValiderDemandeUseCase : Workflow 3 étapes + rollback automatique
        • RejeterDemandeUseCase : Rejet avec validation du motif
        
        **Workflow DDD de validation :**
        1. **Validation des règles métier** (entités riches)
        2. **Orchestration workflow** (3 étapes atomiques)
        3. **Rollback automatique** en cas d'échec
        4. **Gestion d'erreurs** spécifiques au domaine
        
        **Value Objects avec validation :**
        • DemandeId, ProduitId, MagasinId (UUID validés)
        • Quantite (règles métier : >0, <10000)
        • MotifRejet (minimum 5 caractères, validation contenu)
        """,
        terms_of_service="https://www.example.com/policies/terms/",
        contact=openapi.Contact(email="admin@lab430.ca"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


def redirect_to_swagger(request):
    """Redirection automatique vers Swagger"""
    return redirect("schema-swagger-ui")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", redirect_to_swagger, name="home"),  # Redirection automatique
    # 🎯 APIs DDD - Architecture Domain-Driven Design (SERVICE-SUPPLY-CHAIN)
    path("api/ddd/supply-chain/", include("reapprovisionnement.ddd_urls")),
    # Documentation Swagger
    re_path(
        r"^swagger(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    re_path(
        r"^swagger/$",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    re_path(
        r"^redoc/$", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"
    ),
]
