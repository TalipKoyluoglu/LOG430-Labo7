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
        title="Service Inventaire DDD API",
        default_version="v1",
        description="""
        **Service Inventaire - Architecture Domain-Driven Design**
        
        Ce service gère le domaine métier "Gestion Inventaire" avec une architecture DDD pure.
        
        **Bounded Context : "Gestion Inventaire"**
        • Stocks centraux et locaux avec règles métier riches
        • Demandes de réapprovisionnement avec workflow
        • Value Objects avec validation métier
        • Entités riches avec logique domaine
        
        **APIs DDD disponibles :**
        • `/api/ddd/inventaire/` - APIs orientées métier
        • Validation des règles métier automatique
        • Gestion des exceptions domaine
        
        **Communication avec autres services :**
        • Service Catalogue : validation produits existants
        • Service Supply-Chain : orchestration réapprovisionnement
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
    path("", include("stock.ddd_urls")),  # APIs DDD uniquement
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
