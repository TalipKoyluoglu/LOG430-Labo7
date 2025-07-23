"""
Vue Gestion des Produits (ex-UC4)
Gestion et modification des produits via le service-catalogue DDD
"""

from django.shortcuts import render, redirect
from django.contrib import messages
import logging

# Import du client HTTP vers service-catalogue
from magasin.infrastructure.catalogue_client import CatalogueClient

logger = logging.getLogger(__name__)


def uc4_modifier_produit(request, produit_id):
    """
    Modifie un produit via l'API DDD du service-catalogue
    Récupère d'abord le produit, puis le modifie si c'est un POST
    """
    logger.info(f"[TEST LOG] Modification produit demandée - ID: {produit_id}")
    try:
        # Initialisation du client HTTP
        catalogue_client = CatalogueClient()

        # Récupération du produit
        produit_data = catalogue_client.obtenir_produit_par_id(produit_id)

        if not produit_data.get("success", False):
            messages.error(
                request,
                f"Produit introuvable: {produit_data.get('error', 'Erreur inconnue')}",
            )
            return redirect("lister_produits")

        produit = produit_data.get("produit", {})

        if request.method == "POST":
            # Extraction des données du formulaire
            nom = request.POST.get("nom")
            prix = request.POST.get("prix")
            description = request.POST.get("description")

            # Validation des données
            if not all([nom, prix, description]):
                messages.error(request, "Tous les champs sont obligatoires")
                return render(
                    request, "magasin/uc4_modifProduit.html", {"produit": produit}
                )

            try:
                prix_float = float(prix)
                if prix_float <= 0:
                    raise ValueError("Le prix doit être positif")
            except ValueError:
                messages.error(request, "Le prix doit être un nombre positif")
                return render(
                    request, "magasin/uc4_modifProduit.html", {"produit": produit}
                )

            # TODO: Appel à l'API DDD pour modifier le produit
            # Note: L'API DDD actuelle du service-catalogue ne semble pas avoir de endpoint de modification
            # Il faudrait probablement ajouter un AjouterProduitUseCase ou ModifierProduitUseCase

            # Pour l'instant, simulation de la modification
            messages.warning(
                request,
                "Modification de produit en cours d'implémentation dans l'API DDD",
            )
            logger.warning(
                f"Tentative de modification produit {produit_id}: nom={nom}, prix={prix}"
            )

            return redirect("modifier_produit", produit_id=produit_id)

        return render(request, "magasin/uc4_modifProduit.html", {"produit": produit})

    except Exception as e:
        logger.error(f"Erreur lors de la modification du produit {produit_id}: {e}")
        messages.error(request, "Erreur interne lors de la modification du produit")
        return redirect("lister_produits")


def uc4_lister_produits(request):
    """
    Liste tous les produits via l'API DDD du service-catalogue
    Utilise le Use Case: RechercherProduitsUseCase
    """
    logger.info("📦 Listing de tous les produits demandé")
    try:
        # Initialisation du client HTTP
        catalogue_client = CatalogueClient()

        # Récupération de tous les produits via recherche (sans critères = tous)
        produits_data = catalogue_client.rechercher_produits()

        # Debug: afficher la structure des données
        logger.info(f"Réponse API catalogue: {produits_data}")

        if not produits_data.get("success", False):
            # En cas d'erreur API, afficher un message et des données vides
            messages.error(
                request,
                f"Erreur lors de la récupération des produits: {produits_data.get('error', 'Erreur inconnue')}",
            )
            return render(
                request,
                "magasin/uc4_liste.html",
                {
                    "produits": [],
                    "error_message": produits_data.get("error", "Service indisponible"),
                },
            )

        # Extraction des produits - l'API retourne {"success": true, "data": {"produits": [...]}}
        produits = produits_data.get("data", {}).get("produits", [])

        # Debug: afficher le nombre de produits
        logger.info(f"Produits extraits: {len(produits)} produits")
        if produits:
            logger.info(f"Premier produit: {produits[0]}")

        # Statistiques pour l'affichage
        stats = {
            "total_produits": len(produits),
            "prix_moyen": (
                sum(p.get("prix", 0) for p in produits) / len(produits)
                if produits
                else 0
            ),
            "produits_chers": len([p for p in produits if p.get("prix", 0) > 50]),
        }

        logger.info(f"Produits listés avec succès: {len(produits)} produits")

        return render(
            request,
            "magasin/uc4_liste.html",
            {
                "produits": produits,
                "stats": stats,
                "success_message": "Catalogue de produits chargé avec succès",
            },
        )

    except Exception as e:
        logger.error(f"Erreur lors du listage des produits: {e}")
        messages.error(request, "Erreur interne lors du chargement des produits")
        return render(
            request,
            "magasin/uc4_liste.html",
            {"produits": [], "error_message": "Erreur interne du serveur"},
        )


