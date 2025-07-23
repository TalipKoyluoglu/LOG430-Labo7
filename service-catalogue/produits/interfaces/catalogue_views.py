"""
API REST DDD pour le Catalogue
Orchestration des Use Cases métier (pas de logique technique)
"""

from decimal import Decimal
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import os

from ..application.use_cases.rechercher_produits_use_case import (
    RechercherProduitsUseCase,
)
from ..application.use_cases.ajouter_produit_use_case import AjouterProduitUseCase
from ..infrastructure.django_produit_repository import DjangoProduitRepository
from ..infrastructure.django_categorie_repository import DjangoCategorieRepository
from ..domain.value_objects import (
    CritereRecherche,
    CommandeProduit,
    NomProduit,
    PrixMonetaire,
    CategorieId,
    CommandeProduitSimple,
)
from ..domain.exceptions import (
    CatalogueError,
    ProduitDejaExistantError,
    CategorieInexistanteError,
    CriteresRechercheInvalidesError,
)


class DDDCatalogueAPI(APIView):
    """
    API DDD pour le Catalogue - Orchestration pure des Use Cases
    """

    def __init__(self):
        # Injection de dépendances (pattern DDD)
        self.produit_repo = DjangoProduitRepository()
        self.categorie_repo = DjangoCategorieRepository()

        # Instanciation des Use Cases
        self.rechercher_use_case = RechercherProduitsUseCase(
            self.produit_repo, self.categorie_repo
        )
        self.ajouter_use_case = AjouterProduitUseCase(
            self.produit_repo, self.categorie_repo
        )

    @swagger_auto_schema(
        operation_summary="Rechercher des produits (DDD)",
        operation_description="""
        Recherche intelligente de produits avec logique métier DDD.
        
        **Fonctionnalités métier:**
        - Recherche floue par nom/description
        - Filtrage par catégorie (avec sous-catégories)
        - Filtrage par fourchette de prix
        - Tri par pertinence métier
        - Métadonnées enrichies (prix moyen, nb premium, etc.)
        
        **Architecture DDD:** Cette API orchestre le Use Case RechercherProduitsUseCase
        """,
        manual_parameters=[
            openapi.Parameter(
                "nom",
                openapi.IN_QUERY,
                description="Recherche par nom",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "categorie_id",
                openapi.IN_QUERY,
                description="Filtrer par catégorie",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "prix_min",
                openapi.IN_QUERY,
                description="Prix minimum",
                type=openapi.TYPE_NUMBER,
            ),
            openapi.Parameter(
                "prix_max",
                openapi.IN_QUERY,
                description="Prix maximum",
                type=openapi.TYPE_NUMBER,
            ),
            openapi.Parameter(
                "actifs_seulement",
                openapi.IN_QUERY,
                description="Seulement produits actifs",
                type=openapi.TYPE_BOOLEAN,
                default=True,
            ),
        ],
        tags=["Catalogue DDD"],
    )
    def get(self, request):
        """
        GET /api/ddd/catalogue/rechercher/ - Recherche DDD
        """
        try:
            # 1. Construction du Value Object CritereRecherche
            criteres = self._build_criteres_recherche(request.query_params)

            # 2. Exécution du Use Case (format simple par défaut)
            resultats = self.rechercher_use_case.execute(criteres)

            # 3. Retour direct des résultats simplifiés
            return Response(
                {
                    "success": True,
                    "data": resultats,
                    "instance_id": os.environ.get("INSTANCE_ID", "unknown"),
                },
                status=status.HTTP_200_OK,
            )

        except CriteresRechercheInvalidesError as e:
            return Response(
                {
                    "success": False,
                    "error": "Critères de recherche invalides",
                    "details": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except CatalogueError as e:
            return Response(
                {
                    "success": False,
                    "error": "Erreur métier catalogue",
                    "details": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            return Response(
                {
                    "success": False,
                    "error": "Erreur interne du serveur",
                    "details": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        operation_summary="Ajouter un produit (DDD)",
        operation_description="""
        Ajoute un nouveau produit au catalogue avec validation métier complète.
        
        **Validations métier DDD:**
        - Unicité du nom de produit
        - Unicité du SKU (si fourni)
        - Validation de l'existence de la catégorie
        - Validation du format des données (Value Objects)
        - Règles métier intégrées dans les entités
        
        **Architecture DDD:** Cette API orchestre le Use Case AjouterProduitUseCase
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "nom": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Nom du produit (2-100 caractères)",
                ),
                "categorie": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Nom de catégorie (Informatique, Boissons, Confiserie, etc.)",
                ),
                "prix": openapi.Schema(
                    type=openapi.TYPE_NUMBER,
                    description="Prix en euros (max 999999.99)",
                ),
                "description": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Description du produit"
                ),
            },
            required=["nom", "categorie", "prix"],
        ),
        tags=["Catalogue DDD"],
    )
    def post(self, request):
        """
        POST /api/ddd/catalogue/ajouter/ - Ajout DDD
        """
        try:
            # 1. Construction du Value Object CommandeProduit
            commande = self._build_commande_produit(request.data)

            # 2. Exécution du Use Case (toute la logique métier)
            produit_cree = self.ajouter_use_case.execute(commande)

            # 3. Retour des données du produit créé
            return Response(
                {"success": True, "data": produit_cree}, status=status.HTTP_201_CREATED
            )

        except ProduitDejaExistantError as e:
            return Response(
                {"success": False, "error": "Produit déjà existant", "details": str(e)},
                status=status.HTTP_409_CONFLICT,
            )

        except CategorieInexistanteError as e:
            return Response(
                {"success": False, "error": "Catégorie inexistante", "details": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except CatalogueError as e:
            return Response(
                {
                    "success": False,
                    "error": "Erreur métier catalogue",
                    "details": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except ValueError as e:
            return Response(
                {"success": False, "error": "Données invalides", "details": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            return Response(
                {
                    "success": False,
                    "error": "Erreur interne du serveur",
                    "details": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _build_criteres_recherche(self, query_params) -> CritereRecherche:
        """
        Construit le Value Object CritereRecherche depuis les paramètres HTTP
        """
        import uuid

        # Extraction des paramètres avec valeurs par défaut
        nom = query_params.get("nom", "").strip()

        categorie_id = None
        if query_params.get("categorie_id"):
            try:
                categorie_id = CategorieId(uuid.UUID(query_params.get("categorie_id")))
            except ValueError:
                raise CriteresRechercheInvalidesError(
                    "categorie_id doit être un UUID valide"
                )

        prix_min = None
        if query_params.get("prix_min"):
            try:
                prix_min = Decimal(query_params.get("prix_min"))
            except (ValueError, TypeError):
                raise CriteresRechercheInvalidesError(
                    "prix_min doit être un nombre valide"
                )

        prix_max = None
        if query_params.get("prix_max"):
            try:
                prix_max = Decimal(query_params.get("prix_max"))
            except (ValueError, TypeError):
                raise CriteresRechercheInvalidesError(
                    "prix_max doit être un nombre valide"
                )

        actifs_seulement = (
            query_params.get("actifs_seulement", "true").lower() == "true"
        )

        # Construction du Value Object (validation automatique)
        return CritereRecherche(
            nom=nom,
            categorie_id=categorie_id,
            prix_min=prix_min,
            prix_max=prix_max,
            actifs_seulement=actifs_seulement,
        )

    def _build_commande_produit(self, data) -> CommandeProduitSimple:
        """
        Construit le Value Object CommandeProduitSimple depuis les données HTTP
        """
        from ..domain.value_objects import ReferenceSKU

        # Validation et construction des Value Objects
        try:
            nom = NomProduit(data.get("nom", ""))
        except Exception as e:
            raise ValueError(f"Nom invalide: {e}")

        # Récupération du nom de catégorie (string au lieu d'UUID)
        categorie = data.get("categorie", "").strip()
        if not categorie:
            raise ValueError("Le nom de catégorie est obligatoire")

        try:
            prix = PrixMonetaire(Decimal(str(data.get("prix", 0))))
        except Exception as e:
            raise ValueError(f"Prix invalide: {e}")

        description = data.get("description", "").strip()

        sku = None
        if data.get("sku"):
            try:
                sku = ReferenceSKU(data.get("sku"))
            except Exception as e:
                raise ValueError(f"SKU invalide: {e}")

        # Construction du Value Object CommandeProduitSimple (validation automatique)
        return CommandeProduitSimple(
            nom=nom, categorie=categorie, prix=prix, description=description, sku=sku
        )


@swagger_auto_schema(
    method="get",
    operation_summary="Health Check Catalogue DDD",
    operation_description="""
    Vérification de l'état du service Catalogue DDD.
    
    Confirme que l'architecture DDD est opérationnelle.
    """,
    tags=["Health Check"],
)
@api_view(["GET"])
def catalogue_health_check(request):
    """
    Health check simple pour vérifier que le service est actif
    """
    return Response(
        {
            "status": "healthy",
            "service": "Service Catalogue DDD",
            "architecture": "Domain-Driven Design",
            "bounded_context": "Information Produits",
        },
        status=status.HTTP_200_OK,
    )


@swagger_auto_schema(
    method="get",
    operation_summary="Récupérer un produit par ID",
    operation_description="""
    Récupère les détails d'un produit spécifique par son ID.
    
    **Utilisé pour la communication inter-services.**
    """,
    tags=["Catalogue DDD"],
)
@api_view(["GET"])
def get_produit_by_id(request, produit_id):
    """
    GET /api/ddd/catalogue/produits/{id}/ - Récupération d'un produit
    """
    try:
        # Injection de dépendances (pattern DDD)
        produit_repo = DjangoProduitRepository()

        # Récupération du produit
        produit = produit_repo.get_by_id(produit_id)

        if produit is None:
            return Response(
                {"success": False, "error": f"Produit {produit_id} non trouvé"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Retour des données du produit
        return Response(
            {
                "id": str(produit.id),
                "nom": produit.nom.valeur,
                "prix": float(produit.prix.montant),
                "description": produit.description,
                "sku": produit.sku.code if produit.sku else None,
                "actif": produit.est_actif,
                "date_creation": (
                    produit.date_creation.isoformat() if produit.date_creation else None
                ),
            },
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        return Response(
            {"success": False, "error": "Erreur interne du serveur", "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
