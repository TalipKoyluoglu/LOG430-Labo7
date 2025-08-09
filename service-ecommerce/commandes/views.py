"""
APIs REST pour le module Check-out E-commerce
"""

import uuid
import logging
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger("commandes")


@api_view(["POST"])
@permission_classes([AllowAny])
def checkout_ecommerce(request, client_id):
    """
    API principale pour le check-out e-commerce

    POST /api/commandes/clients/{client_id}/checkout/
    {
        "adresse_livraison": {
            "nom_destinataire": "John Doe",
            "rue": "123 Rue Example",
            "ville": "Montréal",
            "code_postal": "H1A 1A1",
            "province": "QC",
            "pays": "Canada",
            "livraison_express": false
        },
        "notes": "Instructions spéciales"
    }
    """
    try:
        # Validation UUID (Django convertit automatiquement via <uuid:client_id>)
        if isinstance(client_id, uuid.UUID):
            client_uuid = client_id
        else:
            try:
                client_uuid = uuid.UUID(client_id)
            except ValueError:
                return Response(
                    {
                        "success": False,
                        "error": "UUID client invalide",
                        "details": f"Format UUID attendu, reçu: {client_id}",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Parsing des données
        try:
            if hasattr(request, "data") and request.data:
                data = request.data
            else:
                data = json.loads(request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return Response(
                {
                    "success": False,
                    "error": "JSON invalide dans le corps de la requête",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        adresse_data = data.get("adresse_livraison")

        # Si aucune adresse de livraison n'est fournie, utiliser celle du client
        if not adresse_data:
            try:
                from clients.models import ClientModel

                client = ClientModel.objects.get(id=client_uuid)
                adresse_data = {
                    "nom_destinataire": f"{client.prenom} {client.nom}",
                    "rue": client.adresse_rue,
                    "ville": client.adresse_ville,
                    "code_postal": client.adresse_code_postal,
                    "province": client.adresse_province,
                    "pays": client.adresse_pays,
                    "livraison_express": False,
                }
            except ClientModel.DoesNotExist:
                return Response(
                    {"success": False, "error": "Client introuvable"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        # Validation adresse obligatoire (après fallback)
        if not adresse_data:
            return Response(
                {"success": False, "error": "Adresse de livraison obligatoire"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validation champs adresse obligatoires
        champs_requis = ["nom_destinataire", "rue", "ville", "code_postal", "province"]
        champs_manquants = [
            champ for champ in champs_requis if not adresse_data.get(champ, "").strip()
        ]

        if champs_manquants:
            return Response(
                {
                    "success": False,
                    "error": "Champs adresse manquants",
                    "details": f'Champs requis manquants: {", ".join(champs_manquants)}',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Utilisation du vrai Use Case de check-out e-commerce
        try:
            from .application.use_cases.checkout_ecommerce_use_case import (
                CheckoutEcommerceUseCase,
            )
            from .domain.value_objects import DemandeCheckout, AdresseLivraison

            # Création de l'adresse de livraison (Value Object)
            adresse_livraison = AdresseLivraison(
                nom_destinataire=adresse_data["nom_destinataire"],
                rue=adresse_data["rue"],
                ville=adresse_data["ville"],
                code_postal=adresse_data["code_postal"],
                province=adresse_data["province"],
                pays=adresse_data.get("pays", "Canada"),
                instructions_livraison=adresse_data.get("instructions_livraison"),
                livraison_express=adresse_data.get("livraison_express", False),
            )

            # Création de la demande de checkout (Value Object)
            demande_checkout = DemandeCheckout(
                client_id=client_uuid,
                panier_id=client_uuid,  # Pour simplifier, même ID que client
                adresse_livraison=adresse_livraison,
                livraison_express=adresse_data.get("livraison_express", False),
                notes=data.get("notes"),
            )

            # Exécution du vrai check-out
            use_case = CheckoutEcommerceUseCase()
            resultat_checkout = use_case.execute(demande_checkout)

            # Publier l'événement de succès
            from .application.services.event_publisher import EcommerceEventPublisher
            publisher = EcommerceEventPublisher()
            # Publier d'abord l'initiation avec le checkout_id réel renvoyé
            publisher.publish_checkout_initiated(
                checkout_id=resultat_checkout["checkout_id"],
                client_id=str(client_uuid),
                panier_resume={"client_id": str(client_uuid)},
            )
            publisher.publish_checkout_succeeded(
                checkout_id=resultat_checkout["checkout_id"],
                commande_id=resultat_checkout["commande_id"],
            )

        except Exception as use_case_error:
            logger.error(f"Erreur Use Case checkout: {str(use_case_error)}")
            try:
                from .application.services.event_publisher import EcommerceEventPublisher
                EcommerceEventPublisher().publish_checkout_failed(
                    checkout_id=str(uuid.uuid4()),
                    reason=str(use_case_error),
                )
            except Exception:
                pass
            # Fallback en cas d'erreur du use case
            return Response(
                {
                    "success": False,
                    "error": "Erreur lors du traitement de la commande",
                    "details": str(use_case_error),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        logger.info(f"Check-out réel réussi pour client {client_id}")
        return Response(resultat_checkout, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Erreur lors du check-out pour client {client_id}: {str(e)}")
        return Response(
            {"success": False, "error": "Erreur interne du serveur", "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def verifier_prerequis_checkout(request, client_id):
    """
    Vérifie les prérequis pour le check-out

    GET /api/commandes/clients/{client_id}/checkout/prerequis/
    """
    try:
        # Validation UUID (Django convertit automatiquement via <uuid:client_id>)
        if isinstance(client_id, uuid.UUID):
            client_uuid = client_id
        else:
            try:
                client_uuid = uuid.UUID(client_id)
            except ValueError:
                return Response(
                    {"peut_commander": False, "error": "UUID client invalide"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Vraies vérifications des prérequis checkout
        try:
            from .application.services.panier_service import PanierService
            from .application.services.stock_service import StockService

            panier_service = PanierService()
            stock_service = StockService()

            # 1. Validation du panier
            panier_validation = panier_service.valider_panier_pour_checkout(
                str(client_uuid)
            )

            # 2. Vérification des stocks si le panier est valide
            stocks_validation = {"tous_suffisants": True, "stocks_insuffisants": []}
            if panier_validation["valide"]:
                produits_panier = panier_service.obtenir_produits_pour_stock(
                    str(client_uuid)
                )
                if produits_panier:
                    stocks_validation = stock_service.valider_stocks_suffisants(
                        produits_panier
                    )

            # Construction de la réponse
            peut_commander = (
                panier_validation["valide"] and stocks_validation["tous_suffisants"]
            )

            prerequis = {
                "peut_commander": peut_commander,
                "client_valide": True,  # Client UUID déjà validé
                "panier_valide": panier_validation["valide"],
                "stocks_suffisants": stocks_validation["tous_suffisants"],
                "details": {
                    "client": {"id": str(client_uuid), "status": "actif"},
                    "panier": {
                        "existe": panier_validation.get("panier", {}).get(
                            "panier_existe", False
                        ),
                        "nombre_articles": panier_validation.get("resume", {}).get(
                            "nombre_articles", 0
                        ),
                        "total": panier_validation.get("resume", {}).get("total", 0),
                        "raison_invalide": (
                            panier_validation.get("raison")
                            if not panier_validation["valide"]
                            else None
                        ),
                    },
                    "stocks": {
                        "tous_disponibles": stocks_validation["tous_suffisants"],
                        "produits_ok": stocks_validation.get("resume", {}).get(
                            "produits_ok", 0
                        ),
                        "produits_ko": stocks_validation.get("resume", {}).get(
                            "produits_ko", 0
                        ),
                        "stocks_insuffisants": stocks_validation.get(
                            "stocks_insuffisants", []
                        ),
                    },
                },
            }

        except Exception as verification_error:
            logger.error(f"Erreur vérification prérequis: {str(verification_error)}")
            prerequis = {
                "peut_commander": False,
                "client_valide": True,
                "panier_valide": False,
                "stocks_suffisants": False,
                "error": f"Erreur lors de la vérification: {str(verification_error)}",
            }

        return Response(prerequis, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Erreur lors de la vérification des prérequis: {str(e)}")
        return Response(
            {
                "peut_commander": False,
                "error": "Erreur lors de la vérification",
                "details": str(e),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def historique_commandes_client(request, client_id):
    """
    Récupère l'historique des commandes d'un client

    GET /api/commandes/clients/{client_id}/historique/

    Query params:
    - limite: nombre maximum de commandes (défaut: 50)
    """
    try:
        # Validation UUID (Django convertit automatiquement via <uuid:client_id>)
        if isinstance(client_id, uuid.UUID):
            client_uuid = client_id
        else:
            try:
                client_uuid = uuid.UUID(client_id)
            except ValueError:
                return Response(
                    {
                        "error": "UUID client invalide",
                        "details": f"Format UUID attendu, reçu: {client_id}",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Récupération du paramètre limite
        limite = int(request.GET.get("limite", 50))
        if limite <= 0 or limite > 100:
            limite = 50

        # Utilisation du Use Case pour récupérer l'historique
        try:
            from .application.use_cases.lister_commandes_client_use_case import (
                ListerCommandesClientUseCase,
            )
            from .infrastructure.django_commande_ecommerce_repository import (
                DjangoCommandeEcommerceRepository,
            )

            repository = DjangoCommandeEcommerceRepository()
            use_case = ListerCommandesClientUseCase(repository)

            historique = use_case.execute(str(client_uuid), limite)

            logger.info(
                f"Historique récupéré pour client {client_id}: {historique['statistiques']['nombre_commandes']} commandes"
            )

            return Response(historique, status=status.HTTP_200_OK)

        except Exception as use_case_error:
            logger.error(f"Erreur Use Case historique: {str(use_case_error)}")
            return Response(
                {
                    "error": "Erreur lors de la récupération de l'historique",
                    "details": str(use_case_error),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    except Exception as e:
        logger.error(
            f"Erreur lors de la récupération de l'historique pour client {client_id}: {str(e)}"
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def checkout_ecommerce_choreo(request, client_id):
    """
    Variante chorégraphiée: publie uniquement l'événement d'initiation
    et retourne un 202 Accepted avec un checkout_id pour suivi via Event Store.
    """
    try:
        client_uuid = str(uuid.UUID(str(client_id)))
    except ValueError:
        return Response({"error": "UUID client invalide"}, status=status.HTTP_400_BAD_REQUEST)

    from .application.services.event_publisher import EcommerceEventPublisher
    from .application.services.panier_service import PanierService
    import uuid as _uuid

    checkout_id = str(_uuid.uuid4())
    publisher = EcommerceEventPublisher()
    panier = PanierService().recuperer_panier_client(client_uuid)
    # métriques saga chorégraphiée
    try:
        from lab7.common.metrics import saga_choreo_started_total
        saga_choreo_started_total.labels(source="ecommerce").inc()
    except Exception:
        pass

    publisher.publish_checkout_initiated(
        checkout_id=checkout_id,
        client_id=client_uuid,
        panier_resume={
            "client_id": client_uuid,
            "nombre_articles": panier.get("nombre_articles", 0),
            "total": panier.get("total", 0.0),
            "produits": panier.get("produits", []),
        },
    )

    return Response({
        "accepted": True,
        "checkout_id": checkout_id,
        "follow": f"http://localhost:7010/api/event-store/replay/checkout/{checkout_id}"
    }, status=status.HTTP_202_ACCEPTED)
