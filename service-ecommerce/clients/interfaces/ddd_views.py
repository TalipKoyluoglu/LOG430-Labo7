"""
Vues REST DDD pour le module Clients E-commerce
Interface layer - Orchestre les Use Cases
"""

import uuid
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404

from ..application.use_cases.creer_compte_client_use_case import (
    CreerCompteClientUseCase,
)
from ..application.use_cases.valider_client_use_case import ValiderClientUseCase
from ..application.use_cases.lister_clients_use_case import ListerClientsUseCase
from ..infrastructure.django_client_repository import DjangoClientRepository
from ..domain.value_objects import CommandeCreationClient, Email, NomComplet, Adresse
from ..domain.exceptions import (
    ClientInexistantError,
    ClientInactifError,
    EmailDejaUtiliseError,
    DonneesClientInvalidesError,
)

logger = logging.getLogger("clients")


class DDDClientViewSet(viewsets.GenericViewSet):
    """
    ViewSet DDD pour les clients e-commerce
    Orchestre les Use Cases sans logique métier
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Injection de dépendance - Repository
        self._client_repo = DjangoClientRepository()

    @swagger_auto_schema(
        operation_summary="Créer un compte client ",
        operation_description="Use Case: Créer un nouveau compte client avec validation complète du domaine métier",
        tags=["Clients"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=[
                "prenom",
                "nom",
                "email",
                "adresse_rue",
                "adresse_ville",
                "adresse_code_postal",
            ],
            properties={
                "prenom": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Prénom du client"
                ),
                "nom": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Nom du client"
                ),
                "email": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_EMAIL,
                    description="Email unique",
                ),
                "telephone": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Téléphone (optionnel)"
                ),
                "adresse_rue": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Adresse rue"
                ),
                "adresse_ville": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Ville"
                ),
                "adresse_code_postal": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Code postal canadien"
                ),
                "adresse_province": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Province (défaut: Québec)"
                ),
                "adresse_pays": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Pays (défaut: Canada)"
                ),
            },
        ),
        responses={
            201: openapi.Response(description="Compte client créé avec succès"),
            400: openapi.Response(description="Données invalides"),
            409: openapi.Response(description="Email déjà utilisé"),
        },
    )
    def create(self, request):
        """Use Case: Créer un compte client"""

        try:
            data = request.data
            logger.info(f"Demande création compte client: {data.get('email')}")

            # Validation des champs requis
            required_fields = [
                "prenom",
                "nom",
                "email",
                "adresse_rue",
                "adresse_ville",
                "adresse_code_postal",
            ]
            for field in required_fields:
                if not data.get(field):
                    return Response(
                        {"error": f"Champ requis manquant: {field}"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            # Construction des value objects
            nom_complet = NomComplet(prenom=data["prenom"], nom=data["nom"])

            email = Email(data["email"])

            adresse = Adresse(
                rue=data["adresse_rue"],
                ville=data["adresse_ville"],
                code_postal=data["adresse_code_postal"],
                province=data.get("adresse_province", "Québec"),
                pays=data.get("adresse_pays", "Canada"),
            )

            # Construction de la commande
            commande = CommandeCreationClient(
                nom_complet=nom_complet,
                email=email,
                adresse=adresse,
                telephone=data.get("telephone"),
            )

            # Exécution du Use Case
            use_case = CreerCompteClientUseCase(self._client_repo)
            resultat = use_case.execute(commande)

            return Response(resultat, status=status.HTTP_201_CREATED)

        except EmailDejaUtiliseError as e:
            return Response({"error": str(e)}, status=status.HTTP_409_CONFLICT)
        except DonneesClientInvalidesError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            return Response(
                {"error": f"Données invalides: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"Erreur lors de la création du compte: {str(e)}")
            return Response(
                {"error": "Erreur interne du serveur"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        operation_summary="Lister tous les clients ",
        operation_description="Use Case: Récupérer la liste de tous les clients actifs avec leurs informations complètes",
        tags=["Clients"],
        responses={
            200: openapi.Response(
                description="Liste des clients récupérée avec succès",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "id": openapi.Schema(
                                type=openapi.TYPE_STRING, description="UUID du client"
                            ),
                            "nom_complet": openapi.Schema(
                                type=openapi.TYPE_STRING,
                                description="Nom complet du client",
                            ),
                            "email": openapi.Schema(
                                type=openapi.TYPE_STRING, description="Email du client"
                            ),
                            "telephone": openapi.Schema(
                                type=openapi.TYPE_STRING,
                                description="Téléphone (peut être null)",
                            ),
                            "adresse": openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "rue": openapi.Schema(type=openapi.TYPE_STRING),
                                    "ville": openapi.Schema(type=openapi.TYPE_STRING),
                                    "code_postal": openapi.Schema(
                                        type=openapi.TYPE_STRING
                                    ),
                                    "province": openapi.Schema(
                                        type=openapi.TYPE_STRING
                                    ),
                                    "pays": openapi.Schema(type=openapi.TYPE_STRING),
                                    "adresse_complete": openapi.Schema(
                                        type=openapi.TYPE_STRING
                                    ),
                                },
                            ),
                            "date_creation": openapi.Schema(
                                type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME
                            ),
                            "date_modification": openapi.Schema(
                                type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME
                            ),
                            "actif": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        },
                    ),
                ),
            )
        },
    )
    def list(self, request):
        """Use Case: Lister tous les clients actifs"""

        try:
            logger.info("Demande de liste des clients")

            # Exécution du Use Case
            use_case = ListerClientsUseCase(self._client_repo)
            clients_data = use_case.execute()

            return Response({"count": len(clients_data), "clients": clients_data})

        except Exception as e:
            logger.error(
                f"Erreur lors de la récupération de la liste des clients: {str(e)}"
            )
            return Response(
                {"error": "Erreur interne du serveur"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ValiderClientView(APIView):
    """
    API pour valider l'existence d'un client (utilisée par service-commandes)
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._client_repo = DjangoClientRepository()

    @swagger_auto_schema(
        operation_summary="Valider l'existence d'un client",
        operation_description="Use Case: Vérifier qu'un client existe et peut passer commande",
        tags=["Clients"],
        responses={
            200: openapi.Response(
                description="Client valide",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "valid": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "client_id": openapi.Schema(type=openapi.TYPE_STRING),
                        "nom_complet": openapi.Schema(type=openapi.TYPE_STRING),
                        "email": openapi.Schema(type=openapi.TYPE_STRING),
                        "adresse_livraison": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
            404: openapi.Response(description="Client non trouvé"),
            400: openapi.Response(description="Client inactif"),
        },
    )
    def get(self, request, client_id):
        """
        Use Case: Valider un client pour commande
        """
        try:
            # Conversion UUID - gérer le cas où Django a déjà converti
            if isinstance(client_id, uuid.UUID):
                client_uuid = client_id
            else:
                try:
                    client_uuid = uuid.UUID(client_id)
                except ValueError:
                    return Response(
                        {"error": "Format UUID invalide"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            # Exécution du Use Case
            use_case = ValiderClientUseCase(self._client_repo)
            resultat = use_case.execute(client_uuid)

            return Response(resultat)

        except ClientInexistantError as e:
            return Response(
                {"valid": False, "error": str(e)}, status=status.HTTP_404_NOT_FOUND
            )
        except ClientInactifError as e:
            return Response(
                {"valid": False, "error": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Erreur lors de la validation du client: {str(e)}")
            return Response(
                {"error": "Erreur interne du serveur"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
