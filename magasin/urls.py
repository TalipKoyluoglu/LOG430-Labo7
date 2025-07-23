from django.urls import path
from django.views.generic.base import RedirectView

# Imports avec nouveaux noms de fichiers
from magasin.views.rapport_consolide import (
    rapport_ventes,
    afficher_formulaire_vente,
    enregistrer_vente,
)
from magasin.views.gestion_stock import uc2_stock, uc2_reapprovisionner
from magasin.views.indicateurs_performance import uc3_dashboard
from magasin.views.gestion_produits import (
    uc4_lister_produits,
    uc4_modifier_produit,
    uc4_ajouter_produit,
)
from magasin.views.workflow_demandes import uc6_demandes, uc6_rejeter, uc6_valider

urlpatterns = [
    # Page d'accueil - Dashboard principal (indicateurs de performance)
    path("", uc3_dashboard, name="home"),
    # Rapport consolidé des ventes (ex-UC1)
    path("rapport-consolide/", rapport_ventes, name="rapport_consolide"),
    path("ventes/ajouter/", afficher_formulaire_vente, name="ajouter_vente"),
    path("ventes/enregistrer/", enregistrer_vente, name="enregistrer_vente"),
    # Gestion des stocks et réapprovisionnement (ex-UC2)
    path("stocks/", uc2_stock, name="gestion_stocks"),
    path("stocks/reapprovisionner/", uc2_reapprovisionner, name="reapprovisionner"),
    # Indicateurs de performance (ex-UC3)
    path("indicateurs/", uc3_dashboard, name="indicateurs_performance"),
    # Gestion des produits (ex-UC4)
    path("produits/", uc4_lister_produits, name="lister_produits"),
    path(
        "produits/modifier/<str:produit_id>/",
        uc4_modifier_produit,
        name="modifier_produit",
    ),
    path("produits/ajouter/", uc4_ajouter_produit, name="ajouter_produit"),
    # Workflow de validation des demandes (ex-UC6)
    path("demandes/", uc6_demandes, name="workflow_demandes"),
    path("demandes/valider/<uuid:demande_id>/", uc6_valider, name="valider_demande"),
    path("demandes/rejeter/<uuid:demande_id>/", uc6_rejeter, name="rejeter_demande"),
]
