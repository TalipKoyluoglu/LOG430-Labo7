"""
Vue Indicateurs de Performance (ex-UC3)
Dashboard principal avec indicateurs de performance via le service-commandes DDD
"""

from django.shortcuts import render
from django.contrib import messages
import logging

# Import du client HTTP vers service-commandes
from magasin.infrastructure.commandes_client import CommandesClient

logger = logging.getLogger(__name__)


def uc3_dashboard(request):
    """
    Dashboard principal avec indicateurs de performance par magasin
    Utilise l'API DDD du service-commandes : GenererIndicateursUseCase
    """
    logger.info("📈 Accès au dashboard des indicateurs de performance")
    try:
        # Initialisation du client HTTP
        commandes_client = CommandesClient()

        # Appel à l'API DDD pour générer les indicateurs
        indicateurs_data = commandes_client.generer_indicateurs()

        # Gestion du cas où l'API retourne une liste directement
        if isinstance(indicateurs_data, list):
            indicateurs = [ind for ind in indicateurs_data if isinstance(ind, dict)]
        elif not indicateurs_data.get("success", False):
            # En cas d'erreur API, afficher un message et des données vides
            messages.error(
                request,
                f"Erreur lors de la génération des indicateurs: {indicateurs_data.get('error', 'Erreur inconnue')}",
            )
            return render(
                request,
                "magasin/uc3_dashboard.html",
                {
                    "indicateurs": [],
                    "error_message": indicateurs_data.get(
                        "error", "Service indisponible"
                    ),
                },
            )
        else:
            # Extraction des indicateurs
            indicateurs = indicateurs_data.get("indicateurs", [])

        # Calculs supplémentaires pour le dashboard
        stats_globales = {
            "total_magasins": len(indicateurs),
            "chiffre_affaires_total": sum(
                ind.get("chiffre_affaires", 0) for ind in indicateurs
            ),
            "total_ruptures": sum(ind.get("ruptures", 0) for ind in indicateurs),
            "total_surstock": sum(ind.get("surstock", 0) for ind in indicateurs),
        }

        # Identification des magasins avec alertes
        magasins_alertes = [
            ind
            for ind in indicateurs
            if ind.get("ruptures", 0) > 0 or ind.get("surstock", 0) > 2
        ]

        # Magasins les plus performants (par chiffre d'affaires)
        top_magasins = sorted(
            indicateurs, key=lambda x: x.get("chiffre_affaires", 0), reverse=True
        )[:3]

        logger.info(
            f"Dashboard généré avec succès: {len(indicateurs)} magasins, CA total: {stats_globales['chiffre_affaires_total']}"
        )

        return render(
            request,
            "magasin/uc3_dashboard.html",
            {
                "indicateurs": indicateurs,
                "stats_globales": stats_globales,
                "magasins_alertes": magasins_alertes,
                "top_magasins": top_magasins,
                "success_message": "Indicateurs de performance mis à jour",
            },
        )

    except Exception as e:
        logger.error(f"Erreur lors de la génération du dashboard: {e}")
        messages.error(request, "Erreur interne lors de la génération du dashboard")
        return render(
            request,
            "magasin/uc3_dashboard.html",
            {
                "indicateurs": [],
                "stats_globales": {
                    "total_magasins": 0,
                    "chiffre_affaires_total": 0,
                    "total_ruptures": 0,
                    "total_surstock": 0,
                },
                "error_message": "Erreur interne du serveur",
            },
        )
