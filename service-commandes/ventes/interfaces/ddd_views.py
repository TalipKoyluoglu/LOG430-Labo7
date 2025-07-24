"""
Vues DDD pour le service Ventes (Commandes)
Architecture Domain-Driven Design - Interface Layer
"""

from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action, api_view
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import uuid

# Domain Layer
from ..domain.value_objects import (
    CommandeVente,
    MagasinId,
    ProduitId,
    ClientId,
    StockInfo,
)
from ..domain.exceptions import (
    MagasinInexistantError,
    ProduitInexistantError,
    StockInsuffisantError,
    VenteInvalideError,
    VenteDejaAnnuleeError,
)

# Application Layer
from ..application.use_cases.enregistrer_vente_use_case import EnregistrerVenteUseCase
from ..application.use_cases.annuler_vente_use_case import AnnulerVenteUseCase
from ..application.use_cases.generer_indicateurs_use_case import (
    GenererIndicateursUseCase,
)
from ..application.use_cases.generer_rapport_consolide_use_case import (
    GenererRapportConsolideUseCase,
)

# Infrastructure Layer
from ..infrastructure.django_vente_repository import DjangoVenteRepository
from ..infrastructure.django_magasin_repository import DjangoMagasinRepository
from ..infrastructure.http_produit_service import HttpProduitService
from ..infrastructure.http_stock_service import HttpStockService

# Models
from ..models import Magasin


