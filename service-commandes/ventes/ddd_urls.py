"""
URLs DDD - Routes pour les Use Cases
Nouvelles routes basées sur les fonctionnalités métier plutôt que sur les entités
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .interfaces.ddd_views import (
    DDDVenteViewSet,
    DDDIndicateursAPI,
    DDDRapportConsolideAPI,
    lister_magasins,
)

# Router pour les ViewSets DDD
router = DefaultRouter()
router.register(r"ventes-ddd", DDDVenteViewSet, basename="ventes-ddd")

urlpatterns = [
    # Routes des Use Cases DDD
    path("", include(router.urls)),
    # Endpoints spécifiques DDD
    path("indicateurs/", DDDIndicateursAPI.as_view(), name="indicateurs-ddd"),
    path(
        "rapport-consolide/",
        DDDRapportConsolideAPI.as_view(),
        name="rapport-consolide-ddd",
    ),
    # Endpoint pour lister les magasins
    path("magasins/", lister_magasins, name="lister-magasins-ddd"),
]

"""
Comparaison des architectures:

CRUD (ancien):
- POST /ventes/enregistrer/          → Service technique CRUD
- PATCH /ventes/{id}/annuler/        → Service technique CRUD  
- GET /indicateurs/magasins/         → Service technique CRUD

DDD (nouveau):
- POST /api/ddd/ventes-ddd/enregistrer/   → EnregistrerVenteUseCase
- PATCH /api/ddd/ventes-ddd/{id}/annuler/ → AnnulerVenteUseCase
- GET /api/ddd/indicateurs/               → GenererIndicateursUseCase
- GET /api/ddd/rapport-consolide/         → GenererRapportConsolideUseCase (UC1)

Avantages DDD:
✅ Logique métier centralisée dans les entités
✅ Use Cases orientés fonctionnalités (pas entités)
✅ Séparation claire domain/infrastructure
✅ Testabilité améliorée (mocking des services)
✅ Évolutivité (ajout facile de nouveaux use cases)
"""
