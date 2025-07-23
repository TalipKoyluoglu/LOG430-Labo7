"""
URLs DDD pour le service Stock (Inventaire)
Routes pour toutes les fonctionnalités métier en architecture DDD.
"""

from django.urls import path
from .interfaces import ddd_views

urlpatterns = [
    # Health Check
    path(
        "api/ddd/inventaire/health/", ddd_views.health_check, name="inventaire_health"
    ),
    # === GESTION DES STOCKS ===
    # Opérations sur les stocks
    path(
        "api/ddd/inventaire/augmenter-stock/",
        ddd_views.augmenter_stock,
        name="augmenter_stock_ddd",
    ),
    path(
        "api/ddd/inventaire/diminuer-stock/",
        ddd_views.diminuer_stock,
        name="diminuer_stock_ddd",
    ),
    # Consultation des stocks
    path(
        "api/ddd/inventaire/stock-central/<uuid:produit_id>/",
        ddd_views.consulter_stock_central,
        name="stock_central_ddd",
    ),
    path(
        "api/ddd/inventaire/stock-local/<uuid:produit_id>/<uuid:magasin_id>/",
        ddd_views.consulter_stock_local,
        name="stock_local_ddd",
    ),
    # Listing des stocks
    path(
        "api/ddd/inventaire/stocks-centraux/",
        ddd_views.lister_stocks_centraux,
        name="stocks_centraux_ddd",
    ),
    path(
        "api/ddd/inventaire/stocks-locaux/<uuid:magasin_id>/",
        ddd_views.lister_stocks_locaux_magasin,
        name="stocks_locaux_magasin_ddd",
    ),
    path(
        "api/ddd/inventaire/magasins-stocks/",
        ddd_views.lister_tous_magasins_avec_stocks,
        name="magasins_stocks_ddd",
    ),
    # === GESTION DES DEMANDES ===
    # Listing des demandes (ROUTES SPÉCIFIQUES EN PREMIER)
    path(
        "api/ddd/inventaire/demandes/en-attente/",
        ddd_views.lister_demandes_en_attente,
        name="demandes_en_attente_ddd",
    ),
    path(
        "api/ddd/inventaire/demandes/magasin/<uuid:magasin_id>/",
        ddd_views.lister_demandes_par_magasin,
        name="demandes_par_magasin_ddd",
    ),
    # Opérations sur les demandes (ROUTES GÉNÉRIQUES APRÈS)
    path(
        "api/ddd/inventaire/demandes/",
        ddd_views.creer_demande,
        name="creer_demande_ddd",
    ),
    path(
        "api/ddd/inventaire/demandes/<str:demande_id>/",
        ddd_views.obtenir_demande_par_id,
        name="obtenir_demande_ddd",
    ),
    path(
        "api/ddd/inventaire/demandes/<str:demande_id>/supprimer/",
        ddd_views.supprimer_demande,
        name="supprimer_demande_ddd",
    ),
    path(
        "api/ddd/inventaire/demandes/<str:demande_id>/approuver/",
        ddd_views.approuver_demande,
        name="approuver_demande_ddd",
    ),
    path(
        "api/ddd/inventaire/demandes/<str:demande_id>/rejeter/",
        ddd_views.rejeter_demande,
        name="rejeter_demande_ddd",
    ),
    # Analyse métier
    path(
        "api/ddd/inventaire/analyser-besoins/<uuid:magasin_id>/",
        ddd_views.analyser_besoins_reapprovisionnement,
        name="analyser_besoins_ddd",
    ),
]
