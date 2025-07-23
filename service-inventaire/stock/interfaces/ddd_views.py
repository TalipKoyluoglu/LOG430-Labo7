"""
Vues DDD pour le service Stock (Inventaire)
Orchestration des Use Cases pour toutes les fonctionnalités métier.
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.decorators import api_view
import json

from ..application.use_cases.gerer_stock_use_case import (
    GererStockUseCase,
    AugmenterStockRequest,
    DiminuerStockRequest,
)
from ..application.use_cases.gerer_demandes_use_case import (
    GererDemandesUseCase,
    CreerDemandeRequest,
)
from ..infrastructure.django_stock_repository import DjangoStockRepository
from ..infrastructure.django_demande_repository import DjangoDemandeRepository
from ..infrastructure.http_produit_service import HttpProduitService
from ..infrastructure.http_magasin_service import HttpMagasinService
from ..domain.exceptions import InventaireDomainError, StockInsuffisantError


# Injection de dépendances - Configuration des services
def _get_gerer_stock_use_case():
    """Factory pour créer le Use Case de gestion des stocks"""
    return GererStockUseCase(
        stock_repository=DjangoStockRepository(),
        demande_repository=DjangoDemandeRepository(),
        produit_service=HttpProduitService(),
        magasin_service=HttpMagasinService(),
    )


def _get_gerer_demandes_use_case():
    """Factory pour créer le Use Case de gestion des demandes"""
    return GererDemandesUseCase(
        stock_repository=DjangoStockRepository(),
        demande_repository=DjangoDemandeRepository(),
        produit_service=HttpProduitService(),
        magasin_service=HttpMagasinService(),
    )


# === HEALTH CHECK ===


@swagger_auto_schema(
    method="get",
    operation_description="Health check pour vérifier que le service DDD fonctionne",
    responses={200: "Service opérationnel"},
)
@api_view(["GET"])
def health_check(request):
    """Health check pour vérifier que le service DDD fonctionne"""
    return JsonResponse(
        {
            "status": "healthy",
            "service": "Service Inventaire DDD",
            "version": "1.0.0",
            "architecture": "Domain-Driven Design",
        }
    )


# === GESTION DES STOCKS ===


@swagger_auto_schema(
    method="post",
    operation_description="Augmente le stock d'un produit (central ou local)",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "produit_id": openapi.Schema(
                type=openapi.TYPE_INTEGER, description="ID du produit"
            ),
            "quantite": openapi.Schema(
                type=openapi.TYPE_INTEGER, description="Quantité à ajouter"
            ),
            "magasin_id": openapi.Schema(
                type=openapi.TYPE_INTEGER,
                description="ID du magasin (optionnel pour stock central)",
            ),
        },
        required=["produit_id", "quantite"],
    ),
    responses={200: "Stock augmenté avec succès", 400: "Erreur de validation"},
)
@csrf_exempt
@api_view(["POST"])
def augmenter_stock(request):
    """
    API DDD : Augmente le stock d'un produit (central ou local)
    Équivalent à l'ancienne API /increase_stock/
    """
    try:
        data = json.loads(request.body)
        request_dto = AugmenterStockRequest(
            produit_id=data["produit_id"],
            quantite=data["quantite"],
            magasin_id=data.get("magasin_id"),
        )

        use_case = _get_gerer_stock_use_case()
        result = use_case.augmenter_stock(request_dto)

        return JsonResponse(result, status=200)

    except (KeyError, ValueError, json.JSONDecodeError) as e:
        return JsonResponse({"error": f"Données invalides: {str(e)}"}, status=400)
    except InventaireDomainError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Erreur interne: {str(e)}"}, status=500)


@swagger_auto_schema(
    method="post",
    operation_description="Diminue le stock d'un produit (central ou local)",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "produit_id": openapi.Schema(
                type=openapi.TYPE_INTEGER, description="ID du produit"
            ),
            "quantite": openapi.Schema(
                type=openapi.TYPE_INTEGER, description="Quantité à retirer"
            ),
            "magasin_id": openapi.Schema(
                type=openapi.TYPE_INTEGER,
                description="ID du magasin (optionnel pour stock central)",
            ),
        },
        required=["produit_id", "quantite"],
    ),
    responses={200: "Stock diminué avec succès", 400: "Stock insuffisant ou erreur"},
)
@csrf_exempt
@api_view(["POST"])
def diminuer_stock(request):
    """
    API DDD : Diminue le stock d'un produit (central ou local)
    Équivalent à l'ancienne API /decrease_stock/
    """
    try:
        data = json.loads(request.body)
        request_dto = DiminuerStockRequest(
            produit_id=data["produit_id"],
            quantite=data["quantite"],
            magasin_id=data.get("magasin_id"),
        )

        use_case = _get_gerer_stock_use_case()
        result = use_case.diminuer_stock(request_dto)

        return JsonResponse(result, status=200)

    except (KeyError, ValueError, json.JSONDecodeError) as e:
        return JsonResponse({"error": f"Données invalides: {str(e)}"}, status=400)
    except StockInsuffisantError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except InventaireDomainError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Erreur interne: {str(e)}"}, status=500)


@swagger_auto_schema(
    method="get",
    operation_description="Consulte le stock central d'un produit",
    responses={200: "Informations du stock central", 400: "Produit non trouvé"},
)
@api_view(["GET"])
def consulter_stock_central(request, produit_id):
    """
    API DDD : Consulte le stock central d'un produit
    Équivalent à l'ancienne API /stock_central/{produit_id}/
    """
    try:
        use_case = _get_gerer_stock_use_case()
        result = use_case.consulter_stock(produit_id=str(produit_id))

        return JsonResponse(
            {
                "produit_id": result.produit_id,
                "quantite": result.quantite,
                "niveau": result.niveau,
                "nom_produit": result.nom_produit,
            }
        )

    except ValueError:
        return JsonResponse({"error": "ID produit invalide"}, status=400)
    except InventaireDomainError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Erreur interne: {str(e)}"}, status=500)


@swagger_auto_schema(
    method="get",
    operation_description="Consulte le stock local d'un produit dans un magasin",
    responses={
        200: "Informations du stock local",
        400: "Produit ou magasin non trouvé",
    },
)
@api_view(["GET"])
def consulter_stock_local(request, produit_id, magasin_id):
    """
    API DDD : Consulte le stock local d'un produit dans un magasin
    Équivalent à l'ancienne API /stock_local/{produit_id}/{magasin_id}/
    """
    try:
        use_case = _get_gerer_stock_use_case()
        result = use_case.consulter_stock(
            produit_id=str(produit_id), magasin_id=str(magasin_id)
        )

        return JsonResponse(
            {
                "produit_id": result.produit_id,
                "quantite": result.quantite,
                "niveau": result.niveau,
                "magasin_id": result.magasin_id,
                "nom_produit": result.nom_produit,
                "nom_magasin": result.nom_magasin,
            }
        )

    except ValueError:
        return JsonResponse({"error": "ID produit ou magasin invalide"}, status=400)
    except InventaireDomainError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Erreur interne: {str(e)}"}, status=500)


@swagger_auto_schema(
    method="get",
    operation_description="Liste tous les stocks centraux",
    responses={200: "Liste des stocks centraux"},
)
@api_view(["GET"])
def lister_stocks_centraux(request):
    """
    API DDD : Liste tous les stocks centraux
    Équivalent à l'ancienne API /stocks_centraux/
    """
    try:
        use_case = _get_gerer_stock_use_case()
        results = use_case.lister_tous_stocks_centraux()

        return JsonResponse(
            {
                "stocks": [
                    {
                        "produit_id": result.produit_id,
                        "quantite": result.quantite,
                        "niveau": result.niveau,
                        "nom_produit": result.nom_produit,
                    }
                    for result in results
                ]
            }
        )

    except Exception as e:
        return JsonResponse({"error": f"Erreur interne: {str(e)}"}, status=500)


@swagger_auto_schema(
    method="get",
    operation_description="Liste les stocks locaux d'un magasin",
    responses={200: "Liste des stocks du magasin"},
)
@api_view(["GET"])
def lister_stocks_locaux_magasin(request, magasin_id):
    """
    API DDD : Liste tous les stocks locaux d'un magasin
    Équivalent à l'ancienne API /stocks_locaux/{magasin_id}/
    """
    try:
        use_case = _get_gerer_stock_use_case()
        results = use_case.lister_stocks_locaux_magasin(magasin_id=str(magasin_id))

        return JsonResponse(
            {
                "magasin_id": str(magasin_id),
                "stocks": [
                    {
                        "produit_id": result.produit_id,
                        "quantite": result.quantite,
                        "niveau": result.niveau,
                        "nom_produit": result.nom_produit,
                    }
                    for result in results
                ],
            }
        )

    except ValueError:
        return JsonResponse({"error": "ID magasin invalide"}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Erreur interne: {str(e)}"}, status=500)


@swagger_auto_schema(
    method="get",
    operation_description="Liste tous les magasins avec leurs stocks locaux",
    responses={200: "Liste des magasins avec leurs stocks"},
)
@api_view(["GET"])
def lister_tous_magasins_avec_stocks(request):
    """
    API DDD : Liste tous les magasins avec leurs stocks locaux
    Vue globale des stocks par magasin - nouvelle fonctionnalité
    """
    try:
        use_case = _get_gerer_stock_use_case()
        result = use_case.lister_tous_stocks_par_magasin()

        return JsonResponse(result, status=200)

    except Exception as e:
        return JsonResponse({"error": f"Erreur interne: {str(e)}"}, status=500)


# === GESTION DES DEMANDES ===


@swagger_auto_schema(
    method="post",
    operation_description="Crée une nouvelle demande de réapprovisionnement",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "produit_id": openapi.Schema(
                type=openapi.TYPE_STRING, description="UUID du produit"
            ),
            "magasin_id": openapi.Schema(
                type=openapi.TYPE_STRING, description="UUID du magasin"
            ),
            "quantite": openapi.Schema(
                type=openapi.TYPE_INTEGER, description="Quantité demandée"
            ),
        },
        required=["produit_id", "magasin_id", "quantite"],
    ),
    responses={201: "Demande créée avec succès", 400: "Erreur de validation"},
)
@csrf_exempt
@api_view(["POST"])
def creer_demande(request):
    """
    API DDD : Crée une nouvelle demande de réapprovisionnement
    Équivalent à l'ancienne API /demandes/
    """
    try:
        data = json.loads(request.body)
        request_dto = CreerDemandeRequest(
            produit_id=data["produit_id"],
            magasin_id=data["magasin_id"],
            quantite=data["quantite"],
        )

        use_case = _get_gerer_demandes_use_case()
        result = use_case.creer_demande(request_dto)

        # Convertir en dictionnaire pour la sérialisation JSON
        response_data = {
            "id": result.id,
            "produit_id": result.produit_id,
            "magasin_id": result.magasin_id,
            "quantite": result.quantite,
            "statut": result.statut,
            "date_creation": result.date_creation,
            "nom_produit": result.nom_produit,
            "nom_magasin": result.nom_magasin,
        }

        return JsonResponse(response_data, status=201)

    except (KeyError, ValueError, json.JSONDecodeError) as e:
        return JsonResponse({"error": f"Données invalides: {str(e)}"}, status=400)
    except InventaireDomainError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Erreur interne: {str(e)}"}, status=500)


@swagger_auto_schema(
    method="get",
    operation_description="Liste toutes les demandes en attente",
    responses={200: "Liste des demandes en attente"},
)
@api_view(["GET"])
def lister_demandes_en_attente(request):
    """
    API DDD : Liste toutes les demandes de réapprovisionnement en attente
    Équivalent à l'ancienne API /demandes/?statut=En attente
    """
    try:
        use_case = _get_gerer_demandes_use_case()
        results = use_case.lister_demandes_en_attente()

        return JsonResponse(
            {
                "demandes": [
                    {
                        "id": result.id,
                        "produit_id": result.produit_id,
                        "magasin_id": result.magasin_id,
                        "quantite": result.quantite,
                        "statut": result.statut,
                        "date_creation": result.date_creation,
                        "nom_produit": result.nom_produit,
                        "nom_magasin": result.nom_magasin,
                    }
                    for result in results
                ]
            }
        )

    except Exception as e:
        return JsonResponse({"error": f"Erreur interne: {str(e)}"}, status=500)


@swagger_auto_schema(
    operation_description="Liste toutes les demandes d'un magasin spécifique",
    responses={200: "Liste des demandes du magasin", 400: "Magasin non trouvé"},
)
@require_http_methods(["GET"])
def lister_demandes_par_magasin(request, magasin_id):
    """
    API DDD : Liste toutes les demandes d'un magasin
    Équivalent à l'ancienne API GET /demandes/magasin/{id}/
    """
    try:
        use_case = _get_gerer_demandes_use_case()
        results = use_case.lister_demandes_par_magasin(str(magasin_id))

        return JsonResponse(
            {
                "magasin_id": str(magasin_id),
                "demandes": [
                    {
                        "id": result.id,
                        "produit_id": result.produit_id,
                        "quantite": result.quantite,
                        "statut": result.statut,
                        "date_creation": result.date_creation,
                        "nom_produit": result.nom_produit,
                    }
                    for result in results
                ],
            }
        )

    except ValueError:
        return JsonResponse({"error": "ID magasin invalide"}, status=400)
    except InventaireDomainError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Erreur interne: {str(e)}"}, status=500)


@swagger_auto_schema(
    operation_description="Récupère une demande spécifique par son ID",
    responses={200: "Détails de la demande", 404: "Demande non trouvée"},
)
@require_http_methods(["GET"])
def obtenir_demande_par_id(request, demande_id):
    """
    API DDD : Récupère une demande spécifique par son ID
    Équivalent à l'ancienne API GET /demandes/{id}/
    """
    try:
        use_case = _get_gerer_demandes_use_case()
        result = use_case.obtenir_demande_par_id(demande_id)

        return JsonResponse(
            {
                "id": result.id,
                "produit_id": result.produit_id,
                "magasin_id": result.magasin_id,
                "quantite": result.quantite,
                "statut": result.statut,
                "date_creation": result.date_creation,
                "date_modification": result.date_modification,
                "nom_produit": result.nom_produit,
                "nom_magasin": result.nom_magasin,
            }
        )

    except InventaireDomainError as e:
        return JsonResponse({"error": str(e)}, status=404)
    except Exception as e:
        return JsonResponse({"error": f"Erreur interne: {str(e)}"}, status=500)


@swagger_auto_schema(
    operation_description="Supprime une demande (seulement si en attente)",
    responses={200: "Demande supprimée", 400: "Impossible de supprimer"},
)
@csrf_exempt
@require_http_methods(["DELETE"])
def supprimer_demande(request, demande_id):
    """
    API DDD : Supprime une demande (seulement si en attente)
    Équivalent à l'ancienne API DELETE /demandes/{id}/
    """
    try:
        use_case = _get_gerer_demandes_use_case()
        result = use_case.supprimer_demande(demande_id)

        return JsonResponse(result)

    except InventaireDomainError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Erreur interne: {str(e)}"}, status=500)


@swagger_auto_schema(
    operation_description="Approuve une demande de réapprovisionnement",
    responses={
        200: "Demande approuvée",
        400: "Impossible d'approuver",
        404: "Demande non trouvée",
    },
)
@csrf_exempt
@require_http_methods(["PUT"])
def approuver_demande(request, demande_id):
    """
    API DDD : Approuve une demande de réapprovisionnement
    Nouveau endpoint pour le service-supply-chain
    """
    try:
        use_case = _get_gerer_demandes_use_case()
        result = use_case.approuver_demande(demande_id)

        return JsonResponse(
            {
                "id": result.id,
                "produit_id": result.produit_id,
                "magasin_id": result.magasin_id,
                "quantite": result.quantite,
                "statut": result.statut,
                "date_creation": result.date_creation,
                "date_modification": result.date_modification,
                "nom_produit": result.nom_produit,
                "nom_magasin": result.nom_magasin,
            }
        )

    except InventaireDomainError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Erreur interne: {str(e)}"}, status=500)


@swagger_auto_schema(
    operation_description="Rejette une demande de réapprovisionnement",
    responses={
        200: "Demande rejetée",
        400: "Impossible de rejeter",
        404: "Demande non trouvée",
    },
)
@csrf_exempt
@require_http_methods(["PUT"])
def rejeter_demande(request, demande_id):
    """
    API DDD : Rejette une demande de réapprovisionnement
    Nouveau endpoint pour le service-supply-chain
    """
    try:
        use_case = _get_gerer_demandes_use_case()
        result = use_case.rejeter_demande(demande_id)

        return JsonResponse(
            {
                "id": result.id,
                "produit_id": result.produit_id,
                "magasin_id": result.magasin_id,
                "quantite": result.quantite,
                "statut": result.statut,
                "date_creation": result.date_creation,
                "date_modification": result.date_modification,
                "nom_produit": result.nom_produit,
                "nom_magasin": result.nom_magasin,
            }
        )

    except InventaireDomainError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Erreur interne: {str(e)}"}, status=500)


@swagger_auto_schema(
    operation_description="Analyse les besoins de réapprovisionnement d'un magasin",
    responses={200: "Analyse des besoins", 400: "Magasin non trouvé"},
)
@require_http_methods(["GET"])
def analyser_besoins_reapprovisionnement(request, magasin_id):
    """
    API DDD : Analyse les besoins de réapprovisionnement d'un magasin
    Nouvelle fonctionnalité métier pour identifier les produits à faible stock
    """
    try:
        use_case = _get_gerer_demandes_use_case()
        result = use_case.analyser_besoins_reapprovisionnement(int(magasin_id))

        return JsonResponse(result)

    except ValueError:
        return JsonResponse({"error": "ID magasin invalide"}, status=400)
    except InventaireDomainError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Erreur interne: {str(e)}"}, status=500)
