"""
Vues REST DDD pour la gestion du panier d'achat
Interface layer - APIs REST avec communications inter-services
"""

import uuid
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..application.use_cases.ajouter_produit_panier_use_case import (
    AjouterProduitPanierUseCase,
)
from ..application.use_cases.voir_panier_use_case import VoirPanierUseCase
from ..application.use_cases.modifier_quantite_panier_use_case import (
    ModifierQuantitePanierUseCase,
)
from ..application.use_cases.vider_panier_use_case import ViderPanierUseCase
from ..application.services.catalogue_service import CatalogueService
from ..application.services.stock_service import StockService
from ..infrastructure.django_panier_repository import DjangoPanierRepository
from ..domain.value_objects import CommandeAjoutPanier, QuantiteProduit
from ..domain.exceptions import (
    ProduitInexistantError,
    StockInsuffisantError,
    ProduitNonTrouveError,
    PanierVideError,
)

logger = logging.getLogger("panier")


class PanierView(APIView):
    """
    API REST pour la gestion du panier d'achat
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Injection de dépendances DDD
        self.panier_repo = DjangoPanierRepository()
        self.catalogue_service = CatalogueService()
        self.stock_service = StockService()

    @swagger_auto_schema(
        operation_description="Récupère le contenu du panier d'un client",
        responses={
            200: openapi.Response(
                description="Contenu du panier",
                examples={
                    "application/json": {
                        "panier_existe": True,
                        "est_vide": False,
                        "panier_id": "123e4567-e89b-12d3-a456-426614174000",
                        "client_id": "456e7890-e89b-12d3-a456-426614174001",
                        "produits": [
                            {
                                "produit_id": "789e0123-e89b-12d3-a456-426614174002",
                                "nom_produit": "Produit exemple",
                                "prix_unitaire": 29.99,
                                "quantite": 2,
                                "prix_ligne": 59.98,
                            }
                        ],
                        "resume": {
                            "nombre_articles": 2,
                            "prix_total": 59.98,
                            "nombre_produits_differents": 1,
                        },
                    }
                },
            ),
            404: "Client non trouvé",
        },
    )
    def get(self, request, client_id):
        """Consulter le panier d'un client"""
        try:
            # Django convertit automatiquement <uuid:client_id> en objet UUID
            client_uuid = (
                client_id if isinstance(client_id, uuid.UUID) else uuid.UUID(client_id)
            )

            use_case = VoirPanierUseCase(self.panier_repo)
            resultat = use_case.execute(client_uuid)

            return Response(resultat, status=status.HTTP_200_OK)

        except ValueError:
            return Response(
                {"error": "UUID client invalide"}, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Erreur consultation panier: {str(e)}")
            return Response(
                {"error": "Erreur lors de la consultation du panier"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        operation_description="Ajoute un produit au panier avec vérification stock e-commerce",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["produit_id", "quantite"],
            properties={
                "produit_id": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format="uuid",
                    description="UUID du produit à ajouter",
                ),
                "quantite": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    minimum=1,
                    maximum=99,
                    description="Quantité à ajouter (1-99)",
                ),
            },
        ),
        responses={
            201: openapi.Response(
                description="Produit ajouté avec succès",
                examples={
                    "application/json": {
                        "success": True,
                        "panier_id": "123e4567-e89b-12d3-a456-426614174000",
                        "client_id": "456e7890-e89b-12d3-a456-426614174001",
                        "produit_ajoute": {
                            "produit_id": "789e0123-e89b-12d3-a456-426614174002",
                            "nom_produit": "Produit exemple",
                            "quantite_ajoutee": 2,
                            "prix_unitaire": 29.99,
                        },
                        "panier_resume": {
                            "nombre_articles": 2,
                            "prix_total": 59.98,
                            "nombre_produits_differents": 1,
                        },
                    }
                },
            ),
            400: "Données invalides ou stock insuffisant",
            404: "Produit non trouvé dans le catalogue",
        },
    )
    def post(self, request, client_id):
        """Ajouter un produit au panier"""
        try:
            # Django convertit automatiquement <uuid:client_id> en objet UUID
            client_uuid = (
                client_id if isinstance(client_id, uuid.UUID) else uuid.UUID(client_id)
            )

            # Valider les données d'entrée
            produit_id = request.data.get("produit_id")
            quantite = request.data.get("quantite")

            if not produit_id or not quantite:
                return Response(
                    {"error": "produit_id et quantite sont obligatoires"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            produit_uuid = uuid.UUID(produit_id)
            quantite_obj = QuantiteProduit(int(quantite))

            # Créer la commande d'ajout
            commande_ajout = CommandeAjoutPanier(
                produit_id=produit_uuid, quantite=quantite_obj
            )

            # Exécuter le use case
            use_case = AjouterProduitPanierUseCase(
                self.panier_repo, self.catalogue_service, self.stock_service
            )

            resultat = use_case.execute(client_uuid, commande_ajout)

            return Response(resultat, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return Response(
                {"error": f"Données invalides: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except ProduitInexistantError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except StockInsuffisantError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Erreur ajout produit panier: {str(e)}")
            return Response(
                {"error": "Erreur lors de l'ajout au panier"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        operation_description="Vide complètement le panier d'un client",
        responses={
            200: openapi.Response(
                description="Panier vidé avec succès",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Panier vidé avec succès",
                        "client_id": "456e7890-e89b-12d3-a456-426614174001",
                        "articles_supprimes": 5,
                        "valeur_supprimee": 149.95,
                    }
                },
            )
        },
    )
    def delete(self, request, client_id):
        """Vider le panier d'un client"""
        try:
            # Django convertit automatiquement <uuid:client_id> en objet UUID
            client_uuid = (
                client_id if isinstance(client_id, uuid.UUID) else uuid.UUID(client_id)
            )

            use_case = ViderPanierUseCase(self.panier_repo)
            resultat = use_case.execute(client_uuid)

            return Response(resultat, status=status.HTTP_200_OK)

        except ValueError:
            return Response(
                {"error": "UUID client invalide"}, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Erreur vidage panier: {str(e)}")
            return Response(
                {"error": "Erreur lors du vidage du panier"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PanierProduitView(APIView):
    """
    API REST pour gérer un produit spécifique dans le panier
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.panier_repo = DjangoPanierRepository()
        self.stock_service = StockService()

    @swagger_auto_schema(
        operation_description="Modifie la quantité d'un produit dans le panier (0 = retirer)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["quantite"],
            properties={
                "quantite": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    minimum=0,
                    maximum=99,
                    description="Nouvelle quantité (0 pour retirer le produit)",
                ),
            },
        ),
        responses={
            200: "Quantité modifiée avec succès",
            400: "Quantité invalide ou stock insuffisant",
            404: "Produit non trouvé dans le panier",
        },
    )
    def put(self, request, client_id, produit_id):
        """Modifier la quantité d'un produit dans le panier"""
        try:
            # Django convertit automatiquement les UUIDs
            client_uuid = (
                client_id if isinstance(client_id, uuid.UUID) else uuid.UUID(client_id)
            )
            produit_uuid = (
                produit_id
                if isinstance(produit_id, uuid.UUID)
                else uuid.UUID(produit_id)
            )

            quantite = request.data.get("quantite")
            if quantite is None:
                return Response(
                    {"error": "quantite est obligatoire"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            use_case = ModifierQuantitePanierUseCase(
                self.panier_repo, self.stock_service
            )

            resultat = use_case.execute(client_uuid, produit_uuid, int(quantite))

            return Response(resultat, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response(
                {"error": f"Données invalides: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except ProduitNonTrouveError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except StockInsuffisantError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Erreur modification quantité: {str(e)}")
            return Response(
                {"error": "Erreur lors de la modification"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
