"""
Vues DDD - Orchestration des Use Cases
APIs REST orientées métier plutôt que CRUD.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging

from ..application.use_cases.valider_demande_use_case import (
    ValiderDemandeUseCase,
    ValiderDemandeCommand,
)
from ..application.use_cases.rejeter_demande_use_case import (
    RejeterDemandeUseCase,
    RejeterDemandeCommand,
)
from ..application.use_cases.lister_demandes_use_case import (
    ListerDemandesUseCase,
    ListerDemandesQuery,
)
from ..infrastructure.http_demande_repository import HttpDemandeRepository
from ..infrastructure.http_stock_service import HttpStockService
from ..domain.exceptions import ReapprovisionnementDomainError

logger = logging.getLogger(__name__)


class DDDDemandesEnAttenteAPI(APIView):
    """Use Case : Lister les demandes en attente"""

    @swagger_auto_schema(
        operation_summary="[DDD] Lister les demandes en attente",
        operation_description="""
        **Use Case métier :** Récupère toutes les demandes de réapprovisionnement en attente.
        
        **Architecture DDD :**
        • Use Case : ListerDemandesUseCase
        • Entités : DemandeReapprovisionnement avec règles métier
        • Repository : Communication avec service Stock via interface abstraite
        
        **Fonctionnalités métier :**
        • Filtrage automatique des demandes en attente
        • Validation des données métier
        • Gestion d'erreurs spécifiques au domaine
        """,
        responses={
            200: openapi.Response(
                description="Demandes récupérées avec succès",
                examples={
                    "application/json": {
                        "success": True,
                        "use_case": "ListerDemandesUseCase",
                        "count": 2,
                        "demandes": [
                            {
                                "id": "550e8400-e29b-41d4-a716-446655440001",
                                "produit_id": "550e8400-e29b-41d4-a716-446655440002",
                                "magasin_id": "33333333-3333-3333-3333-333333333331",
                                "quantite": 50,
                                "statut": "En attente",
                                "date": "2024-01-15T10:30:00Z",
                                "est_quantite_importante": True,
                            }
                        ],
                    }
                },
            )
        },
        tags=["DDD - Demandes"],
    )
    def get(self, request):
        """Exécute le Use Case : Lister les demandes en attente"""
        try:
            # Injection de dépendances DDD
            repository = HttpDemandeRepository()
            use_case = ListerDemandesUseCase(repository)

            # Exécution du Use Case
            query = ListerDemandesQuery()
            result = use_case.execute(query)

            return Response(
                {
                    "success": True,
                    "use_case": "ListerDemandesUseCase",
                    "count": len(result.demandes),
                    "demandes": result.demandes,
                },
                status=status.HTTP_200_OK,
            )

        except ReapprovisionnementDomainError as e:
            logger.error(f"Erreur domaine: {e}")
            return Response(
                {"success": False, "error": str(e), "type": "domain_error"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            logger.error(f"Erreur critique: {e}")
            return Response(
                {
                    "success": False,
                    "error": "Erreur interne lors de la récupération des demandes",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class DDDValiderDemandeAPI(APIView):
    """Use Case : Valider une demande de réapprovisionnement"""

    @swagger_auto_schema(
        operation_summary="[DDD] Valider une demande de réapprovisionnement",
        operation_description="""
        **Use Case métier :** Valide une demande avec workflow complexe et rollback automatique.
        
        **Architecture DDD :**
        • Use Case : ValiderDemandeUseCase (orchestration)
        • Entités : DemandeReapprovisionnement, WorkflowValidation
        • Value Objects : DemandeId, Quantite avec validation
        • Workflow : 3 étapes avec gestion des échecs
        
        **Workflow métier :**
        1. **Validation des règles métier** (entité riche)
        2. **Diminution stock central** (avec vérification)  
        3. **Augmentation stock local** (transfer)
        4. **Mise à jour statut** (finalisation)
        5. **Rollback automatique** en cas d'échec
        
        **Gestion d'erreurs :**
        • Rollback automatique des étapes réussies
        • Exceptions métier spécifiques
        • Logging détaillé pour audit
        """,
        responses={
            200: openapi.Response(
                description="Demande validée avec succès",
                examples={
                    "application/json": {
                        "success": True,
                        "use_case": "ValiderDemandeUseCase",
                        "demande_id": "550e8400-e29b-41d4-a716-446655440001",
                        "message": "Demande validée avec succès",
                        "etapes_executees": [
                            "Diminuer stock central -  Réussi",
                            "Augmenter stock local -  Réussi",
                            "Mettre à jour statut -  Réussi",
                        ],
                        "rollback_effectue": False,
                    }
                },
            ),
            400: openapi.Response(
                description="Erreur de validation métier",
                examples={
                    "application/json": {
                        "success": False,
                        "use_case": "ValiderDemandeUseCase",
                        "error": "La demande ne peut pas être validée (statut: Approuvée)",
                        "type": "workflow_error",
                    }
                },
            ),
        },
        tags=["DDD - Validation"],
    )
    def post(self, request, demande_id):
        """Exécute le Use Case : Valider une demande"""
        try:
            # Injection de dépendances DDD
            repository = HttpDemandeRepository()
            stock_service = HttpStockService()
            use_case = ValiderDemandeUseCase(repository, stock_service)

            # Exécution du Use Case
            command = ValiderDemandeCommand(demande_id=demande_id)
            result = use_case.execute(command)

            response_data = {
                "success": result.succes,
                "use_case": "ValiderDemandeUseCase",
                "demande_id": result.demande_id,
                "message": result.message,
                "etapes_executees": result.etapes_executees,
                "rollback_effectue": result.rollback_effectue,
            }

            if not result.succes:
                response_data["details_erreur"] = result.details_erreur

            status_code = (
                status.HTTP_200_OK if result.succes else status.HTTP_400_BAD_REQUEST
            )
            return Response(response_data, status=status_code)

        except ReapprovisionnementDomainError as e:
            logger.error(f"Erreur domaine: {e}")
            return Response(
                {
                    "success": False,
                    "use_case": "ValiderDemandeUseCase",
                    "error": str(e),
                    "type": "domain_error",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            logger.error(f"Erreur critique: {e}")
            return Response(
                {"success": False, "error": "Erreur interne lors de la validation"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class DDDRejeterDemandeAPI(APIView):
    """Use Case : Rejeter une demande de réapprovisionnement"""

    @swagger_auto_schema(
        operation_summary="[DDD] Rejeter une demande de réapprovisionnement",
        operation_description="""
        **Use Case métier :** Rejette une demande avec motif validé.
        
        **Architecture DDD :**
        • Use Case : RejeterDemandeUseCase
        • Value Objects : MotifRejet avec validation métier
        • Entités : DemandeReapprovisionnement avec règles de transition
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["motif"],
            properties={
                "motif": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Motif de rejet (minimum 5 caractères)",
                    example="Stock central insuffisant pour cette quantité",
                )
            },
        ),
        responses={
            200: openapi.Response(
                description="Demande rejetée avec succès",
                examples={
                    "application/json": {
                        "success": True,
                        "use_case": "RejeterDemandeUseCase",
                        "demande_id": "550e8400-e29b-41d4-a716-446655440001",
                        "message": "Demande rejetée avec succès",
                        "motif": "Stock central insuffisant",
                    }
                },
            )
        },
        tags=["DDD - Validation"],
    )
    def post(self, request, demande_id):
        """Exécute le Use Case : Rejeter une demande"""
        try:
            motif = request.data.get("motif", "")

            # Injection de dépendances DDD
            repository = HttpDemandeRepository()
            use_case = RejeterDemandeUseCase(repository)

            # Exécution du Use Case
            command = RejeterDemandeCommand(demande_id=demande_id, motif=motif)
            result = use_case.execute(command)

            response_data = {
                "success": result.succes,
                "use_case": "RejeterDemandeUseCase",
                "demande_id": result.demande_id,
                "message": result.message,
            }

            if result.succes:
                response_data["motif"] = result.motif
            else:
                response_data["details_erreur"] = result.details_erreur

            status_code = (
                status.HTTP_200_OK if result.succes else status.HTTP_400_BAD_REQUEST
            )
            return Response(response_data, status=status_code)

        except ReapprovisionnementDomainError as e:
            logger.error(f"Erreur domaine: {e}")
            return Response(
                {
                    "success": False,
                    "use_case": "RejeterDemandeUseCase",
                    "error": str(e),
                    "type": "domain_error",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            logger.error(f"Erreur critique: {e}")
            return Response(
                {"success": False, "error": "Erreur interne lors du rejet"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
