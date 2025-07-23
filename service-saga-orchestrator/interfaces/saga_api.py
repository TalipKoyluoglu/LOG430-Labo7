"""
API REST pour les Sagas orchestrées
Interface HTTP pour démarrer et consulter des sagas de commande
"""

import json
import logging
import uuid
from typing import Dict, Any, Tuple
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.http import HttpResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from application.saga_orchestrator import SagaOrchestrator
from domain.entities import SagaCommande, LigneCommande, EtatSaga
from domain.exceptions import (
    SagaException,
    StockInsuffisantException,
    ServiceExterneIndisponibleException,
    DonneesInvalidesException,
)
from infrastructure.django_saga_repository import DjangoSagaRepository
from infrastructure.prometheus_metrics import metrics_collector

logger = logging.getLogger(__name__)


def valider_uuid(uuid_string: str, nom_champ: str) -> Tuple[bool, str]:
    """
    Valide qu'une chaîne est un UUID valide
    
    Returns:
        tuple: (is_valid: bool, error_message: str)
    """
    if not uuid_string:
        return False, f"Le champ '{nom_champ}' est requis"
    
    try:
        uuid.UUID(str(uuid_string))
        return True, ""
    except (ValueError, TypeError, AttributeError):
        return False, f"Le champ '{nom_champ}' doit être un UUID valide"


