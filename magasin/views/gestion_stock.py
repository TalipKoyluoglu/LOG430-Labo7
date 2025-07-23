"""
Vue Gestion des Stocks (ex-UC2)
Gestion des stocks et demandes de réapprovisionnement via le service-inventaire DDD
"""

from django.shortcuts import render, redirect
from django.contrib import messages
import logging

# Import du client HTTP vers service-inventaire
from magasin.infrastructure.inventaire_client import InventaireClient
from magasin.infrastructure.commandes_client import CommandesClient

logger = logging.getLogger(__name__)


def uc2_stock(request):
    """
    Affiche l'état des stocks centraux et permet de gérer les réapprovisionnements
    Utilise l'API DDD du service-inventaire : ConsulterStocksCentralUseCase
    """
    logger.info("🏪 Consultation des stocks centraux demandée")
    try:
        # Initialisation du client HTTP
        inventaire_client = InventaireClient()

        # Récupération des stocks centraux via l'API DDD
        stocks_data = inventaire_client.lister_stocks_centraux()

        if not stocks_data.get("success", False):
            # En cas d'erreur API, afficher un message et des données vides
            logger.error(
                "❌ Échec récupération stocks: %s",
                stocks_data.get("error", "Erreur inconnue"),
            )
            messages.error(
                request,
                f"Erreur lors de la récupération des stocks: {stocks_data.get('error', 'Erreur inconnue')}",
            )
            return render(
                request,
                "magasin/uc2_stock.html",
                {
                    "stocks": [],
                    "magasins": [],
                    "error_message": stocks_data.get("error", "Service indisponible"),
                },
            )

        # Extraction des stocks
        stocks = stocks_data.get("stocks", [])

        # Récupération des magasins (pour les demandes de réapprovisionnement)
        # Utilisation du client HTTP Commandes pour la vraie liste
        commandes_client = CommandesClient()
        magasins_data = (
            commandes_client.lister_magasins()
            if hasattr(commandes_client, "lister_magasins")
            else None
        )
        if magasins_data and magasins_data.get("success"):
            magasins = magasins_data.get("magasins", [])
        else:
            magasins = []

        # Identification des stocks faibles (seuil d'alerte : < 10)
        stocks_faibles = [stock for stock in stocks if stock.get("quantite", 0) < 10]

        # Statistiques pour l'affichage
        stats = {
            "total_produits": len(stocks),
            "stocks_faibles": len(stocks_faibles),
            "valeur_totale": sum(
                stock.get("quantite", 0) * stock.get("prix_unitaire", 0)
                for stock in stocks
            ),
        }

        logger.info(
            f"Stocks consultés avec succès: {len(stocks)} produits, {len(stocks_faibles)} en stock faible"
        )

        return render(
            request,
            "magasin/uc2_stock.html",
            {
                "stocks": stocks,
                "stocks_faibles": stocks_faibles,
                "magasins": magasins,
                "stats": stats,
                "success_message": "Stocks centraux consultés avec succès",
            },
        )

    except Exception as e:
        logger.error(f"Erreur lors de la consultation des stocks: {e}")
        messages.error(request, "Erreur interne lors de la consultation des stocks")
        return render(
            request,
            "magasin/uc2_stock.html",
            {
                "stocks": [],
                "magasins": [],
                "error_message": "Erreur interne du serveur",
            },
        )


def uc2_reapprovisionner(request):
    """
    Crée une demande de réapprovisionnement via l'API DDD du service-inventaire
    Utilise le Use Case: CreerDemandeReapprovisionnementUseCase
    """
    logger.info("🔄 Demande de réapprovisionnement initiée")
    if request.method != "POST":
        logger.error("❌ Méthode non autorisée pour réapprovisionnement")
        messages.error(request, "Méthode non autorisée")
        return redirect("gestion_stocks")

    try:
        # Extraction des données du formulaire
        produit_id = request.POST.get("produit_id")
        magasin_id = request.POST.get("magasin_id")
        quantite = int(request.POST.get("quantite", 0))
        logger.info(
            f"DEMANDE REAPPRO: produit_id={produit_id}, magasin_id={magasin_id}, quantite={quantite}"
        )

        # Validation des données
        if not all([produit_id, magasin_id, quantite > 0]):
            messages.error(
                request,
                "Tous les champs sont obligatoires (produit, magasin, quantité > 0)",
            )
            return redirect("gestion_stocks")

        # Initialisation du client HTTP
        inventaire_client = InventaireClient()

        # Appel à l'API DDD pour créer la demande de réapprovisionnement
        demande_result = inventaire_client.creer_demande_reapprovisionnement(
            produit_id=produit_id, magasin_id=magasin_id, quantite=quantite
        )

        logger.info(f"RÉPONSE CRÉATION DEMANDE: {demande_result}")
        if (
            demande_result.get("success", False)
            or demande_result.get("id")
            or demande_result.get("demande_id")
        ):
            demande_id = demande_result.get("id") or demande_result.get(
                "demande_id", "N/A"
            )
            messages.success(
                request,
                f"Demande de réapprovisionnement créée avec succès (ID: {demande_id})",
            )
            logger.info(
                f"Demande de réapprovisionnement créée: produit={produit_id}, magasin={magasin_id}, quantité={quantite}"
            )
        else:
            error_msg = demande_result.get(
                "error", "Erreur inconnue lors de la création"
            )
            if "déjà en attente" in error_msg or "déja en attente" in error_msg:
                messages.info(
                    request,
                    "Une demande de réapprovisionnement pour ce produit et ce magasin est déjà en attente. Veuillez la traiter avant d'en créer une nouvelle.",
                )
            else:
                messages.error(
                    request, f"Échec de la création de la demande: {error_msg}"
                )
            logger.warning(f"Échec création demande réapprovisionnement: {error_msg}")

        return redirect("gestion_stocks")

    except ValueError as e:
        messages.error(request, "Données invalides: quantité doit être un nombre")
        logger.error(f"Erreur de validation: {e}")
        return redirect("gestion_stocks")

    except Exception as e:
        messages.error(request, "Erreur interne lors de la création de la demande")
        logger.error(
            f"Erreur lors de la création de la demande de réapprovisionnement: {e}"
        )
        return redirect("gestion_stocks")
