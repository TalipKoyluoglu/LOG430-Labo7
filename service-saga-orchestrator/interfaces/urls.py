"""
URLs pour l'API Saga Orchestrator
"""

from django.urls import path
from . import saga_api

app_name = "saga"

urlpatterns = [
    # API principale pour les sagas
    path(
        "api/saga/commandes/",
        saga_api.demarrer_saga_commande,
        name="demarrer_saga_commande"
    ),
    path(
        "api/saga/commandes/<str:saga_id>/",
        saga_api.consulter_saga,
        name="consulter_saga"
    ),
    path(
        "api/saga/commandes/<str:saga_id>/compenser/",
        saga_api.forcer_compensation_saga,
        name="forcer_compensation_saga"
    ),
    path(
        "api/saga/sagas/",
        saga_api.lister_sagas,
        name="lister_sagas"
    ),
    
    # API de test
    path(
        "api/saga/test/echec-stock/",
        saga_api.simuler_echec_stock,
        name="simuler_echec_stock"
    ),
    
    # Utilitaires
    path(
        "api/saga/health/",
        saga_api.health_check,
        name="health_check"
    ),
    path(
        "api/saga/info/",
        saga_api.api_info,
        name="api_info"
    ),
    
    # Métriques Prometheus
    path(
        "metrics/",
        saga_api.metrics,
        name="prometheus_metrics"
    ),
] 