@swagger_auto_schema(
    method="post",
    operation_summary="Démarrer une nouvelle saga de commande",
    operation_description="""
    **Use Case: Saga orchestrée synchrone pour création de commande**
    
    Cette API démarre une saga qui coordonne:
    1. Vérification du stock (service-inventaire)
    2. **Récupération automatique des informations produit** (service-catalogue)
    3. Réservation du stock (service-inventaire) 
    4. Création de la commande (service-commandes)
    
    **Note importante :** Vous n'avez qu'à fournir `produit_id` et `quantite`. 
    Le nom, prix et autres détails sont récupérés automatiquement du service-catalogue.
    
    En cas d'échec, une compensation automatique libère le stock réservé.
    """,
    tags=["Saga Orchestrée"],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=["client_id", "magasin_id", "lignes"],
        properties={
            "client_id": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="UUID du client qui passe la commande",
                format="uuid"
            ),
            "magasin_id": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="UUID du magasin où effectuer la commande",
                format="uuid",
                default="550e8400-e29b-41d4-a716-446655440000"
            ),
            "lignes": openapi.Schema(
                type=openapi.TYPE_ARRAY,
                description="Lignes de la commande",
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    required=["produit_id", "quantite"],
                    properties={
                        "produit_id": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="ID du produit (UUID) - Les détails seront récupérés automatiquement du catalogue"
                        ),
                        "quantite": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            minimum=1,
                            description="Quantité à commander"
                        )
                    }
                )
            )
        },
        example={
            "client_id": "12345678-1234-1234-1234-123456789012",
            "magasin_id": "550e8400-e29b-41d4-a716-446655440000",
            "lignes": [
                {
                    "produit_id": "550e8400-e29b-41d4-a716-446655440001",
                    "quantite": 2
                },
                {
                    "produit_id": "550e8400-e29b-41d4-a716-446655440002", 
                    "quantite": 1
                }
            ]
        }
    ),
    responses={
        201: openapi.Response(
            description="Saga exécutée avec succès",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    "saga_id": openapi.Schema(type=openapi.TYPE_STRING),
                    "etat_final": openapi.Schema(type=openapi.TYPE_STRING),
                    "commande_id": openapi.Schema(type=openapi.TYPE_STRING),
                    "resume_execution": openapi.Schema(type=openapi.TYPE_OBJECT)
                }
            )
        ),
        400: openapi.Response(description="Données invalides ou stock insuffisant"),
        500: openapi.Response(description="Erreur interne ou service indisponible")
    }
)
@csrf_exempt
@api_view(["POST"])
def demarrer_saga_commande(request):
    """
    Démarre une saga orchestrée pour créer une commande
    """
    try:
        # 1. Validation des données d'entrée
        if not request.body:
            return JsonResponse(
                {"error": "Le corps de la requête est requis"},
                status=400
            )
        
        try:
            data = json.loads(request.body.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            return JsonResponse(
                {"error": f"Format JSON invalide: {str(e)}"},
                status=400
            )
        
        if not isinstance(data, dict):
            return JsonResponse(
                {"error": "Le corps de la requête doit être un objet JSON"},
                status=400
            )
        
        # Vérification des champs requis
        if "client_id" not in data or not data["client_id"]:
            return JsonResponse(
                {"error": "Le champ 'client_id' est requis"},
                status=400
            )
        
        if "lignes" not in data or not data["lignes"] or not isinstance(data["lignes"], list):
            return JsonResponse(
                {"error": "Le champ 'lignes' est requis et doit contenir au moins une ligne"},
                status=400
            )
        
        # Validation des UUID
        is_valid, error_msg = valider_uuid(data["client_id"], "client_id")
        if not is_valid:
            return JsonResponse({"error": error_msg}, status=400)
        
        magasin_id = data.get("magasin_id", "550e8400-e29b-41d4-a716-446655440000")
        is_valid, error_msg = valider_uuid(magasin_id, "magasin_id") 
        if not is_valid:
            return JsonResponse({"error": error_msg}, status=400)
        
        # 2. Construction de la saga
        saga = SagaCommande(
            client_id=data["client_id"],
            magasin_id=magasin_id
        )
        
        # Ajouter les lignes de commande (seulement produit_id + quantite)
        for i, ligne_data in enumerate(data["lignes"]):
            try:
                # Validation des champs requis
                if not isinstance(ligne_data, dict):
                    return JsonResponse(
                        {"error": f"Ligne {i+1}: doit être un objet JSON"},
                        status=400
                    )
                
                if "produit_id" not in ligne_data or not ligne_data["produit_id"]:
                    return JsonResponse(
                        {"error": f"Ligne {i+1}: 'produit_id' est requis"},
                        status=400
                    )
                
                if "quantite" not in ligne_data or ligne_data["quantite"] is None:
                    return JsonResponse(
                        {"error": f"Ligne {i+1}: 'quantite' est requis"},
                        status=400
                    )
                
                # Validation UUID du produit
                is_valid, error_msg = valider_uuid(ligne_data["produit_id"], f"produit_id (ligne {i+1})")
                if not is_valid:
                    return JsonResponse({"error": error_msg}, status=400)
                
                ligne = LigneCommande(
                    produit_id=ligne_data["produit_id"],
                    quantite=int(ligne_data["quantite"]),
                    prix_unitaire=0.0,  # Sera récupéré du service catalogue
                    nom_produit=""       # Sera récupéré du service catalogue
                )
                saga.ajouter_ligne_commande(ligne)
            except (KeyError, ValueError, TypeError) as e:
                return JsonResponse(
                    {"error": f"Ligne {i+1} invalide: {str(e)}"},
                    status=400
                )
        
        logger.info(f"Saga créée: {saga.id} pour client {saga.client_id}")
        
        # 3. Initialiser le repository pour la persistance
        saga_repository = DjangoSagaRepository()
        
        # Sauvegarder la saga initiale
        saga_repository.save(saga)
        
        # 4. Exécution de la saga via l'orchestrateur avec persistance
        orchestrator = SagaOrchestrator()
        resume_execution = orchestrator.executer_saga(saga, saga_repository)
        
        # 5. Réponse de succès
        response_data = {
            "success": True,
            "saga_id": saga.id,
            "etat_final": saga.etat_actuel.value,
            "commande_id": saga.commande_finale_id,
            "resume_execution": resume_execution
        }
        
        logger.info(f"Saga {saga.id} terminée avec succès")
        return JsonResponse(response_data, status=201)
        
    except StockInsuffisantException as e:
        logger.warning(f"Stock insuffisant: {e}")
        return JsonResponse(
            {
                "error": "Stock insuffisant",
                "details": str(e),
                "saga_id": saga.id if 'saga' in locals() else None
            },
            status=400
        )
    except ServiceExterneIndisponibleException as e:
        logger.error(f"Service externe indisponible: {e}")
        return JsonResponse(
            {
                "error": "Service externe indisponible",
                "details": str(e),
                "saga_id": saga.id if 'saga' in locals() else None
            },
            status=500
        )
    except SagaException as e:
        logger.error(f"Erreur de saga: {e}")
        return JsonResponse(
            {
                "error": "Erreur lors de l'exécution de la saga",
                "details": str(e),
                "saga_id": saga.id if 'saga' in locals() else None
            },
            status=400
        )
    except Exception as e:
        logger.error(f"Erreur inattendue: {e}", exc_info=True)
        return JsonResponse(
            {
                "error": "Erreur interne du serveur",
                "details": str(e)
            },
            status=500
        )


@swagger_auto_schema(
    method="get",
    operation_summary="Consulter le statut d'une saga",
    operation_description="Récupère l'état actuel et l'historique d'une saga",
    tags=["Saga Orchestrée"],
    manual_parameters=[
        openapi.Parameter(
            "saga_id",
            openapi.IN_PATH,
            description="ID de la saga à consulter",
            type=openapi.TYPE_STRING,
            required=True
        )
    ],
    responses={
        200: openapi.Response(description="Statut de la saga"),
        404: openapi.Response(description="Saga non trouvée")
    }
)
@csrf_exempt
@api_view(["GET"])
def consulter_saga(request, saga_id):
    """
    Consulte le statut d'une saga depuis la base de données
    """
    try:
        # Utiliser le repository pour récupérer la saga
        saga_repository = DjangoSagaRepository()
        saga = saga_repository.get_by_id(saga_id)
        
        if not saga:
            return JsonResponse(
                {"error": f"Saga {saga_id} non trouvée"},
                status=404
            )
        
        # Construire la réponse avec les détails de la saga
        statut = {
            "saga_id": str(saga.id),
            "client_id": saga.client_id,
            "magasin_id": saga.magasin_id,
            "etat_actuel": saga.etat_actuel.value,
            "est_terminee": saga.est_terminee,
            "commande_finale_id": saga.commande_finale_id,
            "date_creation": saga.evenements[0].timestamp.isoformat() if saga.evenements else None,
            "derniere_modification": saga.evenements[-1].timestamp.isoformat() if saga.evenements else None,
            "donnees_contexte": saga.donnees_contexte,
            "historique_evenements": [
                {
                    "type": evt.type_evenement.value,
                    "etat_precedent": evt.etat_precedent.value if evt.etat_precedent else None,
                    "nouvel_etat": evt.nouvel_etat.value,
                    "message": evt.message,
                    "timestamp": evt.timestamp.isoformat(),
                    "donnees": evt.donnees
                }
                for evt in saga.evenements
            ],
            "lignes_commande": [
                {
                    "produit_id": ligne.produit_id,
                    "quantite": ligne.quantite
                }
                for ligne in saga.lignes_commande
            ]
        }
        
        return JsonResponse(statut, status=200)
        
    except Exception as e:
        logger.error(f"Erreur lors de la consultation de saga {saga_id}: {e}")
        return JsonResponse(
            {"error": f"Erreur lors de la consultation: {str(e)}"},
            status=500
        )


@swagger_auto_schema(
    method="post",
    operation_summary="Simuler un échec de stock",
    operation_description="""
    **Endpoint de test pour simuler des échecs de stock**
    
    Permet de tester le comportement de compensation de la saga
    en forçant un échec de stock insuffisant.
    """,
    tags=["Tests Saga"],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=["client_id", "lignes"],
        properties={
            "client_id": openapi.Schema(type=openapi.TYPE_INTEGER),
            "magasin_id": openapi.Schema(type=openapi.TYPE_INTEGER, default=1),
            "lignes": openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "produit_id": openapi.Schema(type=openapi.TYPE_INTEGER),
                        "quantite": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            minimum=1000,  # Force un échec
                            description="Quantité élevée pour forcer l'échec"
                        ),
                        "prix_unitaire": openapi.Schema(type=openapi.TYPE_NUMBER)
                    }
                )
            )
        }
    ),
    responses={
        400: openapi.Response(description="Échec simulé avec succès"),
        500: openapi.Response(description="Erreur de simulation")
    }
)
@csrf_exempt
@api_view(["POST"])
def simuler_echec_stock(request):
    """
    Simule un échec de stock pour tester la compensation
    """
    try:
        data = json.loads(request.body)
        
        # Forcer des quantités élevées pour provoquer l'échec
        for ligne in data.get("lignes", []):
            ligne["quantite"] = max(ligne.get("quantite", 1000), 1000)
        
        # Utiliser la même logique que demarrer_saga_commande
        saga = SagaCommande(
            client_id=data["client_id"],
            magasin_id=data.get("magasin_id", 1)
        )
        
        for ligne_data in data["lignes"]:
            ligne = LigneCommande(
                produit_id=ligne_data["produit_id"],
                quantite=ligne_data["quantite"],
                prix_unitaire=float(ligne_data["prix_unitaire"]),
                nom_produit=ligne_data.get("nom_produit", "")
            )
            saga.ajouter_ligne_commande(ligne)
        
        # Exécution qui va échouer
        orchestrator = SagaOrchestrator()
        try:
            orchestrator.executer_saga(saga)
            return JsonResponse(
                {"error": "La simulation d'échec n'a pas fonctionné"},
                status=500
            )
        except StockInsuffisantException as e:
            return JsonResponse(
                {
                    "simulation_reussie": True,
                    "echec_simule": "Stock insuffisant",
                    "saga_id": saga.id,
                    "etat_final": saga.etat_actuel.value,
                    "details": str(e),
                    "resume_execution": saga.obtenir_resume_execution()
                },
                status=400
            )
        
    except Exception as e:
        logger.error(f"Erreur lors de la simulation d'échec: {e}")
        return JsonResponse(
            {"error": f"Erreur de simulation: {str(e)}"},
            status=500
        )