def rechercher_produits(request):
    """
    Recherche de produits avec critères via l'API DDD du service-catalogue
    Utilise le Use Case: RechercherProduitsUseCase
    """
    logger.info("🔍 Recherche de produits avec critères")
    try:
        # Extraction des critères de recherche
        nom = request.GET.get("nom", "")
        prix_min = request.GET.get("prix_min", "")
        prix_max = request.GET.get("prix_max", "")

        # Initialisation du client HTTP
        catalogue_client = CatalogueClient()

        # Préparation des critères de recherche
        criteres = {}
        if nom:
            criteres["nom"] = nom
        if prix_min:
            try:
                criteres["prix_min"] = float(prix_min)
            except ValueError:
                messages.warning(request, "Prix minimum invalide, ignoré")
        if prix_max:
            try:
                criteres["prix_max"] = float(prix_max)
            except ValueError:
                messages.warning(request, "Prix maximum invalide, ignoré")

        # Appel à l'API DDD de recherche
        produits_data = catalogue_client.rechercher_produits(criteres)

        if not produits_data.get("success", False):
            messages.error(
                request,
                f"Erreur lors de la recherche: {produits_data.get('error', 'Erreur inconnue')}",
            )
            return render(
                request,
                "magasin/uc4_recherche.html",
                {"produits": [], "criteres": criteres},
            )

        # Extraction des résultats
        produits = produits_data.get("produits", [])

        logger.info(
            f"Recherche effectuée avec succès: {len(produits)} résultats pour {criteres}"
        )

        return render(
            request,
            "magasin/uc4_recherche.html",
            {
                "produits": produits,
                "criteres": criteres,
                "nb_resultats": len(produits),
                "success_message": f"{len(produits)} produit(s) trouvé(s)",
            },
        )

    except Exception as e:
        logger.error(f"Erreur lors de la recherche de produits: {e}")
        messages.error(request, "Erreur interne lors de la recherche")
        return render(
            request,
            "magasin/uc4_recherche.html",
            {
                "produits": [],
                "criteres": {},
                "error_message": "Erreur interne du serveur",
            },
        )


def uc4_ajouter_produit(request):
    """
    Ajoute un nouveau produit via l'API DDD du service-catalogue
    """
    logger.info("➕ Ajout d'un nouveau produit")
    try:
        if request.method == "POST":
            nom = request.POST.get("nom")
            prix = request.POST.get("prix")
            description = request.POST.get("description")
            categorie = request.POST.get("categorie")
            if not all([nom, prix, description, categorie]):
                messages.error(request, "Tous les champs sont obligatoires")
                return render(request, "magasin/uc4_ajoutProduit.html")
            try:
                prix_float = float(prix)
                if prix_float <= 0:
                    raise ValueError("Le prix doit être positif")
            except ValueError:
                messages.error(request, "Le prix doit être un nombre positif")
                return render(request, "magasin/uc4_ajoutProduit.html")
            # Appel à l'API DDD pour ajouter le produit
            catalogue_client = CatalogueClient()
            # LOG: afficher le payload envoyé
            logger.error(
                f"Payload envoyé à ajouter_produit: nom={nom}, categorie={categorie}, prix={prix_float}, description={description}"
            )
            result = catalogue_client.ajouter_produit(
                nom, categorie, prix_float, description
            )
            # LOG: afficher la réponse d'erreur si échec
            if not result.get("success", False):
                logger.error(f"Réponse erreur du service catalogue: {result}")
            if result.get("success", False):
                messages.success(request, "Produit ajouté avec succès")
                return redirect("lister_produits")
            else:
                messages.error(
                    request,
                    f"Erreur lors de l'ajout du produit: {result.get('error', 'Erreur inconnue')}",
                )
                return render(request, "magasin/uc4_ajoutProduit.html")
        return render(request, "magasin/uc4_ajoutProduit.html")
    except Exception as e:
        logger.error(f"Erreur lors de l'ajout du produit: {e}")
        messages.error(request, "Erreur interne lors de l'ajout du produit")
        return render(request, "magasin/uc4_ajoutProduit.html")
