"""
Use Case: Rechercher des Produits
Fonctionnalité métier complète pour rechercher dans le catalogue
"""

from typing import List, Dict, Any
from decimal import Decimal

from ..repositories.produit_repository import ProduitRepository
from ..repositories.categorie_repository import CategorieRepository
from ...domain.entities import Produit
from ...domain.value_objects import CritereRecherche, CategorieId
from ...domain.exceptions import CriteresRechercheInvalidesError


class RechercherProduitsUseCase:
    """
    Use Case: Recherche intelligente de produits dans le catalogue

    Orchestration complète de la fonctionnalité métier:
    1. Validation des critères de recherche
    2. Application des filtres métier
    3. Recherche par nom (avec logique floue)
    4. Filtrage par catégorie (avec sous-catégories)
    5. Filtrage par prix (avec logique métier)
    6. Tri et pertinence
    """

    def __init__(
        self,
        produit_repository: ProduitRepository,
        categorie_repository: CategorieRepository,
    ):
        self._produit_repo = produit_repository
        self._categorie_repo = categorie_repository

    def execute(self, criteres: CritereRecherche) -> Dict[str, Any]:
        """
        Exécute la recherche de produits selon les critères

        Args:
            criteres: CritereRecherche avec filtres souhaités

        Returns:
            Dict contenant les produits au format simplifié
        """

        # 1. Validation des critères (règles métier)
        self._valider_criteres(criteres)

        # 2. Récupération de base selon les filtres actifs/inactifs
        if criteres.actifs_seulement:
            produits = self._produit_repo.get_produits_actifs()
        else:
            produits = self._produit_repo.get_all()

        # 3. Application des filtres métier
        produits_filtres = self._appliquer_filtres(produits, criteres)

        # 4. Calcul de la pertinence et tri
        produits_tries = self._calculer_pertinence_et_trier(produits_filtres, criteres)

        # 5. Retour au format simplifié (par défaut)
        return {"produits": [self._produit_to_dict_simple(p) for p in produits_tries]}

    def _valider_criteres(self, criteres: CritereRecherche) -> None:
        """
        Valide les critères de recherche (règles métier)
        """
        # Le VO CritereRecherche fait déjà la validation de base

        # Validation métier supplémentaire : vérifier existence catégorie
        if criteres.a_filtre_categorie():
            categorie = self._categorie_repo.get_by_id(criteres.categorie_id)
            if not categorie:
                raise CriteresRechercheInvalidesError(
                    f"Catégorie {criteres.categorie_id} non trouvée"
                )

            if not categorie.est_active:
                raise CriteresRechercheInvalidesError(
                    f"Catégorie {criteres.categorie_id} est désactivée"
                )

    def _appliquer_filtres(
        self, produits: List[Produit], criteres: CritereRecherche
    ) -> List[Produit]:
        """
        Applique tous les filtres métier sur la liste de produits
        """
        produits_filtres = produits.copy()

        # Filtre par nom (recherche floue)
        if criteres.a_filtre_nom():
            produits_filtres = self._filtrer_par_nom(produits_filtres, criteres.nom)

        # Filtre par catégorie (avec sous-catégories)
        if criteres.a_filtre_categorie():
            produits_filtres = self._filtrer_par_categorie(
                produits_filtres, criteres.categorie_id
            )

        # Filtre par prix (logique métier)
        if criteres.a_filtre_prix():
            produits_filtres = self._filtrer_par_prix(
                produits_filtres, criteres.prix_min, criteres.prix_max
            )

        return produits_filtres

    def _filtrer_par_nom(
        self, produits: List[Produit], terme_recherche: str
    ) -> List[Produit]:
        """
        Filtre par nom avec logique de recherche floue (métier)
        """
        terme = terme_recherche.lower().strip()
        resultats = []

        for produit in produits:
            nom_produit = produit.nom.valeur.lower()
            description = produit.description.lower()

            # Correspondance exacte (priorité haute)
            if terme in nom_produit:
                resultats.append((produit, 3))
            # Correspondance dans description (priorité moyenne)
            elif terme in description:
                resultats.append((produit, 2))
            # Correspondance partielle mots (priorité faible)
            elif any(mot.startswith(terme) for mot in nom_produit.split()):
                resultats.append((produit, 1))

        # Retourne les produits triés par pertinence
        resultats.sort(key=lambda x: x[1], reverse=True)
        return [produit for produit, _ in resultats]

    def _filtrer_par_categorie(
        self, produits: List[Produit], categorie_id: CategorieId
    ) -> List[Produit]:
        """
        Filtre par catégorie en incluant les sous-catégories (logique métier)
        """
        # Récupération de la catégorie et ses sous-catégories
        categorie = self._categorie_repo.get_by_id(categorie_id)
        categories_incluees = [categorie_id]

        if categorie and categorie.a_des_sous_categories():
            categories_incluees.extend(categorie.sous_categories)

        # Filtrage des produits
        return [
            produit
            for produit in produits
            if produit.categorie_id in categories_incluees
        ]

    def _filtrer_par_prix(
        self, produits: List[Produit], prix_min: Decimal, prix_max: Decimal
    ) -> List[Produit]:
        """
        Filtre par fourchette de prix (logique métier)
        """
        return [
            produit
            for produit in produits
            if self._prix_dans_fourchette(produit.prix.montant, prix_min, prix_max)
        ]

    def _prix_dans_fourchette(
        self, prix: Decimal, prix_min: Decimal, prix_max: Decimal
    ) -> bool:
        """
        Vérifie si un prix est dans la fourchette (logique métier)
        """
        if prix_min is not None and prix < prix_min:
            return False
        if prix_max is not None and prix > prix_max:
            return False
        return True

    def _calculer_pertinence_et_trier(
        self, produits: List[Produit], criteres: CritereRecherche
    ) -> List[Produit]:
        """
        Calcule la pertinence et trie les résultats (logique métier)
        """
        # Tri par pertinence métier :
        # 1. Produits premium en premier si recherche par nom
        # 2. Prix croissant sinon
        if criteres.a_filtre_nom():
            return sorted(produits, key=lambda p: (not p.est_premium(), p.prix.montant))
        else:
            return sorted(produits, key=lambda p: p.prix.montant)

    def _generer_metadonnees(
        self, produits: List[Produit], criteres: CritereRecherche
    ) -> Dict[str, Any]:
        """
        Génère des métadonnées métier sur les résultats
        """
        if not produits:
            return {
                "prix_moyen": 0,
                "prix_min": 0,
                "prix_max": 0,
                "categories_trouvees": [],
                "nb_premium": 0,
            }

        prix = [p.prix.montant for p in produits]
        categories = list(set(p.categorie_id for p in produits))

        return {
            "prix_moyen": float(sum(prix) / len(prix)),
            "prix_min": float(min(prix)),
            "prix_max": float(max(prix)),
            "categories_trouvees": [str(cat) for cat in categories],
            "nb_premium": sum(1 for p in produits if p.est_premium()),
        }

    def _produit_to_dict(self, produit: Produit) -> Dict[str, Any]:
        """
        Convertit un produit en dictionnaire pour la réponse complète
        """
        return {
            "id": str(produit.id),
            "nom": produit.nom.valeur,
            "categorie_id": str(produit.categorie_id),
            "prix": float(produit.prix.montant),
            "devise": produit.prix.devise,
            "description": produit.description,
            "sku": produit.sku.code if produit.sku else None,
            "est_actif": produit.est_actif,
            "est_premium": produit.est_premium(),
            "date_creation": produit.date_creation.isoformat(),
            "date_modification": produit.date_modification.isoformat(),
        }

    def _produit_to_dict_simple(self, produit: Produit) -> Dict[str, Any]:
        """
        Convertit un produit en dictionnaire simplifié pour communication inter-services
        Enlève: sku, est_actif, est_premium, devise
        Retourne le nom de catégorie au lieu de l'UUID pour plus de lisibilité
        """
        # Récupération du nom de catégorie depuis le produit Django
        nom_categorie = self._get_nom_categorie(produit)

        return {
            "id": str(produit.id),
            "nom": produit.nom.valeur,
            "categorie": nom_categorie,  # Nom lisible au lieu d'UUID
            "prix": float(produit.prix.montant),
            "description": produit.description,
            "date_creation": produit.date_creation.isoformat(),
            "date_modification": produit.date_modification.isoformat(),
        }

    def _get_nom_categorie(self, produit: Produit) -> str:
        """
        Extrait le nom de catégorie depuis le produit Django
        Solution simple qui contourne l'incohérence UUID/string
        """
        try:
            # Récupérer directement depuis le modèle Django
            from django.apps import apps

            ProduitModel = apps.get_model("produits", "Produit")
            produit_django = ProduitModel.objects.get(id=produit.id)
            return produit_django.categorie  # Retourne "Informatique", "Boissons", etc.
        except Exception:
            return "Catégorie inconnue"

    def _criteres_to_dict(self, criteres: CritereRecherche) -> Dict[str, Any]:
        """
        Convertit les critères en dictionnaire pour la réponse
        """
        return {
            "nom": criteres.nom,
            "categorie_id": (
                str(criteres.categorie_id) if criteres.categorie_id else None
            ),
            "prix_min": float(criteres.prix_min) if criteres.prix_min else None,
            "prix_max": float(criteres.prix_max) if criteres.prix_max else None,
            "actifs_seulement": criteres.actifs_seulement,
        }