class DDDVenteViewSet(viewsets.GenericViewSet):
    """
    ViewSet DDD pour les ventes
    Responsabilité: Orchestration des use cases métier via l'interface REST
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Injection de dépendances (à remplacer par un DI container en production)
        self._vente_repo = DjangoVenteRepository()
        self._magasin_repo = DjangoMagasinRepository()
        self._produit_service = HttpProduitService()
        # Service HTTP pour communication avec l'inventaire
        self._stock_service = HttpStockService()

    @swagger_auto_schema(
        operation_summary="Enregistrer une nouvelle vente (DDD)",
        operation_description="Use Case: Enregistrer une vente avec validation complète du domaine métier",
        tags=["Ventes DDD"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["magasin_id", "produit_id", "quantite", "client_id"],
            properties={
                "magasin_id": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_UUID,
                    description="ID du magasin où effectuer la vente",
                ),
                "produit_id": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_UUID,
                    description="ID du produit à vendre",
                ),
                "quantite": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    minimum=1,
                    description="Quantité à vendre",
                ),
                "client_id": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_UUID,
                    description="ID du client (obligatoire pour traçabilité)",
                ),
            },
        ),
        responses={
            201: openapi.Response(description="Vente enregistrée avec succès"),
            400: openapi.Response(description="Erreur de validation métier"),
        },
    )
    @action(detail=False, methods=["post"])
    def enregistrer(self, request):
        """Use Case: Enregistrer une vente"""
        
        import logging
        logger = logging.getLogger(__name__)

        # 1. Validation des données d'entrée
        try:
            data = request.data
            print(f"DEBUG: Données reçues: {data}")

            # Validation des champs requis
            required_fields = ["magasin_id", "produit_id", "quantite", "client_id"]
            for field in required_fields:
                if field not in data:
                    return Response(
                        {"error": f"Le champ '{field}' est requis"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            # Validation de la quantité
            quantite = int(data["quantite"])
            if quantite <= 0:
                print(f"DEBUG: Quantité invalide: {quantite}")
                return Response(
                    {"error": "La quantité doit être positive"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # 2. Construction de la commande métier (Value Object)
            # Conversion des IDs en types appropriés
            print(f"DEBUG: Conversion des IDs...")
            magasin_id = MagasinId(uuid.UUID(data["magasin_id"]))
            produit_id = ProduitId(uuid.UUID(data["produit_id"]))
            client_id = ClientId(uuid.UUID(data["client_id"]))  # Obligatoire maintenant

            print(f"DEBUG: Construction de CommandeVente...")
            commande = CommandeVente(
                magasin_id=magasin_id,
                produit_id=produit_id,
                quantite=quantite,
                client_id=client_id,
            )
            print(f"DEBUG: Commande créée: {commande}")

            # 3. Exécution du Use Case
            print(f"DEBUG: Création du Use Case...")
            use_case = EnregistrerVenteUseCase(
                self._vente_repo,
                self._magasin_repo,
                self._produit_service,
                self._stock_service,
            )

            print(f"DEBUG: Exécution du Use Case...")
            resultat = use_case.execute(commande)
            print(f"DEBUG: Résultat: {resultat}")

            # 📢 EVENT: Publication d'événement de succès
            logger.info("📢 EVENT: orders.command.creation.success", extra={
                "event_type": "orders.command.creation.success",
                "vente_id": resultat["vente"]["id"],
                "magasin_id": data["magasin_id"],
                "produit_id": data["produit_id"],
                "client_id": data["client_id"],
                "quantite": quantite,
                "total": resultat["vente"]["total"],
                "timestamp": "NOW"
            })

            return Response(resultat, status=status.HTTP_201_CREATED)

        except (ValueError, TypeError) as e:
            # 📢 EVENT: Publication d'événement d'échec
            logger.error("📢 EVENT: orders.command.creation.failed", extra={
                "event_type": "orders.command.creation.failed",
                "error": f"Format de données invalide: {str(e)}",
                "request_data": str(request.data),
                "timestamp": "NOW"
            })
            print(f"DEBUG: Erreur ValueError/TypeError: {e}")
            return Response(
                {"error": "Format de données invalide"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except MagasinInexistantError as e:
            # 📢 EVENT: Publication d'événement d'échec
            logger.error("📢 EVENT: orders.command.creation.failed", extra={
                "event_type": "orders.command.creation.failed",
                "error": f"Magasin invalide: {str(e)}",
                "reason": "magasin_inexistant",
                "timestamp": "NOW"
            })
            print(f"DEBUG: Erreur MagasinInexistantError: {e}")
            return Response(
                {"error": f"Magasin invalide: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except ProduitInexistantError as e:
            # 📢 EVENT: Publication d'événement d'échec
            logger.error("📢 EVENT: orders.command.creation.failed", extra={
                "event_type": "orders.command.creation.failed",
                "error": f"Produit invalide: {str(e)}",
                "reason": "produit_inexistant",
                "timestamp": "NOW"
            })
            print(f"DEBUG: Erreur ProduitInexistantError: {e}")
            return Response(
                {"error": f"Produit invalide: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except StockInsuffisantError as e:
            # 📢 EVENT: Publication d'événement d'échec
            logger.error("📢 EVENT: orders.command.creation.failed", extra={
                "event_type": "orders.command.creation.failed",
                "error": str(e),
                "reason": "stock_insuffisant",
                "timestamp": "NOW"
            })
            print(f"DEBUG: Erreur StockInsuffisantError: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # 📢 EVENT: Publication d'événement d'échec
            logger.error("📢 EVENT: orders.command.creation.failed", extra={
                "event_type": "orders.command.creation.failed",
                "error": f"Erreur interne: {str(e)}",
                "reason": "internal_error",
                "timestamp": "NOW"
            })
            print(f"DEBUG: Erreur générale: {e}")
            import traceback

            traceback.print_exc()
            return Response(
                {"error": f"Erreur interne: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        operation_summary="Annuler une vente (DDD)",
        operation_description="Use Case: Annuler une vente avec restauration automatique du stock",
        tags=["Ventes DDD"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["motif"],
            properties={
                "motif": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Motif de l'annulation"
                )
            },
        ),
        responses={
            200: openapi.Response(description="Vente annulée avec succès"),
            400: openapi.Response(description="Erreur métier (vente déjà annulée)"),
        },
    )
    @action(detail=True, methods=["patch"])
    def annuler(self, request, pk=None):
        """Use Case: Annuler une vente"""

        try:
            # 1. Validation des données d'entrée
            motif = request.data.get("motif", "Aucun motif spécifié")

            # 2. Exécution du Use Case
            use_case = AnnulerVenteUseCase(self._vente_repo, self._stock_service)

            resultat = use_case.execute(pk, motif)

            return Response(resultat, status=status.HTTP_200_OK)

        except VenteInvalideError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except VenteDejaAnnuleeError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": f"Erreur interne: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        operation_summary="Lister toutes les ventes (DDD)",
        operation_description="Use Case: Consulter la liste de toutes les ventes avec détails complets",
        tags=["Ventes DDD"],
        responses={
            200: openapi.Response(
                description="Liste des ventes récupérée avec succès",
                examples={
                    "application/json": {
                        "success": True,
                        "ventes": [
                            {
                                "id": "cfb04df5-91ac-499e-a289-6e9d0e807b1f",
                                "magasin": "Magasin Central",
                                "date_vente": "2025-06-30T22:00:33.537331",
                                "total": 269.97,
                                "client_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                                "statut": "active",
                                "lignes": [
                                    {
                                        "produit_id": "550e8400-e29b-41d4-a716-446655440001",
                                        "produit_nom": "Clavier mécanique",
                                        "quantite": 3,
                                        "prix_unitaire": 89.99,
                                        "sous_total": 269.97,
                                    }
                                ],
                            }
                        ],
                        "total_ventes": 1,
                    }
                },
            )
        },
    )
    def list(self, request):
        """Use Case: Lister toutes les ventes"""

        try:
            # Récupération de toutes les ventes
            ventes = self._vente_repo.get_all()

            # Conversion en format de réponse
            ventes_data = []
            for vente in ventes:
                # Récupération du nom du magasin
                magasin = self._magasin_repo.get_by_id(vente.magasin_id)
                magasin_nom = magasin.nom if magasin else f"Magasin {vente.magasin_id}"

                # Construction des lignes avec noms des produits
                lignes_data = []
                for ligne in vente.lignes:
                    produit_info = self._produit_service.get_produit_details(
                        ligne.produit_id
                    )
                    produit_nom = (
                        produit_info.nom
                        if produit_info
                        else f"Produit {ligne.produit_id}"
                    )

                    lignes_data.append(
                        {
                            "produit_id": str(ligne.produit_id),
                            "produit_nom": produit_nom,
                            "quantite": ligne.quantite,
                            "prix_unitaire": float(ligne.prix_unitaire),
                            "sous_total": float(ligne.sous_total),
                        }
                    )

                ventes_data.append(
                    {
                        "id": str(vente.id),
                        "magasin": magasin_nom,
                        "date_vente": vente.date_vente.isoformat(),
                        "total": float(vente.calculer_total()),
                        "client_id": str(vente.client_id) if vente.client_id else None,
                        "statut": vente.statut.value,
                        "lignes": lignes_data,
                        "date_annulation": (
                            vente.date_annulation.isoformat()
                            if vente.date_annulation
                            else None
                        ),
                        "motif_annulation": vente.motif_annulation,
                    }
                )

            return Response(
                {
                    "success": True,
                    "ventes": ventes_data,
                    "total_ventes": len(ventes_data),
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"error": f"Erreur lors de la récupération des ventes: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        operation_summary="Consulter une vente spécifique (DDD)",
        operation_description="Use Case: Récupérer les détails d'une vente par son ID",
        tags=["Ventes DDD"],
        responses={
            200: openapi.Response(description="Vente trouvée"),
            404: openapi.Response(description="Vente non trouvée"),
        },
    )
    def retrieve(self, request, pk=None):
        """Use Case: Consulter une vente spécifique"""

        try:
            vente = self._vente_repo.get_by_id(pk)

            if not vente:
                return Response(
                    {"error": f"Vente {pk} non trouvée"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Récupération du nom du magasin
            magasin = self._magasin_repo.get_by_id(vente.magasin_id)
            magasin_nom = magasin.nom if magasin else f"Magasin {vente.magasin_id}"

            # Construction des lignes avec noms des produits
            lignes_data = []
            for ligne in vente.lignes:
                produit_info = self._produit_service.get_produit_details(
                    ligne.produit_id
                )
                produit_nom = (
                    produit_info.nom if produit_info else f"Produit {ligne.produit_id}"
                )

                lignes_data.append(
                    {
                        "produit_id": str(ligne.produit_id),
                        "produit_nom": produit_nom,
                        "quantite": ligne.quantite,
                        "prix_unitaire": float(ligne.prix_unitaire),
                        "sous_total": float(ligne.sous_total),
                    }
                )

            vente_data = {
                "id": str(vente.id),
                "magasin": magasin_nom,
                "date_vente": vente.date_vente.isoformat(),
                "total": float(vente.calculer_total()),
                "client_id": str(vente.client_id) if vente.client_id else None,
                "statut": vente.statut.value,
                "lignes": lignes_data,
                "date_annulation": (
                    vente.date_annulation.isoformat() if vente.date_annulation else None
                ),
                "motif_annulation": vente.motif_annulation,
            }

            return Response(
                {"success": True, "vente": vente_data}, status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": f"Erreur lors de la récupération de la vente: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class DDDIndicateursAPI(APIView):
    """
    API DDD pour les indicateurs de performance
    Responsabilité: Orchestration du use case de génération d'indicateurs
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Injection de dépendances
        self._vente_repo = DjangoVenteRepository()
        self._magasin_repo = DjangoMagasinRepository()
        self._produit_service = HttpProduitService()
        # Service HTTP pour communication avec l'inventaire
        self._stock_service = HttpStockService()

    @swagger_auto_schema(
        operation_summary="Indicateurs de performance (DDD)",
        operation_description="Use Case: Générer les indicateurs de performance par magasin avec logique métier DDD",
        tags=["Indicateurs DDD"],
        responses={
            200: openapi.Response(
                description="Indicateurs générés avec succès",
                examples={
                    "application/json": [
                        {
                            "magasin": "Magasin Central",
                            "chiffre_affaires": 150.0,
                            "ruptures": 1,
                            "surstock": 2,
                            "tendances": "Clavier mécanique (2)",
                        }
                    ]
                },
            )
        },
    )
    def get(self, request):
        """Use Case: Générer les indicateurs de performance"""

        try:
            # Exécution du Use Case
            use_case = GenererIndicateursUseCase(
                self._vente_repo,
                self._magasin_repo,
                self._stock_service,
                self._produit_service,
            )

            indicateurs = use_case.execute()

            return Response(indicateurs, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"Erreur lors de la génération des indicateurs: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class DDDRapportConsolideAPI(APIView):
    """
    API DDD pour le rapport consolidé (UC1)
    Responsabilité: Orchestration du use case de génération du rapport consolidé
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Injection de dépendances
        self._vente_repo = DjangoVenteRepository()
        self._magasin_repo = DjangoMagasinRepository()
        self._produit_service = HttpProduitService()
        # Service HTTP pour communication avec l'inventaire
        self._stock_service = HttpStockService()

    @swagger_auto_schema(
        operation_summary="Rapport consolidé tous magasins (UC1 - DDD)",
        operation_description="Use Case: Générer le rapport consolidé avec analyse de performance et alertes métier",
        tags=["Rapport Consolidé DDD"],
        responses={
            200: openapi.Response(description="Rapport consolidé généré avec succès")
        },
    )
    def get(self, request):
        """Use Case: Générer le rapport consolidé tous magasins"""

        try:
            # Injection des dépendances
            vente_repo = DjangoVenteRepository()
            magasin_repo = DjangoMagasinRepository()
            produit_service = HttpProduitService()
            stock_service = HttpStockService()  # Service HTTP réel

            # Exécution du Use Case
            use_case = GenererRapportConsolideUseCase(
                vente_repo, magasin_repo, stock_service, produit_service
            )

            rapport = use_case.execute()

            return Response(rapport, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"Erreur lors de la génération du rapport: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@api_view(["GET"])
def rapport_consolide(request):
    """
    Endpoint: GET /api/v1/rapport-consolide/

    Cas d'usage métier: Génération du rapport consolidé (UC1)
    Ce rapport fournit une vue d'ensemble de la performance de tous les magasins
    avec analyses, alertes et recommandations intelligentes.
    """
    try:
        # Injection des dépendances
        vente_repo = DjangoVenteRepository()
        magasin_repo = DjangoMagasinRepository()
        produit_service = HttpProduitService()
        stock_service = HttpStockService()  # Service HTTP réel

        # Exécution du Use Case
        use_case = GenererRapportConsolideUseCase(
            vente_repo, magasin_repo, stock_service, produit_service
        )

        rapport = use_case.execute()

        return Response(rapport, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {"error": f"Erreur lors de la génération du rapport: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
def lister_magasins(request):
    """
    Endpoint: GET /api/v1/magasins/
    Retourne la liste des magasins avec UUID, nom, adresse.
    """
    try:
        magasins = Magasin.objects.all()
        magasins_data = [
            {"id": str(magasin.id), "nom": magasin.nom, "adresse": magasin.adresse}
            for magasin in magasins
        ]
        return Response(
            {"success": True, "magasins": magasins_data, "total": len(magasins_data)},
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        return Response(
            {
                "success": False,
                "error": f"Erreur lors de la récupération des magasins: {str(e)}",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