@api_view(["GET"])
def health_check(request):
    """Health check de l'API Saga"""
    return JsonResponse({
        "status": "healthy",
        "service": "saga-orchestrator",
        "version": "1.0.0",
        "capabilities": [
            "saga-orchestration-synchrone",
            "compensation-automatique",
            "coordination-stock-commande"
        ]
    })


@api_view(["GET"])
def metrics(request):
    """
    Endpoint Prometheus pour exposer les métriques du service saga
    """
    # Mettre à jour les métriques de sagas actives
    try:
        saga_repository = DjangoSagaRepository()
        sagas_actives = saga_repository.get_all_actives()
        
        # Compter par état
        sagas_by_state = {}
        for saga in sagas_actives:
            etat = saga.etat_actuel.value
            sagas_by_state[etat] = sagas_by_state.get(etat, 0) + 1
        
        # Mettre à jour les métriques
        metrics_collector.update_active_sagas_count(sagas_by_state)
        
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour des métriques: {e}")
    
    # Générer et retourner les métriques Prometheus
    return HttpResponse(
        generate_latest(), 
        content_type=CONTENT_TYPE_LATEST
    )


@swagger_auto_schema(
    method="get",
    operation_summary="Lister toutes les sagas",
    operation_description="Récupère la liste de toutes les sagas avec possibilité de filtrer par état",
    tags=["Saga Orchestrée"],
    manual_parameters=[
        openapi.Parameter(
            "etat",
            openapi.IN_QUERY,
            description="Filtrer par état (ex: EN_ATTENTE, SAGA_TERMINEE, SAGA_ANNULEE)",
            type=openapi.TYPE_STRING,
            required=False
        ),
        openapi.Parameter(
            "actives_seulement",
            openapi.IN_QUERY,
            description="Afficher seulement les sagas actives (non terminées)",
            type=openapi.TYPE_BOOLEAN,
            required=False,
            default=False
        )
    ],
    responses={
        200: openapi.Response(description="Liste des sagas"),
        500: openapi.Response(description="Erreur interne")
    }
)
@csrf_exempt
@api_view(["GET"])
def lister_sagas(request):
    """
    Liste toutes les sagas avec possibilité de filtrage
    """
    try:
        saga_repository = DjangoSagaRepository()
        
        # Paramètres de filtrage
        etat_filtre = request.GET.get('etat')
        actives_seulement = request.GET.get('actives_seulement', 'false').lower() == 'true'
        
        # Récupérer les sagas selon les filtres
        if actives_seulement:
            sagas = saga_repository.get_all_actives()
        elif etat_filtre:
            try:
                etat = EtatSaga(etat_filtre)
                sagas = saga_repository.get_by_etat(etat)
            except ValueError:
                return JsonResponse(
                    {"error": f"État '{etat_filtre}' invalide"},
                    status=400
                )
        else:
            # Récupérer toutes les sagas par défaut
            # En production, on ajouterait de la pagination
            sagas = saga_repository.get_all()
        
        # Construire la réponse
        sagas_data = []
        for saga in sagas:
            saga_info = {
                "saga_id": str(saga.id),
                "client_id": saga.client_id,
                "magasin_id": saga.magasin_id,
                "etat_actuel": saga.etat_actuel.value,
                "est_terminee": saga.est_terminee,
                "necessite_compensation": saga.necessite_compensation,
                "commande_finale_id": saga.commande_finale_id,
                "date_creation": saga.evenements[0].timestamp.isoformat() if saga.evenements else None,
                "derniere_modification": saga.evenements[-1].timestamp.isoformat() if saga.evenements else None,
                "nombre_lignes": len(saga.lignes_commande),
                "nombre_evenements": len(saga.evenements)
            }
            sagas_data.append(saga_info)
        
        return JsonResponse({
            "success": True,
            "total": len(sagas_data),
            "filtres": {
                "etat": etat_filtre,
                "actives_seulement": actives_seulement
            },
            "sagas": sagas_data
        }, status=200)
        
    except Exception as e:
        logger.error(f"Erreur lors du listing des sagas: {e}")
        return JsonResponse(
            {"error": f"Erreur lors du listing: {str(e)}"},
            status=500
        )


