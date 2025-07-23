"""
Vue Rapport Consolidé (ex-UC1)
Génère le rapport consolidé des ventes via le service-commandes DDD
"""

from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.contrib import messages
import logging

# Import du client HTTP vers service-commandes
from magasin.infrastructure.commandes_client import CommandesClient
from magasin.infrastructure.catalogue_client import CatalogueClient
from magasin.infrastructure.inventaire_client import InventaireClient

logger = logging.getLogger(__name__)


def rapport_ventes(request):
    """
    Vue principale pour le rapport consolidé des ventes
    Utilise l'API DDD du service-commandes : GenererRapportConsolideUseCase
    """
    logger.info("📊 Génération rapport consolidé des ventes demandée")
    try:
        # Initialisation du client HTTP
        commandes_client = CommandesClient()

        # Appel à l'API DDD pour générer le rapport consolidé
        rapport_data = commandes_client.generer_rapport_consolide()

        # Gestion du cas où l'API retourne une liste directement
        if isinstance(rapport_data, list):
            # Si c'est une liste, on la traite comme des données de rapport
            rapports_formatted = []
            for item in rapport_data:
                if isinstance(item, dict):
                    rapports_formatted.append(
                        {
                            "magasin": item.get("magasin", "Magasin inconnu"),
                            "total": item.get("total", 0),
                            "produits_vendus": item.get("produits_vendus", {}),
                            "stock_local": item.get("stock_local", {}),
                            "nombre_ventes": item.get("nombre_ventes", 0),
                            "performance": item.get("performance", "N/A"),
                        }
                    )
        elif not rapport_data.get("success", False):
            # En cas d'erreur API, afficher un message et des données vides
            messages.error(
                request,
                f"Erreur lors de la génération du rapport: {rapport_data.get('error', 'Erreur inconnue')}",
            )
            return render(
                request,
                "magasin/uc1_rapport.html",
                {
                    "rapports": [],
                    "error_message": rapport_data.get("error", "Service indisponible"),
                },
            )
        else:
            # Extraction des données du rapport
            rapport = rapport_data.get("rapport", {})

            # Transformation des données pour l'affichage (si nécessaire)
            rapports_formatted = []
            if isinstance(rapport, dict):
                # Si le rapport contient des données par magasin
                for magasin_data in rapport.get("magasins", []):
                    rapports_formatted.append(
                        {
                            "magasin": magasin_data.get("nom", "Magasin inconnu"),
                            "total": magasin_data.get("chiffre_affaires", 0),
                            "produits_vendus": magasin_data.get("produits_vendus", {}),
                            "stock_local": magasin_data.get("stocks_locaux", {}),
                            "nombre_ventes": magasin_data.get("nombre_ventes", 0),
                            "performance": magasin_data.get("performance", "N/A"),
                        }
                    )

        logger.info(
            f"Rapport consolidé généré avec succès: {len(rapports_formatted)} magasins"
        )

        return render(
            request,
            "magasin/uc1_rapport.html",
            {
                "rapports": rapports_formatted,
                "rapport_complet": rapport_data,
                "success_message": "Rapport consolidé généré avec succès",
            },
        )

    except Exception as e:
        logger.error(f"Erreur lors de la génération du rapport consolidé: {e}")
        messages.error(request, "Erreur interne lors de la génération du rapport")
        return render(
            request,
            "magasin/uc1_rapport.html",
            {"rapports": [], "error_message": "Erreur interne du serveur"},
        )


