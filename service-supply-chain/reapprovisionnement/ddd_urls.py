"""
URLs DDD - Routes pour les Use Cases Réapprovisionnement
Routes orientées métier plutôt que CRUD.
"""

from django.urls import path
from .interfaces.ddd_views import (
    DDDDemandesEnAttenteAPI,
    DDDValiderDemandeAPI,
    DDDRejeterDemandeAPI,
)

urlpatterns = [
    # Use Case : Lister les demandes en attente
    path(
        "demandes-en-attente/",
        DDDDemandesEnAttenteAPI.as_view(),
        name="ddd-demandes-en-attente",
    ),
    # Use Case : Valider une demande
    path(
        "valider-demande/<str:demande_id>/",
        DDDValiderDemandeAPI.as_view(),
        name="ddd-valider-demande",
    ),
    # Use Case : Rejeter une demande
    path(
        "rejeter-demande/<str:demande_id>/",
        DDDRejeterDemandeAPI.as_view(),
        name="ddd-rejeter-demande",
    ),
]

"""
Comparaison des architectures:

CRUD (ancien):
- GET /demandes/?statut=En attente     → Service technique (filtrage SQL)
- POST /valider/{id}/                  → Orchestration procédurale dans views
- POST /rejeter/{id}/                  → Logique technique sans validation métier

DDD (nouveau):
- GET /api/ddd/supply-chain/demandes-en-attente/      → ListerDemandesUseCase
- POST /api/ddd/supply-chain/valider-demande/{id}/    → ValiderDemandeUseCase (workflow)
- POST /api/ddd/supply-chain/rejeter-demande/{id}/    → RejeterDemandeUseCase

Avantages DDD:
 Use Cases métier explicites
 Workflow orchestré avec rollback automatique
 Entités riches avec règles métier
 Value Objects avec validation intégrée
 Gestion d'erreurs spécifique au domaine
 Testabilité améliorée (injection de dépendances)
"""