@api_view(["GET"])
def api_info(request):
    """Informations sur l'API Saga"""
    return JsonResponse({
        "service": "Service Saga Orchestrator",
        "description": "Orchestration synchrone de sagas pour la création de commandes",
        "architecture": "Domain-Driven Design (DDD)",
        "endpoints": {
            "POST /api/saga/commandes/": "Démarrer une saga de commande",
            "GET /api/saga/commandes/{saga_id}/": "Consulter le statut d'une saga",
            "GET /api/saga/sagas/": "Lister toutes les sagas",
            "POST /api/saga/test/echec-stock/": "Simuler un échec de stock",
            "GET /api/saga/health/": "Health check",
            "GET /api/saga/info/": "Informations sur l'API"
        },
        "workflow_saga": [
            "1. Vérification du stock (service-inventaire)",
            "2. Récupération informations produit (service-catalogue)",
            "3. Réservation du stock (service-inventaire)",
            "4. Création de la commande (service-commandes)",
            "5. Compensation automatique en cas d'échec"
        ],
        "services_integres": [
            "service-catalogue (port 8001)",
            "service-inventaire (port 8002)",
            "service-commandes (port 8003)"
        ]
    }) 


@csrf_exempt
@api_view(["POST"])
def forcer_compensation_saga(request, saga_id):
    """
    Force la compensation d'une saga orpheline (nettoyage manuel)
    """
    try:
        saga_repository = DjangoSagaRepository()
        saga = saga_repository.get_by_id(saga_id)
        
        if not saga:
            return JsonResponse(
                {"error": f"Saga {saga_id} introuvable"},
                status=404
            )
        
        if saga.est_terminee:
            return JsonResponse(
                {"error": f"Saga {saga_id} déjà terminée"},
                status=400
            )
        
        # Forcer la compensation
        orchestrator = SagaOrchestrator()
        
        # Marquer qu'elle nécessite une compensation si elle a des réservations
        if saga.reservation_stock_ids:
            logger.warning(f"Forçage de compensation pour saga orpheline {saga_id}")
            orchestrator._executer_compensation(saga)
            saga_repository.save(saga)
            
            return JsonResponse({
                "success": True,
                "message": f"Compensation forcée pour saga {saga_id}",
                "saga_id": saga_id,
                "etat_final": saga.etat_actuel.value,
                "reservations_liberees": len(saga.reservation_stock_ids)
            })
        else:
            # Juste marquer comme annulée si pas de réservations
            saga.transitionner_vers(
                EtatSaga.SAGA_ANNULEE,
                TypeEvenement.COMPENSATION_TERMINEE,
                message="Saga orpheline nettoyée manuellement"
            )
            saga_repository.save(saga)
            
            return JsonResponse({
                "success": True,
                "message": f"Saga {saga_id} nettoyée (pas de réservations à libérer)",
                "saga_id": saga_id,
                "etat_final": saga.etat_actuel.value
            })
        
    except Exception as e:
        logger.error(f"Erreur lors du forçage de compensation: {e}")
        return JsonResponse(
            {"error": "Erreur interne du serveur", "details": str(e)},
            status=500
        ) 