def afficher_formulaire_vente(request):
    """
    Affiche le formulaire pour enregistrer une nouvelle vente
    Récupère les données nécessaires via les APIs DDD
    """
    logger.info("📝 Affichage formulaire de nouvelle vente")
    try:
        # Récupérer la liste des magasins via le service-commandes
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

        # Déterminer le magasin sélectionné
        magasin_id = request.GET.get("magasin_id") or request.POST.get("magasin_id")
        produits = []
        quantites = {}
        if magasin_id:
            # Récupérer les produits en stock pour ce magasin
            inventaire_client = InventaireClient()
            stocks_data = inventaire_client.lister_stocks_locaux_magasin(magasin_id)
            logger.info(f"STOCKS LOCAUX POUR {magasin_id}: {stocks_data}")
            for stock in stocks_data.get("stocks", []):
                produits.append(
                    {
                        "id": stock.get("produit_id"),
                        "nom": stock.get("nom_produit"),
                    }
                )
                quantites[stock.get("produit_id")] = stock.get("quantite", 0)
        # Si aucun magasin sélectionné, pas de produits

        # Récupérer aussi les rapports pour l'affichage (comme attendu par le template)
        rapport_data = commandes_client.generer_rapport_consolide()
        rapports = []
        if isinstance(rapport_data, list):
            for item in rapport_data:
                if isinstance(item, dict):
                    rapports.append(
                        {
                            "magasin": item.get("magasin", "Magasin inconnu"),
                            "total": item.get("total", 0),
                            "produits_vendus": item.get("produits_vendus", {}),
                            "stock_local": item.get("stock_local", {}),
                            "nombre_ventes": item.get("nombre_ventes", 0),
                            "performance": item.get("performance", "N/A"),
                        }
                    )
        elif rapport_data.get("success", False):
            rapport = rapport_data.get("rapport", {})
            if isinstance(rapport, dict):
                for magasin_data in rapport.get("magasins", []):
                    rapports.append(
                        {
                            "magasin": magasin_data.get("nom", "Magasin inconnu"),
                            "total": magasin_data.get("chiffre_affaires", 0),
                            "produits_vendus": magasin_data.get("produits_vendus", {}),
                            "stock_local": magasin_data.get("stocks_locaux", {}),
                            "nombre_ventes": magasin_data.get("nombre_ventes", 0),
                            "performance": magasin_data.get("performance", "N/A"),
                        }
                    )

        # Section informative : liste des stocks par magasin (pour affichage, toujours alimentée)
        magasins_avec_stocks = []
        for magasin in magasins:
            stocks_data = InventaireClient().lister_stocks_locaux_magasin(magasin["id"])
            produits_stock = stocks_data.get("stocks", [])
            magasins_avec_stocks.append(
                {"nom": magasin["nom"], "produits": produits_stock}
            )

        context = {
            "produits": produits,
            "magasins": magasins,
            "rapports": rapports,
            "form_available": bool(produits and magasins),
            "magasin_id": magasin_id,
            "quantites": quantites,
            "magasins_avec_stocks": magasins_avec_stocks,
        }
        logger.info(f"MAGASINS POUR TEMPLATE: {magasins}")
        logger.info(
            f"DEBUG VENTE: magasin_id={magasin_id}, produits={produits}, quantites={quantites}"
        )
        return render(request, "magasin/effectuerVente.html", context)
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage du formulaire de vente: {e}")
        messages.error(request, "Erreur lors du chargement du formulaire")
        return redirect("rapport_consolide")


@require_http_methods(["POST", "GET"])
def enregistrer_vente(request):
    """
    Enregistre une nouvelle vente via l'API DDD du service-commandes
    Utilise le Use Case: EnregistrerVenteUseCase
    """
    logger.info("💰 Enregistrement d'une nouvelle vente")
    if request.method == "GET":
        logger.error("❌ Accès direct interdit pour enregistrer vente")
        messages.error(
            request, "Accès direct interdit. Veuillez utiliser le formulaire."
        )
        return redirect("ajouter_vente")

    try:
        # Extraction des données du formulaire
        magasin_id = request.POST.get("magasin_id")
        produit_id = request.POST.get("produit_id")
        quantite = int(request.POST.get("quantite", 0))
        client_id = request.POST.get("client_id")  # Optionnel désormais
        # Si aucun client_id n'est fourni, utiliser un UUID bidon
        if not client_id:
            client_id = "00000000-0000-0000-0000-000000000000"

        # Validation des données (client_id non requis)
        if not all([magasin_id, produit_id, quantite > 0]):
            messages.error(
                request,
                "Tous les champs sont obligatoires (magasin, produit, quantité)",
            )
            return redirect("ajouter_vente")

        # Initialisation du client HTTP
        commandes_client = CommandesClient()

        # Appel à l'API DDD pour enregistrer la vente
        vente_result = commandes_client.enregistrer_vente(
            magasin_id=magasin_id,
            produit_id=produit_id,
            quantite=quantite,
            client_id=client_id,  # Peut être None ou vide
        )

        if vente_result.get("success", False):
            messages.success(
                request, "Vente enregistrée avec succès via le service DDD"
            )
            logger.info(
                f"Vente enregistrée: magasin={magasin_id}, produit={produit_id}, quantité={quantite}"
            )
        else:
            error_msg = vente_result.get(
                "error", "Erreur inconnue lors de l'enregistrement"
            )
            messages.error(request, f"Échec de l'enregistrement: {error_msg}")
            logger.warning(f"Échec enregistrement vente: {error_msg}")

        return redirect("rapport_consolide")

    except ValueError as e:
        messages.error(request, "Données invalides: quantité doit être un nombre")
        logger.error(f"Erreur de validation: {e}")
        return redirect("ajouter_vente")

    except Exception as e:
        messages.error(request, "Erreur interne lors de l'enregistrement de la vente")
        logger.error(f"Erreur lors de l'enregistrement de la vente: {e}")
        return redirect("ajouter_vente")
